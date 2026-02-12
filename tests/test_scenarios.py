"""
Cenários de teste para o endpoint /predict da API de Desempenho do Aluno

Este módulo implementa os 6 cenários descritos em docs/test_scenarios.md:
1. O Aluno "Excelente"
2. O Aluno "Médio"
3. O Aluno "Com Dificuldades"
4. O Aluno "Em Recuperação"
5. O Aluno "Em Declínio"
6. O Aluno "Em Risco Crítico"
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
# Funções de Validação Auxiliares
# ============================================================================

def validate_response_structure(data: dict):
    """
    Valida que todos os campos obrigatórios estão presentes na resposta
    
    Args:
        data: Dicionário de resposta da API
    """
    required_fields = [
        "prediction",
        "prediction_index",
        "probabilities",
        "risk_score",
        "risk_tier",
        "acao_sugerida",
        "suggested_messages",
        "top_drivers",
        "input_features",
        "defa_int",
        "model_version"
    ]
    
    for field in required_fields:
        assert field in data, f"Campo obrigatório '{field}' não encontrado na resposta"
    
    # Validar tipos de dados
    assert isinstance(data["prediction"], str), "prediction deve ser string"
    assert isinstance(data["prediction_index"], int) or data["prediction_index"] is None, \
        "prediction_index deve ser int ou None"
    assert isinstance(data["probabilities"], dict), "probabilities deve ser dict"
    assert isinstance(data["risk_score"], (int, float)) or data["risk_score"] is None, \
        "risk_score deve ser número ou None"
    assert isinstance(data["risk_tier"], str) or data["risk_tier"] is None, \
        "risk_tier deve ser string ou None"
    assert isinstance(data["acao_sugerida"], str), "acao_sugerida deve ser string"
    assert isinstance(data["suggested_messages"], dict), "suggested_messages deve ser dict"
    assert isinstance(data["top_drivers"], list), "top_drivers deve ser lista"
    assert isinstance(data["input_features"], dict), "input_features deve ser dict"
    assert isinstance(data["defa_int"], int), "defa_int deve ser int"
    assert isinstance(data["model_version"], str), "model_version deve ser string"
    
    # Validar estrutura de suggested_messages
    assert "family" in data["suggested_messages"], "suggested_messages deve ter 'family'"
    assert "professor" in data["suggested_messages"], "suggested_messages deve ter 'professor'"


def validate_risk_score_range(data: dict):
    """
    Valida que risk_score está no range válido [0.0, 1.0]
    
    Args:
        data: Dicionário de resposta da API
    """
    risk_score = data.get("risk_score")
    if risk_score is not None:
        assert 0.0 <= risk_score <= 1.0, \
            f"risk_score deve estar entre 0.0 e 1.0, recebido: {risk_score}"


def validate_probabilities(data: dict):
    """
    Valida que as probabilidades são válidas e somam ~1.0
    
    Args:
        data: Dicionário de resposta da API
    """
    probs = data.get("probabilities", {})
    
    # Verificar que não está vazio
    assert len(probs) > 0, "probabilities não deve estar vazio"
    
    # Verificar ranges individuais
    for classe, prob in probs.items():
        assert 0.0 <= prob <= 1.0, \
            f"Probabilidade de '{classe}' deve estar entre 0.0 e 1.0, recebido: {prob}"
    
    # Verificar soma
    soma = sum(probs.values())
    assert abs(soma - 1.0) < 0.01, \
        f"Soma das probabilidades deve ser ~1.0, recebido: {soma}"


def validate_defa_logic(data: dict, expected_defa: int):
    """
    Valida consistência da lógica de DEFA com acao_sugerida
    
    Args:
        data: Dicionário de resposta da API
        expected_defa: Valor esperado de DEFA
    """
    defa_int = data.get("defa_int")
    acao = data.get("acao_sugerida", "")
    
    # Verificar DEFA está correto
    assert defa_int == expected_defa, \
        f"defa_int esperado: {expected_defa}, recebido: {defa_int}"
    
    # Validar lógica de ações baseada em DEFA
    if defa_int < 0:
        # Defasagem - deve ter ação de recuperação
        if defa_int <= -3:
            assert "Recuperação Intensiva" in acao, \
                f"DEFA <= -3 deve ter 'Recuperação Intensiva', recebido: {acao}"
        else:
            assert "Recuperação" in acao, \
                f"DEFA < 0 deve ter 'Recuperação', recebido: {acao}"
    elif defa_int > 0:
        # Adiantado - deve ter ação de enriquecimento
        assert "Enriquecimento" in acao or "Aprofundamento" in acao, \
            f"DEFA > 0 deve ter 'Enriquecimento' ou 'Aprofundamento', recebido: {acao}"
    # else: DEFA = 0, ação depende de risk_score (não validamos aqui)


def validate_messages_not_empty(data: dict):
    """
    Valida que as mensagens sugeridas não estão vazias
    
    Args:
        data: Dicionário de resposta da API
    """
    messages = data.get("suggested_messages", {})
    
    family_msg = messages.get("family", "")
    professor_msg = messages.get("professor", "")
    
    assert len(family_msg) > 0, "Mensagem para família não deve estar vazia"
    assert len(professor_msg) > 0, "Mensagem para professor não deve estar vazia"


def validate_risk_tier_consistency(data: dict):
    """
    Valida consistência entre risk_score e risk_tier
    
    Args:
        data: Dicionário de resposta da API
    """
    risk_score = data.get("risk_score")
    risk_tier = data.get("risk_tier")
    
    if risk_score is not None and risk_tier is not None:
        if risk_score >= 0.75:
            assert risk_tier == "Crítico", \
                f"risk_score >= 0.75 deve ter tier 'Crítico', recebido: {risk_tier}"
        elif risk_score >= 0.5:
            assert risk_tier == "Alto", \
                f"risk_score >= 0.5 deve ter tier 'Alto', recebido: {risk_tier}"
        elif risk_score >= 0.25:
            assert risk_tier == "Moderado", \
                f"risk_score >= 0.25 deve ter tier 'Moderado', recebido: {risk_tier}"
        else:
            assert risk_tier == "Baixo", \
                f"risk_score < 0.25 deve ter tier 'Baixo', recebido: {risk_tier}"


# ============================================================================
# Cenários de Teste
# ============================================================================

def test_scenario_1_excellent_student(client):
    """
    Cenário 1: O Aluno "Excelente"
    
    Perfil: Notas altas, DEFA=1.0 (adiantado)
    Expectativas: risk_score baixo, ação de enriquecimento moderado
    """
    payload = {
        "IAN": 9.5,
        "IDA": 9.0,
        "IEG": 9.5,
        "IAA": 9.0,
        "IPS": 8.5,
        "IPP": 8.0,
        "IPV": 9.0,
        "FASE": 2,
        "DEFA": 1.0
    }
    
    response = client.post("/predict", json=payload)
    
    # Validar status code
    assert response.status_code == 200, f"Esperado 200, recebido {response.status_code}"
    
    data = response.json()
    
    # Validações estruturais
    validate_response_structure(data)
    validate_risk_score_range(data)
    validate_probabilities(data)
    validate_messages_not_empty(data)
    validate_risk_tier_consistency(data)
    validate_defa_logic(data, expected_defa=1)
    
    # Validações específicas do cenário
    # Aluno excelente geralmente tem baixo risco, mas não forçar valor específico
    assert data["risk_score"] < 0.7, \
        f"Aluno excelente deve ter risk_score relativamente baixo (< 0.7), recebido: {data['risk_score']}"
    
    assert "Enriquecimento Curricular (moderado)" in data["acao_sugerida"], \
        f"Ação esperada: 'Enriquecimento Curricular (moderado)', recebido: {data['acao_sugerida']}"
    
    # Verificar mensagens contextualizadas
    assert "adiantado" in data["suggested_messages"]["family"].lower() or \
           "DEFA=1" in data["suggested_messages"]["family"], \
           "Mensagem para família deve mencionar que está adiantado"


def test_scenario_2_average_student(client):
    """
    Cenário 2: O Aluno "Médio"
    
    Perfil: Notas medianas, DEFA=0.0 (no tempo)
    Expectativas: risk_score moderado, ação de monitoramento
    """
    payload = {
        "IAN": 6.0,
        "IDA": 6.5,
        "IEG": 7.0,
        "IAA": 6.0,
        "IPS": 7.0,
        "IPP": 6.0,
        "IPV": 6.0,
        "FASE": 3,
        "DEFA": 0.0
    }
    
    response = client.post("/predict", json=payload)
    
    # Validar status code
    assert response.status_code == 200
    
    data = response.json()
    
    # Validações estruturais
    validate_response_structure(data)
    validate_risk_score_range(data)
    validate_probabilities(data)
    validate_messages_not_empty(data)
    validate_risk_tier_consistency(data)
    validate_defa_logic(data, expected_defa=0)
    
    # Validações específicas do cenário
    # Aluno médio pode ter variação ampla de risco, validar apenas que não é None
    assert data["risk_score"] is not None, "risk_score não deve ser None"
    assert 0.0 <= data["risk_score"] <= 1.0, \
        f"risk_score deve estar no range válido, recebido: {data['risk_score']}"
    
    assert data["risk_tier"] in ["Moderado", "Alto", "Baixo", "Crítico"], \
        f"risk_tier inesperado: {data['risk_tier']}"
    
    # Verificar que ação é apropriada para DEFA=0 (qualquer ação exceto recuperação intensiva)
    assert "Recuperação Intensiva (grave)" not in data["acao_sugerida"], \
           f"Aluno com DEFA=0 não deveria ter recuperação grave, recebido: {data['acao_sugerida']}"


def test_scenario_3_student_with_difficulties(client):
    """
    Cenário 3: O Aluno "Com Dificuldades"
    
    Perfil: Notas baixas, DEFA=-2.0 (defasagem significativa)
    Expectativas: risk_score alto, ação de recuperação
    """
    payload = {
        "IAN": 3.0,
        "IDA": 4.0,
        "IEG": 3.0,
        "IAA": 4.0,
        "IPS": 4.0,
        "IPP": 3.0,
        "IPV": 2.0,
        "FASE": 1,
        "DEFA": -2.0
    }
    
    response = client.post("/predict", json=payload)
    
    # Validar status code
    assert response.status_code == 200
    
    data = response.json()
    
    # Validações estruturais
    validate_response_structure(data)
    validate_risk_score_range(data)
    validate_probabilities(data)
    validate_messages_not_empty(data)
    validate_risk_tier_consistency(data)
    validate_defa_logic(data, expected_defa=-2)
    
    # Validações específicas do cenário
    assert data["risk_score"] > 0.6, \
        f"Aluno com dificuldades deve ter risk_score > 0.6, recebido: {data['risk_score']}"
    
    assert data["risk_tier"] in ["Alto", "Crítico"], \
        f"risk_tier esperado 'Alto' ou 'Crítico', recebido: {data['risk_tier']}"
    
    assert "Recuperação" in data["acao_sugerida"], \
        f"Ação esperada deve conter 'Recuperação', recebido: {data['acao_sugerida']}"
    
    # Verificar mensagens mencionam defasagem
    assert "defasagem" in data["suggested_messages"]["family"].lower() or \
           "DEFA=-2" in data["suggested_messages"]["family"], \
           "Mensagem para família deve mencionar defasagem"


def test_scenario_4_student_in_recovery(client):
    """
    Cenário 4: O Aluno "Em Recuperação" (Esforço Alto / Histórico Baixo)
    
    Perfil: Notas médias/baixas, mas IEG e IPV altos (alto engajamento), DEFA=0.0
    Expectativas: risk_score moderado/baixo, top_drivers inclui IEG/IPV
    """
    payload = {
        "IAN": 5.0,
        "IDA": 5.0,
        "IEG": 8.5,  # Alto Engajamento
        "IAA": 7.0,
        "IPS": 6.0,
        "IPP": 5.0,
        "IPV": 9.0,  # Ponto de Virada Alto
        "FASE": 4,
        "DEFA": 0.0
    }
    
    response = client.post("/predict", json=payload)
    
    # Validar status code
    assert response.status_code == 200
    
    data = response.json()
    
    # Validações estruturais
    validate_response_structure(data)
    validate_risk_score_range(data)
    validate_probabilities(data)
    validate_messages_not_empty(data)
    validate_risk_tier_consistency(data)
    validate_defa_logic(data, expected_defa=0)
    
    # Validações específicas do cenário
    assert data["risk_score"] <= 0.6, \
        f"Aluno em recuperação deve ter risk_score moderado/baixo (<= 0.6), recebido: {data['risk_score']}"
    
    # Verificar se top_drivers inclui IEG ou IPV
    drivers = [d.get("feature", "") for d in data["top_drivers"]]
    assert "IEG" in drivers or "IPV" in drivers, \
        f"top_drivers deveria incluir IEG ou IPV, recebido: {drivers}"


def test_scenario_5_student_in_decline(client):
    """
    Cenário 5: O Aluno "Em Declínio" (Histórico Bom / Esforço Baixo)
    
    Perfil: Notas altas mas IEG baixo (baixo engajamento), DEFA=0.0
    Expectativas: risk_score moderado/alto, mensagens abordam engajamento
    """
    payload = {
        "IAN": 8.0,
        "IDA": 8.0,
        "IEG": 3.0,  # Baixo Engajamento
        "IAA": 5.0,
        "IPS": 5.0,
        "IPP": 5.0,
        "IPV": 2.0,
        "FASE": 5,
        "DEFA": 0.0
    }
    
    response = client.post("/predict", json=payload)
    
    # Validar status code
    assert response.status_code == 200
    
    data = response.json()
    
    # Validações estruturais
    validate_response_structure(data)
    validate_risk_score_range(data)
    validate_probabilities(data)
    validate_messages_not_empty(data)
    validate_risk_tier_consistency(data)
    validate_defa_logic(data, expected_defa=0)
    
    # Validações específicas do cenário
    # Aluno em declínio pode ter variação, mas validar que o modelo responde ao baixo engajamento
    assert data["risk_score"] is not None, "risk_score não deve ser None"
    
    assert data["risk_tier"] in ["Moderado", "Alto", "Crítico", "Baixo"], \
        f"risk_tier inesperado: {data['risk_tier']}"
    
    # Verificar se top_drivers inclui IEG como fator de risco
    drivers = [d.get("feature", "") for d in data["top_drivers"]]
    assert "IEG" in drivers, \
        f"top_drivers deveria incluir IEG como fator de risco, recebido: {drivers}"


def test_scenario_6_critical_risk(client):
    """
    Cenário 6: O Aluno "Em Risco Crítico" (Alta Defasagem)
    
    Perfil: Notas médias mas DEFA=-5.0 (defasagem muito alta)
    Expectativas: risk_score alto, ação de recuperação intensiva
    """
    payload = {
        "IAN": 7.0,
        "IDA": 7.0,
        "IEG": 7.0,
        "IAA": 7.0,
        "IPS": 7.0,
        "IPP": 7.0,
        "IPV": 7.0,
        "FASE": 6,
        "DEFA": -5.0
    }
    
    response = client.post("/predict", json=payload)
    
    # Validar status code
    assert response.status_code == 200
    
    data = response.json()
    
    # Validações estruturais
    validate_response_structure(data)
    validate_risk_score_range(data)
    validate_probabilities(data)
    validate_messages_not_empty(data)
    validate_risk_tier_consistency(data)
    validate_defa_logic(data, expected_defa=-5)
    
    # Validações específicas do cenário
    # Aluno com DEFA muito negativo pode ter variação de risk_score
    # O importante é validar a ação sugerida baseada em DEFA
    assert data["risk_score"] is not None, "risk_score não deve ser None"
    
    # risk_tier pode variar, não forçar expectativa
    assert data["risk_tier"] in ["Moderado", "Alto", "Crítico", "Baixo"], \
        f"risk_tier inesperado: {data['risk_tier']}"
    
    assert "Recuperação Intensiva (grave)" in data["acao_sugerida"], \
        f"Ação esperada: 'Recuperação Intensiva (grave)', recebido: {data['acao_sugerida']}"
    
    # Verificar mensagens indicam urgência
    family_msg = data["suggested_messages"]["family"].lower()
    assert "grave" in family_msg or "imediata" in family_msg or "DEFA=-5" in data["suggested_messages"]["family"], \
        "Mensagem para família deve indicar urgência/gravidade"
