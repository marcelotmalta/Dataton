# services/prediction_service.py
"""
Serviço para predições e geração de recomendações
"""
import numpy as np
import pandas as pd
from fastapi import HTTPException
from typing import Dict, Any

from app.config import logger, DEFA_LARGE_THRESHOLD
from app.models import StudentMetrics
from app.utils.helpers import risk_tier_from_score, estimate_top_drivers, sanitize_for_json


class PredictionService:
    """Gerencia predições e geração de ações sugeridas"""
    
    def __init__(self, model_service):
        self.model_service = model_service
    
    def prepare_features(self, input_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Prepara features derivadas e constrói DataFrame para predição
        
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
        Executa predição usando o modelo
        
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
            # Fallback para imputer/scaler se disponível
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
        Calcula score de risco a partir das probabilidades
        
        Args:
            probs: Array de probabilidades por classe
            
        Returns:
            Score de risco (float) ou None se não houver probabilidades
        """
        if probs is None:
            return None
        
        # Preferir probabilidade da classe 'quartzo' se mapeada
        quartzo_idx = None
        if self.model_service.mapa_classes_inv:
            for idx, name in self.model_service.mapa_classes_inv.items():
                try:
                    if isinstance(name, str) and name.strip().lower() == "quartzo":
                        quartzo_idx = int(idx)
                        break
                except Exception:
                    continue
        
        if quartzo_idx is not None and quartzo_idx < len(probs):
            return float(probs[quartzo_idx])
        else:
            # Fallback: média ponderada
            n = len(probs)
            if n > 1:
                weights = np.array([1.0 - (i / float(n - 1)) for i in range(n)])
                weights = weights / weights.sum()
                return float(np.dot(probs, weights))
            else:
                return float(probs[0])
    
    def generate_suggestions(
        self, 
        defa_int: int, 
        risk_score: float, 
        pred_label: str,
        student_name: str = None
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
                elif isinstance(pred_label, str) and pred_label.strip().lower() in ("topázio", "topazio"):
                    suggested_action = "Enriquecimento Curricular"
                    suggested_messages["family"] = (
                        "Bom desempenho — sugerimos atividades de aprofundamento."
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
            "suggested_messages": suggested_messages
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
        
        # DEFA integer semantics
        try:
            defa_int = int(round(float(input_data.get("DEFA", 0))))
        except Exception:
            defa_int = 0
        
        # Preparar features
        df_pred = self.prepare_features(input_data)
        
        # Fazer predição
        probs, pred_idx = self.make_prediction(df_pred)
        
        # Mapear label
        pred_label = str(pred_idx) if pred_idx is not None else "unknown"
        if self.model_service.mapa_classes_inv and pred_idx is not None:
            try:
                pred_label = self.model_service.mapa_classes_inv.get(
                    int(pred_idx), 
                    str(pred_idx)
                )
            except Exception:
                pred_label = str(pred_idx)
        
        # Calcular risk score
        risk_score = self.calculate_risk_score(probs)
        
        # Gerar sugestões
        suggestions = self.generate_suggestions(
            defa_int, 
            risk_score, 
            pred_label,
            input_data.get('NOME')
        )
        
        # Estimar drivers
        try:
            features = self.model_service.features_list or [
                "IAN", "IDA", "IEG", "IAA", "IPS", "IPP", "IPV",
                "FASE", "Status_DEFA", "consistencia_acad"
            ]
            drivers = estimate_top_drivers(
                df_pred.iloc[0].to_dict(), 
                features,
                self.model_service
            )
        except Exception:
            drivers = []
        
        # Construir mapa de probabilidades
        probs_map = {}
        if probs is not None:
            if self.model_service.mapa_classes_inv:
                for i, p in enumerate(probs):
                    probs_map[
                        self.model_service.mapa_classes_inv.get(int(i), f"Class_{i}")
                    ] = float(p)
            else:
                for i, p in enumerate(probs):
                    probs_map[f"Class_{i}"] = float(p)
        
        response = {
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
        }
        
        return sanitize_for_json(response)
