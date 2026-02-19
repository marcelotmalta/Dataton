# routes/analysis.py
"""
Endpoints de análise profunda e simulação contrafactual.
Implementa suporte à decisão pedagógica.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.models import SimulationRequest

router = APIRouter()


@router.get("/students/{name}/analysis")
def deep_analysis(name: str, request: Request):
    """
    Análise profunda de um estudante com trajetória histórica,
    cruzamento IPV×IDA e diagnósticos automatizados.

    Args:
        name: Nome do estudante (busca exata ou parcial)
        request: Request object do FastAPI

    Returns:
        Análise completa: histórico, trajetória, diagnósticos e resumo
    """
    diagnostic_service = request.app.state.diagnostic_service
    return JSONResponse(content=diagnostic_service.diagnose_student(name))


@router.get("/students/{name}/trajectory")
def student_trajectory(name: str, request: Request):
    """
    Retorna a trajetória interanual do INDE de um estudante.

    Args:
        name: Nome do estudante
        request: Request object do FastAPI

    Returns:
        Trajetória com tendência, inclinação e indicadores por ano
    """
    history_service = request.app.state.history_service
    return JSONResponse(content=history_service.get_student_trajectory(name))


@router.get("/students/{name}/ipv-ida")
def ipv_ida_crossover(name: str, request: Request):
    """
    Retorna o cruzamento IPV × IDA histórico de um estudante.

    Args:
        name: Nome do estudante
        request: Request object do FastAPI

    Returns:
        Análise de tipo de queda (técnica, maturidade, combinada)
    """
    history_service = request.app.state.history_service
    return JSONResponse(content=history_service.cross_ipv_ida(name))


@router.post("/simulate")
def simulate_scenario(sim_request: SimulationRequest, request: Request):
    """
    Simulação contrafactual: testa cenários "e se?" para um aluno.

    Exemplo: "Se este aluno melhorar o IEG em 1 ponto, ele sai do Quartzo?"

    Args:
        sim_request: Request com nome do aluno e mudanças propostas
        request: Request object do FastAPI

    Returns:
        Comparação entre predição original e simulada com análise de impacto
    """
    prediction_service = request.app.state.prediction_service
    result = prediction_service.simulate_scenario(
        student_name=sim_request.NOME,
        changes=sim_request.changes
    )
    return JSONResponse(content=result)
