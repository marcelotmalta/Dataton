# models.py
"""
Modelos Pydantic para validação de dados
"""
from pydantic import BaseModel


class StudentMetrics(BaseModel):
    """Métricas de desempenho do estudante"""
    IAN: float = None
    IDA: float = None
    IEG: float = None
    IAA: float = None
    IPS: float = None
    IPP: float = None
    IPV: float = None
    FASE: int = None
    DEFA: float = 0.0
    NOME: str = None
