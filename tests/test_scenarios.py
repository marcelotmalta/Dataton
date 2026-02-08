import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Fixture para criar cliente de teste da API"""
    with TestClient(app) as c:
        yield c


# Cenários de teste baseados em docs/test_scenarios.md
test_data = [
    (
        "Cenário 1: O Aluno 'Excelente'",
        {
            "IAN": 9.5, "IDA": 9.0, "IEG": 9.5, "IAA": 9.0, "IPS": 8.5,
            "IPP": 8.0, "IPV": 9.0, "FASE": 2, "DEFA": 1.0
        },
        {
            "expected_risk_tier": ["Baixo", "Médio"],
            "expected_action": "Enriquecimento Curricular (moderado)",
            "expected_defa_int": 1,
            "max_risk_score": 0.5,
            "description": "Aluno adiantado com alto desempenho"
        }
    ),
    (
        "Cenário 2: O Aluno 'Médio'",
        {
            "IAN": 6.0, "IDA": 6.5, "IEG": 7.0, "IAA": 6.0, "IPS": 7.0,
            "IPP": 6.0, "IPV": 6.0, "FASE": 3, "DEFA": 0.0
        },
        {
            "expected_risk_tier": ["Médio", "Alto"],
            "expected_action_contains": ["Monitoramento", "Acompanhamento"],
            "expected_defa_int": 0,
            "min_risk_score": 0.2,
            "max_risk_score": 0.7,
            "description": "Aluno com desempenho mediano"
        }
    ),
    (
        "Cenário 3: O Aluno 'Com Dificuldades'",
        {
            "IAN": 3.0, "IDA": 4.0, "IEG": 3.0, "IAA": 4.0, "IPS": 4.0,
            "IPP": 3.0, "IPV": 2.0, "FASE": 1, "DEFA": -2.0
        },
        {
            "expected_risk_tier": ["Alto", "Crítico"],
            "expected_action": "Recuperação de Aprendizagem",
            "expected_defa_int": -2,
            "min_risk_score": 0.5,
            "description": "Aluno com defasagem e baixo desempenho"
        }
    ),
    (
        "Cenário 4: O Aluno 'Em Recuperação'",
        {
            "IAN": 5.0, "IDA": 5.0, "IEG": 8.5, "IAA": 7.0, "IPS": 6.0,
            "IPP": 5.0, "IPV": 9.0, "FASE": 4, "DEFA": 0.0
        },
        {
            "expected_risk_tier": ["Baixo", "Médio"],
            "expected_action_contains": ["Monitoramento", "Manutenção"],
            "expected_defa_int": 0,
            "max_risk_score": 0.6,
            "description": "Aluno com alto engajamento e ponto de virada"
        }
    ),
    (
        "Cenário 5: O Aluno 'Em Declínio'",
        {
            "IAN": 8.0, "IDA": 8.0, "IEG": 3.0, "IAA": 5.0, "IPS": 5.0,
            "IPP": 5.0, "IPV": 2.0, "FASE": 5, "DEFA": 0.0
        },
        {
            "expected_risk_tier": ["Médio", "Alto"],
            "expected_action_contains": ["Acompanhamento", "Monitoramento"],
            "expected_defa_int": 0,
            "min_risk_score": 0.3,
            "description": "Aluno com bom histórico mas baixo engajamento"
        }
    ),
    (
        "Cenário 6: O Aluno 'Em Risco Crítico'",
        {
            "IAN": 7.0, "IDA": 7.0, "IEG": 7.0, "IAA": 7.0, "IPS": 7.0,
            "IPP": 7.0, "IPV": 7.0, "FASE": 6, "DEFA": -5.0
        },
        {
            "expected_risk_tier": ["Alto", "Crítico"],
            "expected_action": "Recuperação Intensiva (grave)",
            "expected_defa_int": -5,
            "min_risk_score": 0.5,
            "description": "Aluno com defasagem grave"
        }
    ),
]


@pytest.mark.parametrize("scenario_name, payload, expectations", test_data)
def test_predict_scenarios(client, scenario_name, payload, expectations):
    """
    Testa cenários de predição validando todos os campos da resposta da API.
    
    Validações incluem:
    - Estrutura da resposta
    - Tipos de dados
    - Ranges de valores
    - Lógica de ações sugeridas
    - Mensagens contextualizadas
    """
    print(f"\n\n{'='*80}")
    print(f"Executando: {scenario_name}")
    print(f"Descrição: {expectations['description']}")
    print(f"Payload: {payload}")
    print(f"{'='*80}")
    
    # Fazer requisição
    response = client.post("/predict", json=payload)
    
    # Validação 1: Status code
    assert response.status_code == 200, f"API falhou: {response.text}"
    
    data = response.json()
    
    # Validação 2: Estrutura da resposta - campos obrigatórios
    required_fields = [
        "prediction", "prediction_index", "probabilities", 
        "risk_score", "risk_tier", "acao_sugerida",
        "suggested_messages", "defa_int", "input_features"
    ]
    
    for field in required_fields:
        assert field in data, f"Campo obrigatório '{field}' ausente na resposta"
    
    # Validação 3: Tipos de dados
    assert isinstance(data["prediction"], str), "prediction deve ser string"
    assert isinstance(data["prediction_index"], (int, type(None))), "prediction_index deve ser int ou None"
    assert isinstance(data["probabilities"], dict), "probabilities deve ser dict"
    assert isinstance(data["risk_score"], (float, type(None))), "risk_score deve ser float ou None"
    assert isinstance(data["risk_tier"], (str, type(None))), "risk_tier deve ser string ou None"
    assert isinstance(data["acao_sugerida"], str), "acao_sugerida deve ser string"
    assert isinstance(data["suggested_messages"], dict), "suggested_messages deve ser dict"
    assert isinstance(data["defa_int"], int), "defa_int deve ser int"
    
    # Validação 4: Mensagens para família e professor
    assert "family" in data["suggested_messages"], "Mensagem para família ausente"
    assert "professor" in data["suggested_messages"], "Mensagem para professor ausente"
    assert len(data["suggested_messages"]["family"]) > 0, "Mensagem para família vazia"
    assert len(data["suggested_messages"]["professor"]) > 0, "Mensagem para professor vazia"
    
    # Validação 5: Ranges de valores
    if data["risk_score"] is not None:
        assert 0.0 <= data["risk_score"] <= 1.0, \
            f"risk_score fora do range [0,1]: {data['risk_score']}"
    
    if data["prediction_index"] is not None:
        assert data["prediction_index"] >= 0, \
            f"prediction_index deve ser >= 0: {data['prediction_index']}"
    
    # Validação 6: Probabilidades
    assert len(data["probabilities"]) > 0, "probabilities não pode estar vazio"
    
    prob_sum = sum(data["probabilities"].values())
    assert 0.99 <= prob_sum <= 1.01, \
        f"Soma das probabilidades deve ser ~1.0, obtido: {prob_sum}"
    
    for class_name, prob in data["probabilities"].items():
        assert 0.0 <= prob <= 1.0, \
            f"Probabilidade de '{class_name}' fora do range [0,1]: {prob}"
    
    # Validação 7: DEFA integer
    assert data["defa_int"] == expectations["expected_defa_int"], \
        f"defa_int esperado: {expectations['expected_defa_int']}, obtido: {data['defa_int']}"
    
    # Validação 8: Risk tier esperado
    if "expected_risk_tier" in expectations and data["risk_tier"] is not None:
        assert data["risk_tier"] in expectations["expected_risk_tier"], \
            f"risk_tier esperado: {expectations['expected_risk_tier']}, obtido: {data['risk_tier']}"
    
    # Validação 9: Ação sugerida
    if "expected_action" in expectations:
        assert data["acao_sugerida"] == expectations["expected_action"], \
            f"acao_sugerida esperada: {expectations['expected_action']}, obtida: {data['acao_sugerida']}"
    elif "expected_action_contains" in expectations:
        action_matched = any(
            keyword.lower() in data["acao_sugerida"].lower() 
            for keyword in expectations["expected_action_contains"]
        )
        assert action_matched, \
            f"acao_sugerida deve conter um de {expectations['expected_action_contains']}, obtida: {data['acao_sugerida']}"
    
    # Validação 10: Risk score ranges específicos
    if "min_risk_score" in expectations and data["risk_score"] is not None:
        assert data["risk_score"] >= expectations["min_risk_score"], \
            f"risk_score deve ser >= {expectations['min_risk_score']}, obtido: {data['risk_score']}"
    
    if "max_risk_score" in expectations and data["risk_score"] is not None:
        assert data["risk_score"] <= expectations["max_risk_score"], \
            f"risk_score deve ser <= {expectations['max_risk_score']}, obtido: {data['risk_score']}"
    
    # Validação 11: Consistência entre risk_score e risk_tier
    if data["risk_score"] is not None and data["risk_tier"] is not None:
        if data["risk_score"] >= 0.75:
            assert data["risk_tier"] == "Crítico", \
                f"risk_score >= 0.75 deve resultar em tier 'Crítico', obtido: {data['risk_tier']}"
        elif data["risk_score"] >= 0.5:
            assert data["risk_tier"] in ["Alto", "Crítico"], \
                f"risk_score >= 0.5 deve resultar em tier 'Alto' ou 'Crítico', obtido: {data['risk_tier']}"
    
    # Validação 12: Lógica de DEFA
    defa_int = data["defa_int"]
    action = data["acao_sugerida"]
    
    if defa_int < 0:
        # Defasagem: deve ter ação de recuperação
        assert "Recuperação" in action or "Intervenção" in action, \
            f"DEFA negativo ({defa_int}) deve resultar em ação de recuperação, obtida: {action}"
        
        if defa_int <= -3:
            assert "grave" in action.lower() or "intensiva" in action.lower(), \
                f"DEFA <= -3 deve indicar gravidade/intensidade, obtida: {action}"
    
    elif defa_int > 0:
        # Adiantado: deve ter ação de enriquecimento
        assert "Enriquecimento" in action or "Aprofundamento" in action, \
            f"DEFA positivo ({defa_int}) deve resultar em ação de enriquecimento, obtida: {action}"
    
    # Imprimir resultados para verificação manual
    print(f"\n✓ RESULTADOS:")
    print(f"  Predição: {data['prediction']} (índice: {data['prediction_index']})")
    print(f"  Risk Score: {data['risk_score']}")
    print(f"  Risk Tier: {data['risk_tier']}")
    print(f"  Ação Sugerida: {data['acao_sugerida']}")
    print(f"  DEFA Int: {data['defa_int']}")
    print(f"\n  Probabilidades:")
    for class_name, prob in sorted(data["probabilities"].items(), key=lambda x: x[1], reverse=True):
        print(f"    {class_name}: {prob:.4f}")
    print(f"\n  Mensagem Família: {data['suggested_messages']['family'][:100]}...")
    print(f"  Mensagem Professor: {data['suggested_messages']['professor'][:100]}...")
    
    if "top_drivers" in data and data["top_drivers"]:
        print(f"\n  Top Drivers: {data['top_drivers'][:3]}")
    
    print(f"\n✓ Todas as validações passaram!")


def test_api_response_structure(client):
    """
    Teste genérico para validar estrutura básica da resposta da API
    """
    payload = {
        "IAN": 7.0, "IDA": 7.0, "IEG": 7.0, "IAA": 7.0, "IPS": 7.0,
        "IPP": 7.0, "IPV": 7.0, "FASE": 3, "DEFA": 0.0
    }
    
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # Validar que todos os campos esperados estão presentes
    expected_keys = {
        "prediction", "prediction_index", "probabilities", 
        "risk_score", "risk_tier", "acao_sugerida",
        "suggested_messages", "top_drivers", "input_features",
        "defa_int", "model_version"
    }
    
    actual_keys = set(data.keys())
    missing_keys = expected_keys - actual_keys
    
    assert len(missing_keys) == 0, f"Campos ausentes na resposta: {missing_keys}"
    
    print(f"\n✓ Estrutura da resposta validada com sucesso!")
    print(f"  Campos presentes: {sorted(actual_keys)}")


def test_defa_logic_negative(client):
    """
    Testa lógica específica para DEFA negativo (defasagem)
    """
    test_cases = [
        (-1.0, "Recuperação de Aprendizagem"),
        (-2.5, "Recuperação de Aprendizagem"),
        (-3.0, "Recuperação Intensiva (grave)"),
        (-5.0, "Recuperação Intensiva (grave)"),
    ]
    
    for defa_value, expected_action in test_cases:
        payload = {
            "IAN": 6.0, "IDA": 6.0, "IEG": 6.0, "IAA": 6.0, "IPS": 6.0,
            "IPP": 6.0, "IPV": 6.0, "FASE": 3, "DEFA": defa_value
        }
        
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["acao_sugerida"] == expected_action, \
            f"DEFA={defa_value}: esperado '{expected_action}', obtido '{data['acao_sugerida']}'"
        
        print(f"✓ DEFA={defa_value}: {data['acao_sugerida']}")


def test_defa_logic_positive(client):
    """
    Testa lógica específica para DEFA positivo (adiantado)
    """
    test_cases = [
        (1.0, "Enriquecimento Curricular (moderado)"),
        (2.5, "Enriquecimento Curricular (moderado)"),
        (3.0, "Aprofundamento / Enriquecimento (alto)"),
        (5.0, "Aprofundamento / Enriquecimento (alto)"),
    ]
    
    for defa_value, expected_action in test_cases:
        payload = {
            "IAN": 7.0, "IDA": 7.0, "IEG": 7.0, "IAA": 7.0, "IPS": 7.0,
            "IPP": 7.0, "IPV": 7.0, "FASE": 3, "DEFA": defa_value
        }
        
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["acao_sugerida"] == expected_action, \
            f"DEFA={defa_value}: esperado '{expected_action}', obtido '{data['acao_sugerida']}'"
        
        print(f"✓ DEFA={defa_value}: {data['acao_sugerida']}")
