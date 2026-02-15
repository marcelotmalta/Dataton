# services/prediction_service.py
"""
Serviço para predições e geração de recomendações
"""
import unicodedata
from typing import Any, Dict

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.config import DEFA_LARGE_THRESHOLD, logger
from app.models import StudentMetrics
from app.utils.helpers import estimate_top_drivers, risk_tier_from_score, sanitize_for_json


class PredictionService:
    """Gerencia predições e geração de ações sugeridas"""

    DEFAULT_FEATURES = [
        "IAN",
        "IDA",
        "IEG",
        "IAA",
        "IPS",
        "IPP",
        "IPV",
        "FASE",
        "consistencia_acad",
    ]

    def __init__(self, model_service):
        self.model_service = model_service

    @staticmethod
    def _normalize_label(text: Any) -> str:
        """Normaliza labels para comparação robusta (remove acentos)."""
        if not isinstance(text, str):
            return ""
        normalized = unicodedata.normalize("NFKD", text)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return normalized.strip().lower()

    def _class_index_by_label(self, mapa_classes_inv, candidate_labels):
        """Retorna índice da classe cujo nome coincide com algum candidato."""
        if not mapa_classes_inv:
            return None

        normalized_candidates = {self._normalize_label(lbl) for lbl in candidate_labels}
        for idx, class_name in mapa_classes_inv.items():
            if self._normalize_label(class_name) in normalized_candidates:
                try:
                    return int(idx)
                except Exception:
                    continue
        return None

    def prepare_features(self, input_data: Dict[str, Any], features=None) -> pd.DataFrame:
        """
        Prepara features derivadas e constrói DataFrame para predição

        Args:
            input_data: Dicionário com métricas do estudante
            features: Lista de features desejadas

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

        feature_list = features or self.model_service.features_list or self.DEFAULT_FEATURES
        return pd.DataFrame([{k: input_data.get(k, np.nan) for k in feature_list}])

    def make_prediction(
        self,
        df_pred: pd.DataFrame,
        model,
        imputer=None,
        scaler=None,
        model_name: str = "model",
    ):
        """
        Executa predição usando modelo + artefatos de transformação.

        Args:
            df_pred: DataFrame com features preparadas
            model: Estimador com predict/predict_proba
            imputer: Imputer opcional
            scaler: Scaler opcional

        Returns:
            Tupla (probabilidades, índice_predito)
        """
        if model is None:
            return None, None

        # Tentar predição direta com DataFrame (modelo já preparado para isso)
        try:
            # Alguns estimadores (ex.: LogisticRegression treinado com ndarray) não
            # possuem feature_names_in_ e emitem warning ao receber DataFrame.
            # Nesses casos, seguimos direto para o caminho com transformação em array.
            if not hasattr(model, "feature_names_in_"):
                raise ValueError("Model fitted without feature names")

            probs = model.predict_proba(df_pred)[0]
            pred_idx = int(model.predict(df_pred)[0])
            return probs, pred_idx
        except Exception:
            # Fallback para imputer/scaler se disponível
            try:
                if imputer is not None:
                    try:
                        if hasattr(imputer, "feature_names_in_"):
                            cols = list(imputer.feature_names_in_)
                            X_input = df_pred.reindex(columns=cols)
                            X_for_pred = imputer.transform(X_input)
                        else:
                            X_for_pred = imputer.transform(df_pred.values)
                    except Exception as imputer_error:
                        logger.warning(
                            "Imputer transform failed for %s (%s). Using manual fallback.",
                            model_name,
                            imputer_error,
                        )
                        X_for_pred = self._manual_imputation_fallback(
                            df_pred=df_pred,
                            imputer=imputer,
                        )
                else:
                    X_for_pred = self._manual_imputation_fallback(df_pred=df_pred)

                if scaler is not None:
                    X_for_pred = scaler.transform(X_for_pred)

                probs = model.predict_proba(X_for_pred)[0]
                pred_idx = int(model.predict(X_for_pred)[0])
                return probs, pred_idx
            except Exception as e:
                logger.exception("Prediction failed for %s: %s", model_name, e)
                raise HTTPException(
                    status_code=500,
                    detail="Prediction failed on server",
                )

    def _manual_imputation_fallback(self, df_pred: pd.DataFrame, imputer=None):
        """
        Fallback de imputação sem depender de atributos internos do scikit-learn
        (útil quando há incompatibilidade de versão no artefato serializado).
        """
        if imputer is not None and hasattr(imputer, "feature_names_in_"):
            cols = list(imputer.feature_names_in_)
            X_input = df_pred.reindex(columns=cols)
        else:
            X_input = df_pred.copy()

        fill_map = {}
        if imputer is not None and hasattr(imputer, "statistics_"):
            stats = list(imputer.statistics_)
            for idx, col in enumerate(X_input.columns):
                if idx >= len(stats):
                    break
                try:
                    value = float(stats[idx])
                    if np.isfinite(value):
                        fill_map[col] = value
                except Exception:
                    continue

        if fill_map:
            X_input = X_input.fillna(fill_map)

        if self.model_service.feature_medians is not None:
            try:
                medians = {
                    c: float(v)
                    for c, v in self.model_service.feature_medians.to_dict().items()
                    if c in X_input.columns
                }
                if medians:
                    X_input = X_input.fillna(medians)
            except Exception:
                pass

        return X_input.fillna(0.0).values

    def calculate_risk_score(
        self,
        risk_probs=None,
        risk_map_inv=None,
        fallback_probs=None,
        fallback_map_inv=None,
    ):
        """
        Calcula score de risco priorizando o modelo binário (classe Critico).

        Args:
            risk_probs: Probabilidades do modelo binário
            risk_map_inv: Mapa invertido do modelo binário
            fallback_probs: Probabilidades de fallback (multiclasse)
            fallback_map_inv: Mapa invertido do fallback

        Returns:
            Score de risco (float) ou None
        """
        # Preferência 1: classe positiva do binário (Critico)
        if risk_probs is not None:
            critico_idx = self._class_index_by_label(
                risk_map_inv,
                {"Critico", "Crítico"},
            )
            if critico_idx is not None and critico_idx < len(risk_probs):
                return float(risk_probs[critico_idx])

            # Fallback conservador para binário sem mapa: classe índice 1
            if len(risk_probs) == 2:
                return float(risk_probs[1])
            if len(risk_probs) == 1:
                return float(risk_probs[0])

        # Preferência 2: heurística antiga em cima de multiclasse (Quartzo)
        if fallback_probs is None:
            return None

        quartzo_idx = self._class_index_by_label(
            fallback_map_inv,
            {"Quartzo"},
        )
        if quartzo_idx is not None and quartzo_idx < len(fallback_probs):
            return float(fallback_probs[quartzo_idx])

        # Fallback final: média ponderada (índices iniciais = maior risco)
        n = len(fallback_probs)
        if n > 1:
            weights = np.array([1.0 - (i / float(n - 1)) for i in range(n)])
            weights = weights / weights.sum()
            return float(np.dot(fallback_probs, weights))
        if n == 1:
            return float(fallback_probs[0])
        return None

    @staticmethod
    def _map_prediction_label(pred_idx, class_map_inv) -> str:
        """Mapeia índice predito para label textual."""
        if pred_idx is None:
            return "unknown"
        if class_map_inv:
            try:
                return class_map_inv.get(int(pred_idx), str(pred_idx))
            except Exception:
                return str(pred_idx)
        return str(pred_idx)

    @staticmethod
    def _build_probabilities_map(probs, class_map_inv) -> Dict[str, float]:
        """Constrói dicionário de probabilidades por classe."""
        probs_map = {}
        if probs is None:
            return probs_map

        if class_map_inv:
            for i, p in enumerate(probs):
                probs_map[class_map_inv.get(int(i), f"Class_{i}")] = float(p)
        else:
            for i, p in enumerate(probs):
                probs_map[f"Class_{i}"] = float(p)

        return probs_map

    def generate_suggestions(
        self,
        defa_int: int,
        risk_score: float,
        pred_label: str,
        student_name: str = None,
    ) -> Dict[str, Any]:
        """
        Gera ações sugeridas e mensagens baseadas em DEFA e risco

        Args:
            defa_int: Valor inteiro de DEFA
            risk_score: Score de risco calculado
            pred_label: Label da predição
            student_name: Nome do estudante (opcional)

        Returns:
            Dicionário com ação sugerida e mensagens
        """
        suggested_action = "Manutenção do Desempenho"
        suggested_messages = {"family": "", "professor": ""}

        nome = student_name or "O aluno"

        # DEFA negativo = problema (defasagem)
        if defa_int < 0:
            if defa_int <= -DEFA_LARGE_THRESHOLD:
                suggested_action = "Recuperação Intensiva (grave)"
                suggested_messages["family"] = (
                    f"Detectamos defasagem grave (DEFA={defa_int}). "
                    "Requer reunião imediata com coordenação."
                )
                suggested_messages["professor"] = (
                    "Acionar plano de intervenção intensiva, "
                    "tutorias diárias, contato família."
                )
            else:
                suggested_action = "Recuperação de Aprendizagem"
                suggested_messages["family"] = (
                    f"Detectamos defasagem (DEFA={defa_int}). "
                    "Recomendamos plano de recuperação de curto prazo."
                )
                suggested_messages["professor"] = (
                    "Atividades focalizadas e monitoramento."
                )

        # DEFA positivo = aluno adiantado
        elif defa_int > 0:
            if defa_int >= DEFA_LARGE_THRESHOLD:
                suggested_action = "Aprofundamento / Enriquecimento (alto)"
                suggested_messages["family"] = (
                    f"{nome} está adiantado (DEFA={defa_int}). "
                    "Sugerimos aprofundamento/possível aceleração."
                )
                suggested_messages["professor"] = (
                    "Projetos de aprofundamento, mentorias, avaliar aceleração."
                )
            else:
                suggested_action = "Enriquecimento Curricular (moderado)"
                suggested_messages["family"] = (
                    f"{nome} está ligeiramente adiantado (DEFA={defa_int}). "
                    "Sugerimos atividades de extensão."
                )
                suggested_messages["professor"] = (
                    "Desafios adicionais e monitorar engajamento."
                )

            # Se modelo indica alto risco apesar de estar adiantado, flag review
            if risk_score is not None and risk_score >= 0.75:
                suggested_action += " + Revisão"
                suggested_messages["family"] += (
                    " (Nota: modelo indica risco; revisar caso.)"
                )
                suggested_messages["professor"] += " (Rever indicador de risco.)"

        # DEFA = 0: seguir risk_score ou monitoramento padrão
        else:
            if risk_score is not None:
                tier = risk_tier_from_score(risk_score)

                if tier == "Crítico":
                    suggested_action = "Intervenção Psicopedagógica"
                    suggested_messages["family"] = (
                        "Detectamos risco crítico. "
                        "Agendar apoio psicopedagógico urgente."
                    )
                    suggested_messages["professor"] = (
                        "Priorizar acompanhamento intensivo e "
                        "comunicação com a família."
                    )
                elif tier == "Alto":
                    suggested_action = "Acompanhamento Intensivo"
                    suggested_messages["family"] = (
                        "Sinais de risco. Recomendamos tutoria "
                        "1-2x/semana por 4 semanas."
                    )
                    suggested_messages["professor"] = (
                        "Planejar recuperação focalizada e monitorar semanalmente."
                    )
                elif isinstance(pred_label, str) and self._normalize_label(pred_label) in (
                    "topazio",
                ):
                    suggested_action = "Enriquecimento Curricular"
                    suggested_messages["family"] = (
                        "Bom desempenho - sugerimos atividades de aprofundamento."
                    )
                    suggested_messages["professor"] = "Oferecer desafios e extensão."
                else:
                    suggested_action = "Monitoramento e Micro-intervenção"
                    suggested_messages["family"] = (
                        "Acompanhamento de rotina; entraremos em contato "
                        "se houver piora."
                    )
                    suggested_messages["professor"] = (
                        "Monitorar evolução e aplicar micro-intervenção se necessário."
                    )
            else:
                # Sem modelo disponível
                suggested_action = "Monitoramento"
                suggested_messages["family"] = (
                    "Sem modelo disponível: faremos revisão por DEFA e "
                    "acompanhamento de rotina."
                )
                suggested_messages["professor"] = (
                    "Monitorar presença e desempenho; reportar casos de atenção."
                )

        return {
            "suggested_action": suggested_action,
            "suggested_messages": suggested_messages,
        }

    def predict_score(self, metrics: StudentMetrics) -> Dict[str, Any]:
        """
        Executa predição completa e gera resposta

        Args:
            metrics: Métricas do estudante

        Returns:
            Dicionário com predição, probabilidades, risco e recomendações
        """
        input_data = metrics.model_dump()

        try:
            defa_int = int(round(float(input_data.get("DEFA", 0))))
        except Exception:
            defa_int = 0

        multi_features = self.model_service.features_list or self.DEFAULT_FEATURES
        risk_features = self.model_service.features_list_risk or multi_features

        df_pred_multi = self.prepare_features(input_data, features=multi_features)
        if list(risk_features) == list(multi_features):
            df_pred_risk = df_pred_multi
        else:
            df_pred_risk = self.prepare_features(input_data, features=risk_features)

        # Predição principal (Pedra Conceito)
        probs_multi, pred_idx_multi = None, None
        multi_error = None
        if self.model_service.model_pipeline is not None:
            try:
                probs_multi, pred_idx_multi = self.make_prediction(
                    df_pred_multi,
                    model=self.model_service.model_pipeline,
                    imputer=self.model_service.imputer,
                    scaler=self.model_service.scaler,
                    model_name="multiclass",
                )
            except HTTPException as exc:
                multi_error = exc
                logger.exception(
                    "Multiclass prediction failed; proceeding with risk model fallback if possible."
                )

        # Predição binária (Risco Crítico)
        probs_risk, pred_idx_risk = None, None
        risk_error = None
        if self.model_service.model_pipeline_risk is not None:
            try:
                probs_risk, pred_idx_risk = self.make_prediction(
                    df_pred_risk,
                    model=self.model_service.model_pipeline_risk,
                    imputer=self.model_service.imputer_risk,
                    scaler=self.model_service.scaler_risk,
                    model_name="risk",
                )
            except HTTPException as exc:
                risk_error = exc
                logger.exception(
                    "Risk prediction failed; proceeding with available multiclass output."
                )

        if (
            pred_idx_multi is None
            and pred_idx_risk is None
            and (multi_error is not None or risk_error is not None)
        ):
            raise HTTPException(status_code=500, detail="Prediction failed on server")

        # Label exibida: preferir multiclasse
        if pred_idx_multi is not None:
            pred_idx = pred_idx_multi
            pred_label = self._map_prediction_label(
                pred_idx_multi,
                self.model_service.mapa_classes_inv,
            )
        else:
            pred_idx = pred_idx_risk
            pred_label = self._map_prediction_label(
                pred_idx_risk,
                self.model_service.mapa_classes_inv_risk,
            )

        # Score de risco: preferir modelo binário
        risk_score = self.calculate_risk_score(
            risk_probs=probs_risk,
            risk_map_inv=self.model_service.mapa_classes_inv_risk,
            fallback_probs=probs_multi,
            fallback_map_inv=self.model_service.mapa_classes_inv,
        )

        # Sugestões
        suggestions = self.generate_suggestions(
            defa_int,
            risk_score,
            pred_label,
            input_data.get("NOME"),
        )

        # Drivers (heurística baseada no modelo principal)
        try:
            drivers = estimate_top_drivers(
                df_pred_multi.iloc[0].to_dict(),
                list(multi_features),
                self.model_service,
            )
        except Exception:
            drivers = []

        probs_main = probs_multi if probs_multi is not None else probs_risk
        map_main = (
            self.model_service.mapa_classes_inv
            if probs_multi is not None
            else self.model_service.mapa_classes_inv_risk
        )

        response = {
            "prediction": pred_label,
            "prediction_index": int(pred_idx) if pred_idx is not None else None,
            "probabilities": self._build_probabilities_map(probs_main, map_main),
            "risk_score": None if risk_score is None else round(float(risk_score), 4),
            "risk_tier": None if risk_score is None else risk_tier_from_score(risk_score),
            "acao_sugerida": suggestions["suggested_action"],
            "suggested_messages": suggestions["suggested_messages"],
            "top_drivers": drivers,
            "input_features": df_pred_multi.to_dict(orient="records")[0],
            "defa_int": int(defa_int),
            "model_version": self.model_service.model_version,
            "risk_model_version": self.model_service.model_version_risk,
        }

        return sanitize_for_json(response)
