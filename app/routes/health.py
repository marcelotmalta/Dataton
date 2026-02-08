# routes/health.py
"""
Endpoints de verificação de saúde da API
"""
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health_check(request: Request):
    """
    Verifica o status da API e disponibilidade de recursos
    
    Returns:
        Status da API, modelo e dados
    """
    model_service = request.app.state.model_service
    
    return {
        "status": "ok",
        "model_loaded": model_service.model_pipeline is not None,
        "data_loaded": model_service.df_base is not None,
        "model_version": model_service.model_version
    }
