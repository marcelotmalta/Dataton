# routes/predictions.py
"""
Endpoints de predição de desempenho
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.models import StudentMetrics

router = APIRouter()


@router.post("/predict")
def predict_score(metrics: StudentMetrics, request: Request):
    """
    Prediz desempenho do estudante e gera recomendações
    
    Args:
        metrics: Métricas do estudante
        request: Request object do FastAPI
        
    Returns:
        Predição, probabilidades, risco, ações sugeridas e histórico
    """
    prediction_service = request.app.state.prediction_service
    student_service = request.app.state.student_service
    response = prediction_service.predict_score(metrics, student_service=student_service)
    return JSONResponse(content=response)
