"""
Testes para DiagnosticService - Diagnóstico automatizado pedagógico.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.services.history_service import HistoryService
from app.services.diagnostic_service import DiagnosticService


@pytest.fixture
def mock_model_service():
    """ModelService mockado com dados de teste"""
    svc = MagicMock()
    svc.df_base = pd.DataFrame([
        # Aluno com gargalo acadêmico: IDA e IAN baixos
        {"NOME": "Aluno-Academico", "ANO": 23, "INDE": 5.0, "IAN": 3.5, "IDA": 4.0, "IEG": 7.0, "IAA": 7.5, "IPS": 7.0, "IPP": 6.0, "IPV": 6.0, "DEFA": -1, "FASE": 2},
        {"NOME": "Aluno-Academico", "ANO": 24, "INDE": 4.5, "IAN": 2.5, "IDA": 2.8, "IEG": 6.5, "IAA": 7.0, "IPS": 6.5, "IPP": 5.5, "IPV": 5.5, "DEFA": -2, "FASE": 3},
        # Aluno com risco de desengajamento: IEG baixo (< 3.0 = grave)
        {"NOME": "Aluno-Desengajado", "ANO": 24, "INDE": 6.0, "IAN": 6.5, "IDA": 7.0, "IEG": 2.5, "IAA": 7.0, "IPS": 7.0, "IPP": 5.0, "IPV": 6.0, "DEFA": 0, "FASE": 2},
        # Aluno com vulnerabilidade psicossocial: IPS e IAA baixos
        {"NOME": "Aluno-Vulneravel", "ANO": 24, "INDE": 5.5, "IAN": 6.0, "IDA": 6.5, "IEG": 6.0, "IAA": 2.5, "IPS": 2.8, "IPP": 5.0, "IPV": 5.5, "DEFA": 0, "FASE": 1},
        # Aluno saudável: todos os indicadores bons
        {"NOME": "Aluno-Saudavel", "ANO": 24, "INDE": 8.5, "IAN": 8.0, "IDA": 8.5, "IEG": 8.0, "IAA": 8.5, "IPS": 9.0, "IPP": 7.5, "IPV": 8.0, "DEFA": 1, "FASE": 3},
        # Aluno com múltiplos problemas
        {"NOME": "Aluno-Critico", "ANO": 24, "INDE": 3.5, "IAN": 2.5, "IDA": 3.0, "IEG": 2.0, "IAA": 3.0, "IPS": 2.5, "IPP": 3.0, "IPV": 3.0, "DEFA": -3, "FASE": 1},
    ])
    return svc


@pytest.fixture
def diagnostic_service(mock_model_service):
    """DiagnosticService com HistoryService conectado"""
    history_svc = HistoryService(mock_model_service)
    return DiagnosticService(mock_model_service, history_svc)


class TestDiagnoseAcademic:
    """Testes para diagnóstico de Gargalo Acadêmico"""

    def test_low_ida_ian_detected(self, diagnostic_service):
        """Deve detectar gargalo acadêmico com IDA/IAN baixos"""
        result = diagnostic_service.diagnose_student("Aluno-Academico")
        diagnostics = result["diagnosticos"]

        academic = [d for d in diagnostics if d["tipo"] == "academico"]
        assert len(academic) > 0
        assert academic[0]["gravidade"] in ("grave", "moderado")
        assert len(academic[0]["intervencoes"]) > 0

    def test_healthy_student_no_academic(self, diagnostic_service):
        """Aluno saudável não deve ter diagnóstico acadêmico"""
        result = diagnostic_service.diagnose_student("Aluno-Saudavel")
        diagnostics = result["diagnosticos"]

        academic = [d for d in diagnostics if d["tipo"] == "academico"]
        assert len(academic) == 0


class TestDiagnoseEngagement:
    """Testes para diagnóstico de Risco de Desengajamento"""

    def test_low_ieg_detected(self, diagnostic_service):
        """Deve detectar desengajamento com IEG baixo"""
        result = diagnostic_service.diagnose_student("Aluno-Desengajado")
        diagnostics = result["diagnosticos"]

        engagement = [d for d in diagnostics if d["tipo"] == "desengajamento"]
        assert len(engagement) > 0
        assert engagement[0]["gravidade"] == "grave"  # IEG=3.0 < 3.0 threshold

    def test_healthy_student_no_engagement(self, diagnostic_service):
        """Aluno saudável não deve ter diagnóstico de desengajamento"""
        result = diagnostic_service.diagnose_student("Aluno-Saudavel")
        diagnostics = result["diagnosticos"]

        engagement = [d for d in diagnostics if d["tipo"] == "desengajamento"]
        assert len(engagement) == 0


class TestDiagnosePsychosocial:
    """Testes para diagnóstico de Vulnerabilidade Psicossocial"""

    def test_low_ips_iaa_detected(self, diagnostic_service):
        """Deve detectar vulnerabilidade psicossocial com IPS/IAA baixos"""
        result = diagnostic_service.diagnose_student("Aluno-Vulneravel")
        diagnostics = result["diagnosticos"]

        psycho = [d for d in diagnostics if d["tipo"] == "psicossocial"]
        assert len(psycho) > 0
        assert len(psycho[0]["intervencoes"]) > 0

    def test_healthy_student_no_psycho(self, diagnostic_service):
        """Aluno saudável não deve ter diagnóstico psicossocial"""
        result = diagnostic_service.diagnose_student("Aluno-Saudavel")
        diagnostics = result["diagnosticos"]

        psycho = [d for d in diagnostics if d["tipo"] == "psicossocial"]
        assert len(psycho) == 0


class TestDiagnoseComplete:
    """Testes para diagnóstico completo integrado"""

    def test_critical_student_multiple_diagnostics(self, diagnostic_service):
        """Aluno crítico deve ter múltiplos diagnósticos"""
        result = diagnostic_service.diagnose_student("Aluno-Critico")
        diagnostics = result["diagnosticos"]

        tipos = {d["tipo"] for d in diagnostics}
        assert "academico" in tipos
        assert "desengajamento" in tipos
        assert "psicossocial" in tipos

    def test_includes_trajectory(self, diagnostic_service):
        """Diagnóstico completo deve incluir trajetória quando disponível"""
        result = diagnostic_service.diagnose_student("Aluno-Academico")

        assert "trajetoria" in result
        assert result["trajetoria"] is not None

    def test_includes_ipv_ida_cross(self, diagnostic_service):
        """Diagnóstico completo deve incluir cruzamento IPV×IDA"""
        result = diagnostic_service.diagnose_student("Aluno-Academico")

        assert "cruzamento_ipv_ida" in result

    def test_includes_summary(self, diagnostic_service):
        """Diagnóstico deve incluir resumo textual"""
        result = diagnostic_service.diagnose_student("Aluno-Critico")

        assert "resumo" in result
        assert len(result["resumo"]) > 0
        assert "Aluno-Critico" in result["resumo"]

    def test_healthy_student_clean(self, diagnostic_service):
        """Aluno saudável deve ter diagnóstico limpo"""
        result = diagnostic_service.diagnose_student("Aluno-Saudavel")

        assert len(result["diagnosticos"]) == 0
        assert "✅" in result["resumo"]

    def test_student_not_found(self, diagnostic_service):
        """Aluno inexistente deve retornar 404"""
        with pytest.raises(HTTPException) as exc_info:
            diagnostic_service.diagnose_student("NaoExiste")
        assert exc_info.value.status_code == 404
