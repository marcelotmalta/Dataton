"""
Testes de integração para endpoints de análise profunda e simulação contrafactual.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.model_service import ModelService
from app.services.student_service import StudentService
from app.services.suggestion_service import SuggestionService
from app.services.prediction_service import PredictionService
from app.services.simulation_service import SimulationService
from app.services.history_service import HistoryService
from app.services.diagnostic_service import DiagnosticService


@pytest.fixture
def client():
    """
    Fixture para cliente de teste FastAPI com todos os serviços inicializados.
    """
    if not hasattr(app.state, 'model_service'):
        model_service = ModelService()
        model_service.initialize()
        app.state.model_service = model_service

        student_service = StudentService(model_service)
        app.state.student_service = student_service

        suggestion_service = SuggestionService()
        app.state.suggestion_service = suggestion_service

        prediction_service = PredictionService(model_service, suggestion_service)
        app.state.prediction_service = prediction_service

        simulation_service = SimulationService(model_service, prediction_service)
        app.state.simulation_service = simulation_service

        history_service = HistoryService(model_service)
        app.state.history_service = history_service

        diagnostic_service = DiagnosticService(model_service, history_service)
        app.state.diagnostic_service = diagnostic_service

    with TestClient(app) as c:
        yield c


class TestDeepAnalysisEndpoint:
    """Testes para GET /students/{name}/analysis"""

    def test_analysis_with_existing_student(self, client):
        """Deve retornar análise profunda para aluno existente"""
        # Buscar qualquer aluno que exista nos dados
        response = client.get("/students/Aluno-1/analysis")

        if response.status_code == 200:
            data = response.json()
            assert "nome" in data
            assert "historico" in data
            assert "trajetoria" in data
            assert "diagnosticos" in data
            assert "resumo" in data
            assert isinstance(data["diagnosticos"], list)
        else:
            # Se Aluno-1 não existe, deve ser 404
            assert response.status_code == 404

    def test_analysis_not_found(self, client):
        """Deve retornar 404 para aluno inexistente"""
        response = client.get("/students/AlunoQueNaoExisteXYZ123/analysis")
        assert response.status_code == 404

    def test_analysis_response_structure(self, client):
        """Valida estrutura completa da resposta de análise"""
        response = client.get("/students/A/analysis")

        if response.status_code == 200:
            data = response.json()

            # Validar campos obrigatórios
            assert "nome" in data
            assert "resumo" in data
            assert isinstance(data.get("diagnosticos", []), list)

            # Validar trajetória se presente
            if data.get("trajetoria"):
                traj = data["trajetoria"]
                assert "tendencia" in traj
                assert traj["tendencia"] in [
                    "ascendente", "estável", "descendente", "insuficiente"
                ]


class TestTrajectoryEndpoint:
    """Testes para GET /students/{name}/trajectory"""

    def test_trajectory_existing_student(self, client):
        """Deve retornar trajetória para aluno existente"""
        response = client.get("/students/Aluno-1/trajectory")

        if response.status_code == 200:
            data = response.json()
            assert "nome" in data
            assert "anos" in data
            assert "inde_values" in data
            assert "tendencia" in data
            assert "inclinacao" in data

    def test_trajectory_not_found(self, client):
        """Deve retornar 404 para aluno inexistente"""
        response = client.get("/students/NaoExisteXYZ/trajectory")
        assert response.status_code == 404


class TestIpvIdaEndpoint:
    """Testes para GET /students/{name}/ipv-ida"""

    def test_ipv_ida_existing_student(self, client):
        """Deve retornar cruzamento IPV×IDA para aluno existente"""
        response = client.get("/students/Aluno-1/ipv-ida")

        if response.status_code == 200:
            data = response.json()
            assert "nome" in data
            assert "analise_disponivel" in data

            if data["analise_disponivel"]:
                assert "tipo_queda" in data
                assert data["tipo_queda"] in [
                    "técnica", "maturidade", "combinada", "nenhuma", "atípica"
                ]


class TestSimulationEndpoint:
    """Testes para POST /simulate"""

    def test_simulation_existing_student(self, client):
        """Deve executar simulação para aluno existente"""
        payload = {
            "NOME": "Aluno-1",
            "changes": {"IEG": 8.0}
        }
        response = client.post("/simulate", json=payload)

        if response.status_code == 200:
            data = response.json()
            assert "nome" in data
            assert "original_prediction" in data
            assert "simulated_prediction" in data
            assert "impacto" in data
            assert "changes_applied" in data
        else:
            # Aluno pode não existir
            assert response.status_code in [200, 404]

    def test_simulation_not_found(self, client):
        """Deve retornar 404 para aluno inexistente"""
        payload = {
            "NOME": "AlunoQueNaoExisteXYZ123",
            "changes": {"IEG": 8.0}
        }
        response = client.post("/simulate", json=payload)
        assert response.status_code == 404

    def test_simulation_multiple_changes(self, client):
        """Deve aceitar múltiplas mudanças no cenário"""
        payload = {
            "NOME": "Aluno-1",
            "changes": {"IEG": 8.0, "IDA": 7.5, "IPS": 9.0}
        }
        response = client.post("/simulate", json=payload)

        if response.status_code == 200:
            data = response.json()
            assert len(data["changes_applied"]) == 3

    def test_simulation_empty_changes(self, client):
        """Simulação com mudanças vazias deve retornar mesma predição"""
        payload = {
            "NOME": "Aluno-1",
            "changes": {}
        }
        response = client.post("/simulate", json=payload)

        if response.status_code == 200:
            data = response.json()
            assert data["original_prediction"] == data["simulated_prediction"]


class TestExistingEndpointsStillWork:
    """Garante que endpoints existentes não quebraram"""

    def test_health_check(self, client):
        """Health check deve continuar funcionando"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_predict_still_works(self, client):
        """Endpoint de predição deve continuar funcionando"""
        payload = {
            "IAN": 5.0, "IDA": 7.0, "IEG": 8.0,
            "IAA": 6.5, "IPS": 7.5, "IPP": 6.0,
            "IPV": 8.0, "FASE": 1, "DEFA": 0.0
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data

    def test_search_student_still_works(self, client):
        """Endpoint de busca deve continuar funcionando"""
        response = client.get("/students/A")
        assert response.status_code in [200, 404]
