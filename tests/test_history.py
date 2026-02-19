"""
Testes para HistoryService - Análise de trajetória e cruzamento IPV×IDA.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.services.history_service import HistoryService


@pytest.fixture
def mock_model_service():
    """ModelService mockado com dados de teste"""
    svc = MagicMock()
    svc.df_base = pd.DataFrame([
        {"NOME": "Aluno-Test", "ANO": 22, "INDE": 6.0, "IAN": 5.5, "IDA": 6.0, "IEG": 5.0, "IAA": 6.5, "IPS": 7.0, "IPP": 5.5, "IPV": 6.0, "DEFA": 0, "FASE": 1},
        {"NOME": "Aluno-Test", "ANO": 23, "INDE": 7.0, "IAN": 6.5, "IDA": 7.0, "IEG": 6.0, "IAA": 7.0, "IPS": 7.5, "IPP": 6.0, "IPV": 7.0, "DEFA": 0, "FASE": 2},
        {"NOME": "Aluno-Test", "ANO": 24, "INDE": 8.0, "IAN": 7.5, "IDA": 8.0, "IEG": 7.0, "IAA": 7.5, "IPS": 8.0, "IPP": 7.0, "IPV": 8.0, "DEFA": 1, "FASE": 3},
        {"NOME": "Aluno-Queda", "ANO": 22, "INDE": 9.0, "IAN": 8.5, "IDA": 9.0, "IEG": 8.0, "IAA": 8.5, "IPS": 8.0, "IPP": 8.0, "IPV": 9.0, "DEFA": 0, "FASE": 2},
        {"NOME": "Aluno-Queda", "ANO": 23, "INDE": 7.5, "IAN": 7.0, "IDA": 7.0, "IEG": 6.0, "IAA": 7.0, "IPS": 7.0, "IPP": 6.5, "IPV": 7.0, "DEFA": -1, "FASE": 3},
        {"NOME": "Aluno-Queda", "ANO": 24, "INDE": 6.0, "IAN": 5.5, "IDA": 5.5, "IEG": 5.0, "IAA": 6.0, "IPS": 6.0, "IPP": 5.0, "IPV": 5.5, "DEFA": -2, "FASE": 4},
        {"NOME": "Aluno-Unico", "ANO": 24, "INDE": 7.0, "IAN": 6.0, "IDA": 7.0, "IEG": 6.5, "IAA": 7.0, "IPS": 7.5, "IPP": 6.0, "IPV": 7.0, "DEFA": 0, "FASE": 1},
        {"NOME": "Aluno-Tecnica", "ANO": 23, "INDE": 8.0, "IAN": 7.5, "IDA": 8.0, "IEG": 7.0, "IAA": 7.5, "IPS": 7.5, "IPP": 7.0, "IPV": 8.0, "DEFA": 0, "FASE": 2},
        {"NOME": "Aluno-Tecnica", "ANO": 24, "INDE": 6.5, "IAN": 6.0, "IDA": 5.0, "IEG": 6.5, "IAA": 7.0, "IPS": 7.5, "IPP": 6.5, "IPV": 8.1, "DEFA": -1, "FASE": 3},
        {"NOME": "Aluno-Maturidade", "ANO": 23, "INDE": 8.0, "IAN": 7.5, "IDA": 8.0, "IEG": 7.0, "IAA": 7.5, "IPS": 7.5, "IPP": 7.0, "IPV": 8.0, "DEFA": 0, "FASE": 2},
        {"NOME": "Aluno-Maturidade", "ANO": 24, "INDE": 7.0, "IAN": 7.0, "IDA": 8.1, "IEG": 6.5, "IAA": 7.0, "IPS": 7.0, "IPP": 6.5, "IPV": 4.5, "DEFA": 0, "FASE": 3},
    ])
    return svc


class TestGetStudentTrajectory:
    """Testes para HistoryService.get_student_trajectory"""

    def test_trajectory_ascending(self, mock_model_service):
        """Aluno com INDE crescente deve ter tendência ascendente"""
        svc = HistoryService(mock_model_service)
        result = svc.get_student_trajectory("Aluno-Test")

        assert result["nome"] == "Aluno-Test"
        assert result["tendencia"] == "ascendente"
        assert result["inclinacao"] > 0
        assert len(result["anos"]) == 3
        assert result["inde_values"] == [6.0, 7.0, 8.0]
        assert len(result["deltas"]) == 2
        assert result["deltas"][0] == 1.0
        assert result["deltas"][1] == 1.0

    def test_trajectory_descending(self, mock_model_service):
        """Aluno com INDE decrescente deve ter tendência descendente"""
        svc = HistoryService(mock_model_service)
        result = svc.get_student_trajectory("Aluno-Queda")

        assert result["nome"] == "Aluno-Queda"
        assert result["tendencia"] == "descendente"
        assert result["inclinacao"] < 0
        assert len(result["anos"]) == 3

    def test_trajectory_single_year(self, mock_model_service):
        """Aluno com apenas 1 ano deve retornar tendência 'insuficiente'"""
        svc = HistoryService(mock_model_service)
        result = svc.get_student_trajectory("Aluno-Unico")

        assert result["nome"] == "Aluno-Unico"
        assert result["tendencia"] == "insuficiente"
        assert result["num_registros"] == 1
        assert len(result["deltas"]) == 0

    def test_trajectory_not_found(self, mock_model_service):
        """Aluno inexistente deve retornar 404"""
        svc = HistoryService(mock_model_service)
        with pytest.raises(HTTPException) as exc_info:
            svc.get_student_trajectory("NaoExiste")
        assert exc_info.value.status_code == 404

    def test_trajectory_indicators_per_year(self, mock_model_service):
        """Deve retornar indicadores completos por ano"""
        svc = HistoryService(mock_model_service)
        result = svc.get_student_trajectory("Aluno-Test")

        assert "indicadores_por_ano" in result
        assert len(result["indicadores_por_ano"]) == 3
        first_year = result["indicadores_por_ano"][0]
        assert "INDE" in first_year
        assert "IDA" in first_year
        assert "IPV" in first_year

    def test_trajectory_data_unavailable(self, mock_model_service):
        """Deve retornar 503 quando dados não disponíveis"""
        mock_model_service.df_base = None
        svc = HistoryService(mock_model_service)
        with pytest.raises(HTTPException) as exc_info:
            svc.get_student_trajectory("Aluno-Test")
        assert exc_info.value.status_code == 503


class TestCrossIpvIda:
    """Testes para HistoryService.cross_ipv_ida"""

    def test_technical_drop(self, mock_model_service):
        """IDA caiu, IPV manteve = queda técnica"""
        svc = HistoryService(mock_model_service)
        result = svc.cross_ipv_ida("Aluno-Tecnica")

        assert result["analise_disponivel"] is True
        assert result["tipo_queda"] == "técnica"
        assert result["detalhes"]["delta_ida"] < -0.3  # IDA dropped significantly
        # IPV should be stable (delta within threshold)

    def test_maturity_drop(self, mock_model_service):
        """IPV caiu, IDA manteve = queda de maturidade"""
        svc = HistoryService(mock_model_service)
        result = svc.cross_ipv_ida("Aluno-Maturidade")

        assert result["analise_disponivel"] is True
        assert result["tipo_queda"] == "maturidade"
        assert result["detalhes"]["delta_ipv"] < 0

    def test_combined_drop(self, mock_model_service):
        """Ambos caíram = queda combinada"""
        svc = HistoryService(mock_model_service)
        result = svc.cross_ipv_ida("Aluno-Queda")

        assert result["analise_disponivel"] is True
        assert result["tipo_queda"] == "combinada"

    def test_insufficient_history(self, mock_model_service):
        """Aluno com 1 ano = análise não disponível"""
        svc = HistoryService(mock_model_service)
        result = svc.cross_ipv_ida("Aluno-Unico")

        assert result["analise_disponivel"] is False
        assert result["tipo_queda"] is None

    def test_no_drop(self, mock_model_service):
        """Aluno ascendente = nenhuma queda"""
        svc = HistoryService(mock_model_service)
        result = svc.cross_ipv_ida("Aluno-Test")

        assert result["analise_disponivel"] is True
        assert result["tipo_queda"] == "nenhuma"
