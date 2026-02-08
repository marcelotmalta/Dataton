# routes/students.py
"""
Endpoints relacionados a estudantes
"""
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/students/{name}")
def search_student(name: str, request: Request):
    """
    Busca estudante por nome e retorna histórico
    
    Args:
        name: Nome do estudante (busca exata ou parcial)
        request: Request object do FastAPI
        
    Returns:
        Dados do estudante e histórico
    """
    student_service = request.app.state.student_service
    return student_service.search_student_by_name(name)
