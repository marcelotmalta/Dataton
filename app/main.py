from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import os
from pathlib import Path

app = FastAPI(title="Datathon Prediction API - Pedra Conceito")

# Definição do esquema de entrada
class StudentData(BaseModel):
    IAN: float
    IDA: float
    IEG: float
    IAA: float
    IPS: float
    IPP: float
    IPV: float
    FASE: float
    DEFA: float  # Defasagem escolar (input) para calcular Status_DEFA

# Caminho do modelo
# Ajustando para encontrar o arquivo relativo à raiz do projeto ou absoluto
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "modelo_pedra_conceito_v1.pkl"


_model = None
_imputer = None

def load_model():
    global _model, _imputer
    try:
        if MODEL_PATH.exists():
            artifact = joblib.load(MODEL_PATH)
            
            # Verificando se é um dicionário e extraindo componentes
            if isinstance(artifact, dict):
                _model = artifact.get('modelo')
                _imputer = artifact.get('imputer')
                print(f"Artefato carregado com sucesso. Chaves: {artifact.keys()}")
            else:
                _model = artifact
                _imputer = None
                print("Artefato carregado (não é dicionário).")
                
            print(f"Modelo carregado de: {MODEL_PATH}")
        else:
            print(f"Alerta: Modelo não encontrado em {MODEL_PATH}")
            _model = None
    except Exception as e:
        print(f"Erro ao carregar o modelo: {e}")
        _model = None

@app.on_event("startup")
def startup_event():
    load_model()

@app.get("/")
def health():
    return {
        "status": "ok",
        "model_loaded": _model is not None,
        "imputer_loaded": _imputer is not None,
        "model_path": str(MODEL_PATH)
    }

@app.post("/predict")
def predict(data: StudentData):
    if _model is None:
        raise HTTPException(status_code=503, detail="Modelo não disponível")
    
    # Cálculo do Status_DEFA
    if data.DEFA < 0:
        status_defa = 0
    elif data.DEFA == 0:
        status_defa = 1
    else:
        status_defa = 2
        
    features = [
        data.IAN,
        data.IDA,
        data.IEG,
        data.IAA,
        data.IPS,
        data.IPP,
        data.IPV,
        data.FASE,
        float(status_defa)
    ]
    
    try:
        input_array = np.array([features])
        
        # Aplicar imputer se disponível
        if _imputer is not None:
            # O imputer espera um array 2D com as mesmas colunas do treino
            # features = ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'FASE', 'Status_DEFA']
            input_array = _imputer.transform(input_array)
            
        prediction = _model.predict(input_array)[0]
        
        if hasattr(_model, "predict_proba"):
            probs = _model.predict_proba(input_array).tolist()[0]
            confidence = max(probs)
        else:
            probs = None
            confidence = None
            
        # Lógica de Sugestão de Ação
        sugestoes = []

        # --- REGRAS GERAIS POR CATEGORIA ---
        
        # 1. Topázio (Excelência)
        if prediction == 'Topázio':
            sugestoes.append({
                "perfil": "Topázio (Geral)",
                "acao": "Enriquecimento: Monitoria de pares, projetos de liderança e olimpíadas científicas. Monitorar equilíbrio emocional (IAA/IPS)."
            })

        # 2. Ametista (Estável)
        elif prediction == 'Ametista':
            sugestoes.append({
                "perfil": "Ametista (Geral)",
                "acao": "Manutenção: Incentivo para atingir a zona de excelência. Reforçar o engajamento em atividades extracurriculares."
            })

        # 3. Ágata (Alerta)
        elif prediction == 'Ágata':
            sugestoes.append({
                "perfil": "Ágata (Geral)",
                "acao": "Apoio Pedagógico: Reforço escolar focado em gaps de aprendizagem para evitar queda para o nível Quartzo."
            })
            
        # 4. Quartzo (Risco Crítico)
        elif prediction == 'Quartzo':
            sugestoes.append({
                "perfil": "Quartzo (Geral)",
                "acao": "Intervenção Urgente: Plano de aceleração de estudos e nivelamento. Verificação imediata de defasagem idade-fase."
            })

        # --- REGRAS ESPECÍFICAS (perfis complementares) ---
        
        # Perfil Crítico (Quartzo + Atrasado) - Reforço do alerta de defasagem
        if prediction == 'Quartzo' and status_defa == 0:
            sugestoes.append({
                "perfil": "Crítico (Defasagem)",
                "acao": "Atenção Prioritária: A defasagem idade-série agrava o risco. Priorizar nivelamento básico."
            })
            
        # Perfil Desengajado (IEG < 6.0 e IPS < 6.0)
        if data.IEG < 6.0 and data.IPS < 6.0:
            sugestoes.append({
                "perfil": "Desengajado",
                "acao": "Apoio Psicossocial: Foco em motivação e participação em atividades de voluntariado para elevar o vínculo."
            })
            
        # Risco Acadêmico (IDA < 6.0 e No Prazo)
        if data.IDA < 6.0 and status_defa == 1:
            sugestoes.append({
                "perfil": "Risco Acadêmico",
                "acao": "Reforço de Conteúdo: Tutoria acadêmica focada nas matérias de base para evitar que o aluno se atrase."
            })
            
        # Potencial Topázio (Ametista + IPV > 8.0)
        if prediction == 'Ametista' and data.IPV > 8.0:
            sugestoes.append({
                "perfil": "Potencial Topázio",
                "acao": "Mentoria de Excelência: Desafios extras e preparação para competições ou monitoria de outros alunos."
            })
        
        return {
            "pedra_conceito": prediction,
            "status_defa_calculado": status_defa,
            "confidence": confidence,
            "sugestoes_pedagogicas": sugestoes,
            "input_features": features
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na predição: {str(e)}")
