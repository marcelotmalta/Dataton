from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import StudentData, PredictionResponse
from .services import model_service

app = FastAPI(title="Datathon Prediction API - Pedra Conceito")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # O serviço já carrega no init, mas podemos forçar reload se quiser
    pass

@app.get("/")
def health():
    status = model_service.get_status()
    return {"status": "ok", **status}

@app.post("/predict", response_model=PredictionResponse)
def predict(data: StudentData):
    try:
        return model_service.predict(data)
    except Exception as e:
        status_code = 503 if "Modelo não disponível" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))
