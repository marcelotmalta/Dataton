# services/prediction_service.py
"""
Serviço para predições de desempenho de estudantes.
Responsável apenas pelo core de ML: preparação de features,
execução de predição e cálculo de risco.
"""
import numpy as np
import pandas as pd
from fastapi import HTTPException
from typing import Dict, Any

from app.config import logger
from app.models import StudentMetrics
from app.utils.helpers import risk_tier_from_score, estimate_top_drivers, sanitize_for_json


class PredictionService:
    """Core de Machine Learning: features, predição e risco"""

    def __init__(self, model_service, suggestion_service=None):
        self.model_service = model_service
        self.suggestion_service = suggestion_service

    def prepare_features(self, input_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Prepara features derivadas e constrói DataFrame para predição.

        Args:
            input_data: Dicionário com métricas do estudante

        Returns:
            DataFrame com features preparadas
        """
        # Feature derivada: consistência acadêmica
        try:
            ida = float(input_data.get("IDA") or 0.0)
            ieg = float(input_data.get("IEG") or 0.0)
            input_data["consistencia_acad"] = ida / (ieg + 0.1)
        except Exception:
            input_data["consistencia_acad"] = 0.0

        # Construir vetor de features
        features = self.model_service.features_list or [
            "IAN", "IDA", "IEG", "IAA", "IPS", "IPP", "IPV",
            "FASE", "Status_DEFA", "consistencia_acad"
        ]

        df_pred = pd.DataFrame([{
            k: input_data.get(k, np.nan) for k in features
        }])

        return df_pred

    def make_prediction(self, df_pred: pd.DataFrame):
        """
        Executa predição usando o modelo.

        Args:
            df_pred: DataFrame com features preparadas

        Returns:
            Tupla (probabilidades, índice_predito)
        """
        model = self.model_service.model_pipeline

        if model is None:
            return None, None

        # Tentar predição direta com pipeline
        try:
            probs = model.predict_proba(df_pred)[0]
            pred_idx = int(model.predict(df_pred)[0])
            return probs, pred_idx
        except Exception:
            return self._prediction_fallback(model, df_pred)

    def _prediction_fallback(self, model, df_pred: pd.DataFrame):
        """Fallback para imputer/scaler se predição direta falhar."""
        try:
            X = df_pred.copy()

            if self.model_service.imputer is not None:
                imp = self.model_service.imputer
                try:
                    if hasattr(imp, "feature_names_in_"):
                        X_imp = imp.transform(df_pred[imp.feature_names_in_])
                    else:
                        X_imp = imp.transform(df_pred.values)
                except Exception:
                    X_imp = imp.transform(df_pred.values)
                X_for_pred = X_imp
            else:
                if self.model_service.feature_medians is not None:
                    X_for_pred = df_pred.fillna(
                        self.model_service.feature_medians.to_dict()
                    ).values
                else:
                    X_for_pred = df_pred.fillna(0.0).values

            if self.model_service.scaler is not None:
                X_for_pred = self.model_service.scaler.transform(X_for_pred)

            probs = model.predict_proba(X_for_pred)[0]
            pred_idx = int(model.predict(X_for_pred)[0])
            return probs, pred_idx
        except Exception as e:
            logger.exception("Prediction failed: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Prediction failed on server"
            )

    def calculate_risk_score(self, probs):
        """
        Calcula score de risco a partir das probabilidades.

        Args:
            probs: Array de probabilidades por classe

        Returns:
            Score de risco (float) ou None se não houver probabilidades
        """
        if probs is None:
            return None

        # Preferir probabilidade da classe 'quartzo' se mapeada
        quartzo_idx = self._find_quartzo_index()

        if quartzo_idx is not None and quartzo_idx < len(probs):
            return float(probs[quartzo_idx])
        else:
            return self._weighted_risk_fallback(probs)

    def _find_quartzo_index(self):
        """Localiza o índice da classe Quartzo no mapa de classes."""
        if not self.model_service.mapa_classes_inv:
            return None

        for idx, name in self.model_service.mapa_classes_inv.items():
            try:
                if isinstance(name, str) and name.strip().lower() == "quartzo":
                    return int(idx)
            except Exception:
                continue
        return None

    def _weighted_risk_fallback(self, probs) -> float:
        """Fallback: média ponderada quando classe Quartzo não está mapeada."""
        n = len(probs)
        if n > 1:
            weights = np.array([1.0 - (i / float(n - 1)) for i in range(n)])
            weights = weights / weights.sum()
            return float(np.dot(probs, weights))
        return float(probs[0])

    def _resolve_label(self, pred_idx) -> str:
        """Resolve o índice de predição para o label textual."""
        if pred_idx is None:
            return "unknown"

        pred_label = str(pred_idx)
        if self.model_service.mapa_classes_inv:
            try:
                pred_label = self.model_service.mapa_classes_inv.get(
                    int(pred_idx), str(pred_idx)
                )
            except Exception:
                pass
        return pred_label

    def predict_score(self, metrics: StudentMetrics) -> Dict[str, Any]:
        """
        Executa predição completa e gera resposta.

        Args:
            metrics: Métricas do estudante

        Returns:
            Dicionário com predição, probabilidades, risco e recomendações
        """
        input_data = metrics.model_dump()

        # DEFA integer semantics
        try:
            defa_int = int(round(float(input_data.get("DEFA", 0))))
        except Exception:
            defa_int = 0

        # Preparar features e fazer predição
        df_pred = self.prepare_features(input_data)
        probs, pred_idx = self.make_prediction(df_pred)
        pred_label = self._resolve_label(pred_idx)
        risk_score = self.calculate_risk_score(probs)

        # Gerar sugestões via SuggestionService
        suggestions = self.suggestion_service.generate_suggestions(
            defa_int, risk_score, pred_label, input_data.get('NOME')
        )

        # Estimar drivers
        drivers = self._estimate_drivers(df_pred)

        # Construir mapa de probabilidades
        probs_map = self._build_probs_map(probs)

        return sanitize_for_json({
            "prediction": pred_label,
            "prediction_index": int(pred_idx) if pred_idx is not None else None,
            "probabilities": probs_map,
            "risk_score": None if risk_score is None else round(float(risk_score), 4),
            "risk_tier": None if risk_score is None else risk_tier_from_score(risk_score),
            "acao_sugerida": suggestions["suggested_action"],
            "suggested_messages": suggestions["suggested_messages"],
            "top_drivers": drivers,
            "input_features": df_pred.to_dict(orient="records")[0],
            "defa_int": int(defa_int),
            "model_version": self.model_service.model_version
        })

    def _estimate_drivers(self, df_pred: pd.DataFrame) -> list:
        """Estima os principais drivers da predição."""
        try:
            features = self.model_service.features_list or [
                "IAN", "IDA", "IEG", "IAA", "IPS", "IPP", "IPV",
                "FASE", "Status_DEFA", "consistencia_acad"
            ]
            return estimate_top_drivers(
                df_pred.iloc[0].to_dict(),
                features,
                self.model_service
            )
        except Exception:
            return []

    def _build_probs_map(self, probs) -> dict:
        """Constrói mapa de probabilidades por classe."""
        probs_map = {}
        if probs is None:
            return probs_map

        if self.model_service.mapa_classes_inv:
            for i, p in enumerate(probs):
                label = self.model_service.mapa_classes_inv.get(int(i), f"Class_{i}")
                probs_map[label] = float(p)
        else:
            for i, p in enumerate(probs):
                probs_map[f"Class_{i}"] = float(p)

        return probs_map
