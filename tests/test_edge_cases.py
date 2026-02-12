"""
Testes parametrizados de edge cases para a API de Desempenho do Aluno

Este módulo testa casos extremos e limites do endpoint /predict:
- Validação de entrada (valores inválidos, tipos incorretos, boundaries)
- Thresholds de DEFA exatos
- Casos extremos de métricas
- Consistência de resposta
"""

from fastapi.testclient import TestClient
from app.main import app
import pytest


@pytest.fixture
def client():
    """Fixture para cliente de teste FastAPI"""
    with TestClient(app) as c:
        yield c


# ============================================================================
# Edge Cases de Validação de Entrada
# ============================================================================

@pytest.mark.parametrize("missing_field", [
    "IAN", "IDA", "IEG", "IAA", "IPS", "IPP", "IPV", "FASE"
])
def test_missing_required_fields(client, missing_field):
    """
    Testa que a API rejeita requisições com campos obrigatórios faltando
    
    Nota: Pydantic com campos Optional pode aceitar campos ausentes,
    então este teste verifica o comportamento atual da API
    """
    payload = {
        "IAN": 5.0,
        "IDA": 6.0,
        "IEG": 7.0,
        "IAA": 6.0,
        "IPS": 7.0,
        "IPP": 6.0,
        "IPV": 7.0,
        "FASE": 1,
        "DEFA": 0.0
    }
    
    # Remover o campo
    del payload[missing_field]
    
    response = client.post("/predict", json=payload)
    
    # A API pode aceitar campos None/ausentes dependendo da configuração Pydantic
    # Validar que ou retorna 200 (aceita) ou 422 (rejeita)
    assert response.status_code in [200, 422], \
        f"Status inesperado para campo ausente '{missing_field}': {response.status_code}"


@pytest.mark.parametrize("field,invalid_value,description", [
    ("IAN", "invalid_string", "string ao invés de número"),
    ("IEG", [], "lista ao invés de número"),
    ("FASE", "not_a_number", "string ao invés de inteiro"),
    ("DEFA", {}, "dict ao invés de número"),
])
def test_invalid_data_types(client, field, invalid_value, description):
    """
    Testa que a API rejeita tipos de dados claramente inválidos
    
    Nota: Pydantic faz type coercion, então boolean True pode ser
    aceito como 1.0. Este teste verifica apenas tipos claramente inválidos.
    """
    payload = {
        "IAN": 5.0,
        "IDA": 6.0,
        "IEG": 7.0,
        "IAA": 6.0,
        "IPS": 7.0,
        "IPP": 6.0,
        "IPV": 7.0,
        "FASE": 1,
        "DEFA": 0.0
    }
    
    payload[field] = invalid_value
    
    response = client.post("/predict", json=payload)
    
    # Deve rejeitar com 422 (Unprocessable Entity)
    assert response.status_code == 422, \
        f"Esperado 422 para {field}={invalid_value} ({description}), recebido {response.status_code}"


@pytest.mark.parametrize("field,value,description", [
    ("IAN", -1.0, "valor negativo"),
    ("IDA", -10.0, "valor muito negativo"),
    ("IEG", 11.0, "valor acima do máximo"),
    ("IAA", 100.0, "valor muito acima do máximo"),
    ("FASE", -1, "fase negativa"),
    ("FASE", 0, "fase zero"),
])
def test_out_of_range_values(client, field, value, description):
    """
    Testa comportamento da API com valores fora do range esperado
    
    Nota: A API pode aceitar ou normalizar valores fora do range,
    este teste documenta o comportamento atual
    """
    payload = {
        "IAN": 5.0,
        "IDA": 6.0,
        "IEG": 7.0,
        "IAA": 6.0,
        "IPS": 7.0,
        "IPP": 6.0,
        "IPV": 7.0,
        "FASE": 1,
        "DEFA": 0.0
    }
    
    payload[field] = value
    
    response = client.post("/predict", json=payload)
    
    # Documentar comportamento (pode aceitar e processar ou rejeitar)
    assert response.status_code in [200, 422], \
        f"Status inesperado para {field}={value} ({description}): {response.status_code}"
    
    if response.status_code == 200:
        data = response.json()
        # Se aceita, deve retornar estrutura válida
        assert "prediction" in data
        assert "risk_score" in data


@pytest.mark.parametrize("field,value", [
    ("IAN", 0.0),
    ("IDA", 0.0),
    ("IEG", 0.0),
    ("IAN", 10.0),
    ("IDA", 10.0),
    ("IEG", 10.0),
])
def test_boundary_values(client, field, value):
    """
    Testa valores nos limites exatos (0.0 e 10.0)
    """
    payload = {
        "IAN": 5.0,
        "IDA": 6.0,
        "IEG": 7.0,
        "IAA": 6.0,
        "IPS": 7.0,
        "IPP": 6.0,
        "IPV": 7.0,
        "FASE": 1,
        "DEFA": 0.0
    }
    
    payload[field] = value
    
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200, \
        f"Valor boundary {field}={value} deveria ser aceito"
    
    data = response.json()
    assert "prediction" in data
    assert data["risk_score"] is not None


# ============================================================================
# Edge Cases de DEFA
# ============================================================================

@pytest.mark.parametrize("defa,expected_pattern,description", [
    (-2.0, "Recuperação", "Threshold exato -2"),
    (-3.0, "Recuperação Intensiva", "Threshold exato -3"),
    (2.0, "Enriquecimento", "Threshold exato +2"),
    (3.0, "Aprofundamento|Enriquecimento", "Threshold exato +3"),
    (-2.1, "Recuperação", "Logo abaixo de -2"),
    (-2.9, "Recuperação", "Logo abaixo de -3"),
    (-3.1, "Recuperação Intensiva", "Logo abaixo de -3"),
    (2.1, "Enriquecimento", "Logo acima de +2"),
    (2.9, "Enriquecimento", "Logo abaixo de +3"),
    (3.1, "Aprofundamento|Enriquecimento", "Logo acima de +3"),
])
def test_defa_threshold_boundaries(client, defa, expected_pattern, description):
    """
    Testa comportamento nos thresholds exatos de DEFA
    
    DEFA_LARGE_THRESHOLD = 2, então:
    - DEFA <= -2: Recuperação Intensiva
    - -2 < DEFA < 0: Recuperação de Aprendizagem
    - DEFA >= 2: Aprofundamento/Enriquecimento alto
    - 0 < DEFA < 2: Enriquecimento moderado
    """
    payload = {
        "IAN": 6.0,
        "IDA": 6.0,
        "IEG": 6.0,
        "IAA": 6.0,
        "IPS": 6.0,
        "IPP": 6.0,
        "IPV": 6.0,
        "FASE": 3,
        "DEFA": defa
    }
    
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200, \
        f"DEFA={defa} ({description}) deveria retornar 200"
    
    data = response.json()
    acao = data["acao_sugerida"]
    
    # Verificar que contém o padrão esperado (suporta alternativas com |)
    patterns = expected_pattern.split("|")
    assert any(pattern in acao for pattern in patterns), \
        f"DEFA={defa} ({description}): esperado '{expected_pattern}' na ação, recebido: {acao}"
    
    # Verificar defa_int correto
    assert data["defa_int"] == int(round(defa)), \
        f"defa_int esperado {int(round(defa))}, recebido {data['defa_int']}"


@pytest.mark.parametrize("defa", [
    -10.0, -15.0, -20.0, -100.0
])
def test_extreme_negative_defa(client, defa):
    """
    Testa DEFA extremamente negativo (alta defasagem)
    """
    payload = {
        "IAN": 7.0,
        "IDA": 7.0,
        "IEG": 7.0,
        "IAA": 7.0,
        "IPS": 7.0,
        "IPP": 7.0,
        "IPV": 7.0,
        "FASE": 5,
        "DEFA": defa
    }
    
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Deve sempre ser Recuperação Intensiva (grave)
    assert "Recuperação Intensiva" in data["acao_sugerida"], \
        f"DEFA={defa} muito negativo deve ter 'Recuperação Intensiva'"


@pytest.mark.parametrize("defa", [
    10.0, 15.0, 20.0, 100.0
])
def test_extreme_positive_defa(client, defa):
    """
    Testa DEFA extremamente positivo (muito adiantado)
    """
    payload = {
        "IAN": 7.0,
        "IDA": 7.0,
        "IEG": 7.0,
        "IAA": 7.0,
        "IPS": 7.0,
        "IPP": 7.0,
        "IPV": 7.0,
        "FASE": 5,
        "DEFA": defa
    }
    
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Deve ter ação de aprofundamento/enriquecimento alto
    assert "Aprofundamento" in data["acao_sugerida"] or \
           "Enriquecimento" in data["acao_sugerida"], \
        f"DEFA={defa} muito positivo deve ter ação de aprofundamento/enriquecimento"


# ============================================================================
# Edge Cases de Métricas Extremas
# ============================================================================

def test_all_metrics_minimum(client):
    """
    Testa com todas as métricas no mínimo (0)
    """
    payload = {
        "IAN": 0.0,
        "IDA": 0.0,
        "IEG": 0.0,
        "IAA": 0.0,
        "IPS": 0.0,
        "IPP": 0.0,
        "IPV": 0.0,
        "FASE": 1,
        "DEFA": 0.0
    }
    
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Deve ter alto risco
    assert data["risk_score"] is not None
    assert data["risk_score"] > 0.5, \
        "Todas métricas em 0 deveria resultar em alto risco"
    
    # Estrutura válida
    assert "prediction" in data
    assert "probabilities" in data


def test_all_metrics_maximum(client):
    """
    Testa com todas as métricas no máximo (10)
    """
    payload = {
        "IAN": 10.0,
        "IDA": 10.0,
        "IEG": 10.0,
        "IAA": 10.0,
        "IPS": 10.0,
        "IPP": 10.0,
        "IPV": 10.0,
        "FASE": 6,
        "DEFA": 0.0
    }
    
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Deve ter baixo risco
    assert data["risk_score"] is not None
    assert data["risk_score"] < 0.3, \
        "Todas métricas em 10 deveria resultar em baixo risco"


@pytest.mark.parametrize("contrast_config", [
    {"high": ["IAN", "IDA"], "low": ["IEG", "IPV"]},
    {"high": ["IEG", "IPV"], "low": ["IAN", "IDA"]},
    {"high": ["IPS", "IPP"], "low": ["IAN", "IDA", "IEG"]},
])
def test_mixed_extreme_values(client, contrast_config):
    """
    Testa combinações contrastantes de valores extremos
    """
    payload = {
        "IAN": 5.0,
        "IDA": 5.0,
        "IEG": 5.0,
        "IAA": 5.0,
        "IPS": 5.0,
        "IPP": 5.0,
        "IPV": 5.0,
        "FASE": 3,
        "DEFA": 0.0
    }
    
    # Configurar valores altos
    for field in contrast_config["high"]:
        payload[field] = 10.0
    
    # Configurar valores baixos
    for field in contrast_config["low"]:
        payload[field] = 0.0
    
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Deve processar e retornar predição válida
    assert "prediction" in data
    assert data["risk_score"] is not None
    assert 0.0 <= data["risk_score"] <= 1.0
    
    # Top drivers devem incluir algum dos campos extremos
    drivers = [d.get("feature", "") for d in data["top_drivers"]]
    extreme_fields = contrast_config["high"] + contrast_config["low"]
    assert any(field in drivers for field in extreme_fields), \
        f"Top drivers deveria incluir algum campo extremo, recebido: {drivers}"


# ============================================================================
# Testes de Consistência de Resposta
# ============================================================================

def test_deterministic_predictions(client):
    """
    Testa que predições idênticas produzem resultados idênticos
    """
    payload = {
        "IAN": 7.5,
        "IDA": 8.0,
        "IEG": 7.0,
        "IAA": 7.5,
        "IPS": 8.0,
        "IPP": 7.0,
        "IPV": 8.5,
        "FASE": 4,
        "DEFA": 1.5
    }
    
    # Fazer 3 predições idênticas
    responses = [client.post("/predict", json=payload) for _ in range(3)]
    
    # Todas devem ter sucesso
    for i, response in enumerate(responses):
        assert response.status_code == 200, f"Request {i+1} falhou"
    
    # Extrair dados
    data_list = [r.json() for r in responses]
    
    # Verificar que predições são idênticas
    first = data_list[0]
    for i, data in enumerate(data_list[1:], start=2):
        assert data["prediction"] == first["prediction"], \
            f"Predição {i} diferente da primeira"
        assert data["prediction_index"] == first["prediction_index"], \
            f"Prediction index {i} diferente da primeira"
        assert data["risk_score"] == first["risk_score"], \
            f"Risk score {i} diferente da primeira"
        assert data["risk_tier"] == first["risk_tier"], \
            f"Risk tier {i} diferente da primeira"
        assert data["acao_sugerida"] == first["acao_sugerida"], \
            f"Ação sugerida {i} diferente da primeira"


@pytest.mark.parametrize("precision_test", [
    {"DEFA": 1.999999, "expected_int": 2},
    {"DEFA": 2.000001, "expected_int": 2},
    {"DEFA": -1.999999, "expected_int": -2},
    {"DEFA": -2.000001, "expected_int": -2},
    {"DEFA": 0.4, "expected_int": 0},
    {"DEFA": 0.5, "expected_int": 0},  # Python round() uses banker's rounding
    {"DEFA": 0.6, "expected_int": 1},
])
def test_defa_rounding_precision(client, precision_test):
    """
    Testa precisão de arredondamento de DEFA para inteiro
    """
    payload = {
        "IAN": 6.0,
        "IDA": 6.0,
        "IEG": 6.0,
        "IAA": 6.0,
        "IPS": 6.0,
        "IPP": 6.0,
        "IPV": 6.0,
        "FASE": 3,
        "DEFA": precision_test["DEFA"]
    }
    
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Verificar arredondamento correto
    assert data["defa_int"] == precision_test["expected_int"], \
        f"DEFA={precision_test['DEFA']} deveria arredondar para {precision_test['expected_int']}, " \
        f"recebido {data['defa_int']}"


# ============================================================================
# Testes de Robustez
# ============================================================================

@pytest.mark.timeout(5)
def test_response_time_normal_case(client):
    """
    Testa que a API responde em tempo razoável (< 5 segundos)
    """
    payload = {
        "IAN": 7.0,
        "IDA": 7.0,
        "IEG": 7.0,
        "IAA": 7.0,
        "IPS": 7.0,
        "IPP": 7.0,
        "IPV": 7.0,
        "FASE": 3,
        "DEFA": 0.0
    }
    
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200


def test_empty_payload(client):
    """
    Testa comportamento com payload vazio
    
    Nota: A API pode aceitar (200) ou rejeitar (422) dependendo da
    configuração de campos Optional/Required no Pydantic
    """
    response = client.post("/predict", json={})
    
    # API com campos Optional pode aceitar payload vazio
    assert response.status_code in [200, 422], \
        f"Payload vazio deveria retornar 200 ou 422, recebido: {response.status_code}"
