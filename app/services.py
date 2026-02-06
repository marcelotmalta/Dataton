import joblib
import numpy as np
import os
from pathlib import Path
from .schemas import StudentData, PredictionResponse, PedagogicalSuggestion

class ModelService:
    def __init__(self):
        self._model = None
        self._imputer = None
        self.model_path = Path(__file__).resolve().parent.parent / "models" / "modelo_pedra_conceito_v1.pkl"
        self.load_model()

    def load_model(self):
        try:
            if self.model_path.exists():
                artifact = joblib.load(self.model_path)
                
                if isinstance(artifact, dict):
                    self._model = artifact.get('modelo')
                    self._imputer = artifact.get('imputer')
                    print(f"Artefato carregado com sucesso. Chaves: {artifact.keys()}")
                else:
                    self._model = artifact
                    self._imputer = None
                    print("Artefato carregado (não é dicionário).")
                    
                print(f"Modelo carregado de: {self.model_path}")
            else:
                print(f"Alerta: Modelo não encontrado em {self.model_path}")
                self._model = None
        except Exception as e:
            print(f"Erro ao carregar o modelo: {e}")
            self._model = None

    def get_status(self):
        return {
            "model_loaded": self._model is not None,
            "imputer_loaded": self._imputer is not None,
            "model_path": str(self.model_path)
        }

    def predict(self, data: StudentData) -> PredictionResponse:
        if self._model is None:
            raise Exception("Modelo não disponível")

        # Cálculo do Status_DEFA
        if data.DEFA < 0:
            status_defa = 0
        elif data.DEFA == 0:
            status_defa = 1
        else:
            status_defa = 2
            
        features = [
            data.IAN, data.IDA, data.IEG, data.IAA, 
            data.IPS, data.IPP, data.IPV, data.FASE, 
            float(status_defa)
        ]
        
        input_array = np.array([features])
        
        # Aplicar imputer se disponível
        if self._imputer is not None:
            try:
                # O imputer foi treinado com nomes de features no pandas, 
                # mas transform com array numpy gera aviso. É seguro ignorar neste contexto
                # ou poderíamos recriar um DataFrame. Vamos manter numpy por performance.
                input_array = self._imputer.transform(input_array)
            except Exception as e:
                # Fallback se der erro crítico
                print(f"Erro no imputer: {e}")

        prediction = self._model.predict(input_array)[0]
        
        confidence = None
        if hasattr(self._model, "predict_proba"):
            probs = self._model.predict_proba(input_array).tolist()[0]
            confidence = max(probs)
            
        sugestoes = self._gerar_sugestoes(prediction, status_defa, data)
            
        return PredictionResponse(
            pedra_conceito=prediction,
            status_defa_calculado=status_defa,
            confidence=confidence,
            sugestoes_pedagogicas=sugestoes,
            input_features=features
        )

    def _gerar_sugestoes(self, prediction: str, status_defa: int, data: StudentData) -> list:
        sugestoes = []

        # --- REGRAS GERAIS POR CATEGORIA ---
        if prediction == 'Topázio':
            sugestoes.append(PedagogicalSuggestion(
                perfil="Topázio (Geral)",
                acao="Enriquecimento: Monitoria de pares, projetos de liderança e olimpíadas científicas. Monitorar equilíbrio emocional (IAA/IPS)."
            ))
        elif prediction == 'Ametista':
            sugestoes.append(PedagogicalSuggestion(
                perfil="Ametista (Geral)",
                acao="Manutenção: Incentivo para atingir a zona de excelência. Reforçar o engajamento em atividades extracurriculares."
            ))
        elif prediction == 'Ágata':
            sugestoes.append(PedagogicalSuggestion(
                perfil="Ágata (Geral)",
                acao="Apoio Pedagógico: Reforço escolar focado em gaps de aprendizagem para evitar queda para o nível Quartzo."
            ))
        elif prediction == 'Quartzo':
            sugestoes.append(PedagogicalSuggestion(
                perfil="Quartzo (Geral)",
                acao="Intervenção Urgente: Plano de aceleração de estudos e nivelamento. Verificação imediata de defasagem idade-fase."
            ))

        # --- REGRAS ESPECÍFICAS ---
        
        # Perfil Crítico (Quartzo + Atrasado)
        if prediction == 'Quartzo' and status_defa == 0:
            sugestoes.append(PedagogicalSuggestion(
                perfil="Crítico (Defasagem)",
                acao="Atenção Prioritária: A defasagem idade-série agrava o risco. Priorizar nivelamento básico."
            ))
            
        # Perfil Desengajado
        if data.IEG < 6.0 and data.IPS < 6.0:
            sugestoes.append(PedagogicalSuggestion(
                perfil="Desengajado",
                acao="Apoio Psicossocial: Foco em motivação e participação em atividades de voluntariado para elevar o vínculo."
            ))
            
        # Risco Acadêmico
        if data.IDA < 6.0 and status_defa == 1:
            sugestoes.append(PedagogicalSuggestion(
                perfil="Risco Acadêmico",
                acao="Reforço de Conteúdo: Tutoria acadêmica focada nas matérias de base para evitar que o aluno se atrase."
            ))
            
        # Potencial Topázio
        if prediction == 'Ametista' and data.IPV > 8.0:
            sugestoes.append(PedagogicalSuggestion(
                perfil="Potencial Topázio",
                acao="Mentoria de Excelência: Desafios extras e preparação para competições ou monitoria de outros alunos."
            ))
            
        # Topázio (Ações de Manutenção e Excelência) - mantendo as específicas solicitadas anteriormente
        if prediction == 'Topázio':
            if data.IAA is not None or data.IPS is not None: # Verifica só se tem dados, na verdade já adicionamos o geral,
                                                            # mas vamos manter as específicas se for o desejo de granularidade.
                                                            # O usuário pediu: "Inclua essas sugestões para o Topázio"
                                                            # Se quisermos evitar duplicação com o Geral, podemos filtrar,
                                                            # mas vou adicionar todas para garantir.
                sugestoes.append(PedagogicalSuggestion(perfil="Topázio (Acadêmica)", acao="Projetos de extensão e monitoria de pares."))
                sugestoes.append(PedagogicalSuggestion(perfil="Topázio (Psicopedagógica)", acao="Preparação para liderança e competições externas."))
                sugestoes.append(PedagogicalSuggestion(perfil="Topázio (Psicossocial)", acao="Acompanhamento para prevenção de burnout escolar."))

        return sugestoes

# Singleton
model_service = ModelService()
