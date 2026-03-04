# tests/test_student_service.py
"""
Testes unitários para StudentService — cobrindo busca de alunos,
histórico ordenado e o novo método get_student_history.
"""
import pandas as pd
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.services.student_service import StudentService


# ────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────

@pytest.fixture
def mock_model_service():
    ms = MagicMock()
    ms.df_base = pd.DataFrame({
        "NOME": ["Ana Silva", "Ana Silva", "Bruno Costa"],
        "ANO": [2023, 2024, 2024],
        "FASE": [1, 2, 1],
        "IAN": [5.0, 6.0, 7.0],
        "IDA": [4.0, 5.0, 8.0],
        "IEG": [3.0, 4.0, 6.0],
        "IAA": [6.0, 7.0, 5.0],
        "IPS": [5.0, 6.0, 7.0],
        "IPP": [4.0, 5.0, 6.0],
        "IPV": [3.0, 4.0, 5.0],
        "DEFA": [0.0, -1.0, 1.0],
    })
    return ms


@pytest.fixture
def service(mock_model_service):
    return StudentService(mock_model_service)


# ────────────────────────────────────────────
# search_student_by_name
# ────────────────────────────────────────────

class TestSearchStudentByName:
    def test_exact_match(self, service):
        result = service.search_student_by_name("Ana Silva")
        assert result["nome"] == "Ana Silva"
        assert len(result["historico"]) == 2

    def test_partial_match(self, service):
        result = service.search_student_by_name("Ana")
        assert result["nome"] == "Ana Silva"

    def test_case_insensitive(self, service):
        result = service.search_student_by_name("ana silva")
        assert result["nome"] == "Ana Silva"

    def test_not_found(self, service):
        with pytest.raises(HTTPException) as exc_info:
            service.search_student_by_name("Zé Ninguém")
        assert exc_info.value.status_code == 404

    def test_data_not_available(self, service, mock_model_service):
        mock_model_service.df_base = None
        with pytest.raises(HTTPException) as exc_info:
            service.search_student_by_name("Ana")
        assert exc_info.value.status_code == 503

    def test_no_nome_column(self, service, mock_model_service):
        mock_model_service.df_base = pd.DataFrame({"X": [1]})
        with pytest.raises(HTTPException) as exc_info:
            service.search_student_by_name("Ana")
        assert exc_info.value.status_code == 404

    def test_historico_ordered_by_ano(self, service):
        result = service.search_student_by_name("Ana Silva")
        historico = result["historico"]
        anos = [h["ANO"] for h in historico]
        assert anos == sorted(anos)


# ────────────────────────────────────────────
# get_student_history
# ────────────────────────────────────────────

class TestGetStudentHistory:
    def test_returns_history(self, service):
        history = service.get_student_history("Ana Silva")
        assert len(history) == 2
        assert history[0]["ANO"] == 2023
        assert history[1]["ANO"] == 2024

    def test_not_found_returns_empty(self, service):
        history = service.get_student_history("Inexistente")
        assert history == []

    def test_data_unavailable_returns_empty(self, service, mock_model_service):
        mock_model_service.df_base = None
        history = service.get_student_history("Ana")
        assert history == []


# ────────────────────────────────────────────
# _build_historico
# ────────────────────────────────────────────

class TestBuildHistorico:
    def test_returns_all_fields(self, service, mock_model_service):
        matches = mock_model_service.df_base[mock_model_service.df_base["NOME"] == "Ana Silva"]
        historico = service._build_historico(matches)
        expected_fields = {'ANO', 'FASE', 'IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'DEFA'}
        for item in historico:
            assert set(item.keys()) == expected_fields

    def test_sorted_ascending(self, service, mock_model_service):
        matches = mock_model_service.df_base[mock_model_service.df_base["NOME"] == "Ana Silva"]
        historico = service._build_historico(matches)
        anos = [h["ANO"] for h in historico]
        assert anos == sorted(anos)
