# models.py
"""
Modelos Pydantic para validação de dados
"""
from pydantic import BaseModel
from typing import List, Optional, Dict


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


# ---------- Modelos de Trajetória ----------

class TrajectoryResult(BaseModel):
    """Resultado da análise de trajetória interanual"""
    anos: List[int] = []
    inde_values: List[Optional[float]] = []
    deltas: List[float] = []
    tendencia: str = "insuficiente"  # ascendente, estável, descendente, insuficiente
    inclinacao: float = 0.0
    num_registros: int = 0


# ---------- Modelos de Diagnóstico ----------

class DiagnosticResult(BaseModel):
    """Resultado de um diagnóstico individual"""
    tipo: str                    # academico, desengajamento, psicossocial
    gravidade: str               # leve, moderado, grave
    indicadores_afetados: List[str] = []
    intervencoes: List[str] = []


class DeepAnalysisResponse(BaseModel):
    """Resposta completa da análise profunda de um estudante"""
    nome: str
    historico: List[dict] = []
    trajetoria: Optional[TrajectoryResult] = None
    cruzamento_ipv_ida: Optional[dict] = None
    diagnosticos: List[DiagnosticResult] = []
    resumo: str = ""


# ---------- Modelos de Simulação Contrafactual ----------

class SimulationRequest(BaseModel):
    """Request para simulação contrafactual"""
    NOME: str
    changes: Dict[str, float]    # ex: {"IEG": 6.0, "IDA": 7.5}


class SimulationResponse(BaseModel):
    """Response da simulação contrafactual"""
    nome: str
    original_prediction: str
    simulated_prediction: str
    original_risk: Optional[float] = None
    simulated_risk: Optional[float] = None
    delta_risk: Optional[float] = None
    impacto: str = ""
    changes_applied: Dict[str, float] = {}
    original_values: Dict[str, Optional[float]] = {}
