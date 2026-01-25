from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI(title="Datathon Prediction API")

# Exemplo de schema de entrada
class PredictIn(BaseModel):
    # adaptar para as features reais do dataset
    nota_port: float
    nota_mat: float
    ips: float

# Carregamento do modelo (exemplo: se existir ./models/model.joblib)
MODEL_PATH = "models/model.joblib"
_model = None

def load_model():
    global _model
    try:
        _model = joblib.load(MODEL_PATH)
    except Exception:
        _model = None

@app.on_event("startup")
def startup_event():
    load_model()

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict(payload: PredictIn):
    if _model is None:
        return {"error": "Modelo não encontrado. Faça o upload em models/model.joblib"}
    x = np.array([[payload.nota_port, payload.nota_mat, payload.ips]])
    prob = _model.predict_proba(x)[:,1].tolist()
    pred = _model.predict(x).tolist()
    return {"prediction": pred[0], "probability": prob[0]}
