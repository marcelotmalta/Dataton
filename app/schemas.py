from pydantic import BaseModel
from typing import List, Optional, Any

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

class PedagogicalSuggestion(BaseModel):
    perfil: str
    acao: str

class PredictionResponse(BaseModel):
    pedra_conceito: str
    status_defa_calculado: int
    confidence: Optional[float]
    sugestoes_pedagogicas: List[PedagogicalSuggestion]
    input_features: List[float]
