# Student Performance API (Datathon)

API REST para predição de desempenho estudantil (Pedra Conceito) utilizando modelo XGBoost, com análise profunda, trajetória histórica e simulação contrafactual.

## Descrição

Este projeto fornece uma interface para:
1.  Consultar dados históricos de alunos.
2.  Prever a "Pedra Conceito" (classificação de desempenho) com base em métricas acadêmicas (IAN, IDA, IEG, IAA, IPS, IPP, IPV).
3.  Analisar trajetória interanual (tendência do INDE) e cruzamento IPV × IDA.
4.  Gerar diagnósticos pedagógicos automatizados (acadêmico, engajamento, psicossocial).
5.  Simular cenários contrafactuais ("E se o aluno melhorar o IEG em 1 ponto?").

O modelo foi treinado com dados históricos e utiliza XGBoost para classificação.

## Como Executar

### Pré-requisitos
- Python 3.10+ (Recomendado 3.13)
- Docker (Opcional)

### Instalação Local

1.  Clone o repositório.
2.  Crie e ative o ambiente virtual:
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```
3.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

### Executando a API

Para iniciar o servidor de desenvolvimento:
```bash
uvicorn app.main:app --reload
# Ou via Makefile (se disponível make)
make run
```
A API estará disponível em `http://localhost:8000`.
Documentação interativa (Swagger UI): `http://localhost:8000/docs`

### Executando com Docker

1.  Construa a imagem:
    ```bash
    docker build -t student-api .
    ```
2.  Execute o container:
    ```bash
    docker run -p 8080:8080 student-api
    ```
    Acesse em `http://localhost:8080/docs`.

## Endpoints

### `GET /health`
Verifica o status da API e se o modelo e dados foram carregados corretamente.

### `GET /students/{name}`
Busca alunos pelo nome (parcial, case-insensitive).
- **Parâmetros**: `name` (str)
- **Retorno**: Lista de alunos encontrados com todas as colunas disponíveis.

### `POST /predict`
Realiza a predição da Pedra Conceito com análise de risco e sugestões de ação.
- **Body**:
    ```json
    {
      "IAN": 5.0, "IDA": 7.0, "IEG": 8.0,
      "IAA": 6.5, "IPS": 7.5, "IPP": 6.0,
      "IPV": 8.0, "FASE": 1, "DEFA": 0.0
    }
    ```
- **Retorno**:
    ```json
    {
      "prediction": "Topázio",
      "probabilities": { "Quartzo": 0.05, "Ágata": 0.10, "Ametista": 0.15, "Topázio": 0.70 },
      "risk_score": 0.003,
      "risk_tier": "Baixo",
      "acao_sugerida": "Monitoramento e Micro-intervenção",
      "suggested_messages": {
        "family": "Acompanhamento de rotina; entraremos em contato se houver piora.",
        "professor": "Monitorar evolução e aplicar micro-intervenção se necessário."
      }
    }
    ```

### `GET /students/{name}/analysis`
Análise profunda do aluno: histórico completo, trajetória, cruzamento IPV × IDA e diagnósticos automatizados.
- **Retorno**: Diagnósticos com gravidade (grave/moderado/leve), intervenções sugeridas e resumo geral.

### `GET /students/{name}/trajectory`
Trajetória interanual do INDE com tendência calculada via regressão linear.
- **Retorno**: Anos, valores INDE, deltas, tendência (ascendente/estável/descendente) e inclinação.

### `GET /students/{name}/ipv-ida`
Cruzamento IPV × IDA para identificar o tipo de queda (técnica, maturidade, combinada ou nenhuma).

### `POST /simulate`
Simulação contrafactual: testa cenários "e se?" para um aluno.
- **Body**:
    ```json
    {
      "NOME": "Aluno-1",
      "changes": { "IEG": 8.0, "IDA": 7.5 }
    }
    ```
- **Retorno**: Comparação original vs. simulado com delta de risco e impacto.

## Interface Web (Dashboard)

O projeto inclui um **Painel Pedagógico** com dark theme, acessível em `http://localhost:8000`:

1. **Buscar Aluno** — Busca por nome, exibe histórico em tabela clicável por ano
2. **Perfil do Aluno** — 3 abas:
   - 📋 **Histórico** — Tabela com indicadores por ano
   - 📈 **Trajetória** — Gráfico INDE (canvas) + cruzamento IPV × IDA
   - 🩺 **Diagnóstico** — Cards de severidade com intervenções recomendadas
3. **Nova Avaliação** — Sliders preenchidos automaticamente + botão de simulação
4. **Resultado** — Badge colorido por categoria, risco, mensagens para família/professor, probabilidades

## Estrutura do Projeto

```
ProjetoFIAP/
├── app/                          # 📦 Código fonte da API
│   ├── routes/                   # Endpoints da API
│   │   ├── health.py            # GET /health
│   │   ├── students.py          # GET /students/{name}
│   │   ├── predictions.py       # POST /predict
│   │   └── analysis.py          # Análise, trajetória, IPV×IDA, simulação
│   ├── services/                 # Lógica de negócio (SRP)
│   │   ├── model_service.py     # Carregamento do modelo e dados
│   │   ├── student_service.py   # Busca e consulta de alunos
│   │   ├── prediction_service.py # Core ML: features, predição, risco
│   │   ├── suggestion_service.py # Recomendações pedagógicas
│   │   ├── simulation_service.py # Simulação contrafactual
│   │   ├── history_service.py   # Trajetória INDE e cruzamento IPV×IDA
│   │   └── diagnostic_service.py # Diagnóstico pedagógico automatizado
│   ├── static/                   # Dashboard web (dark theme)
│   │   ├── index.html           # Painel pedagógico (3 passos)
│   │   ├── styles.css           # Dark glassmorphism design system
│   │   └── script.js            # APIs integradas + gráfico canvas
│   ├── utils/                    # Funções auxiliares e helpers
│   ├── config.py                # Configurações e thresholds
│   ├── main.py                  # Ponto de entrada FastAPI
│   └── models.py                # Modelos Pydantic
│
├── data/                         # 📊 Dados do projeto
│   ├── df_Base_final.csv        # Base de dados processada
│   ├── BASE DE DADOS PEDE 2024 - DATATHON.xlsx
│   └── lista_intervencao_preventiva_2025.csv
│
├── models/                       # 🤖 Modelo XGBoost treinado
│   └── modelo_pedra_conceito_xgb_2025.pkl
│
├── notebooks/                    # 📓 Jupyter Notebooks (EDA, modelo)
│   ├── 1 - obtendoDados.ipynb
│   ├── 2 - EDA.ipynb
│   └── 3 - modelo.ipynb
│
├── docs/                         # 📚 Documentação
│   ├── dicionarioDados.md
│   └── test_scenarios.md
│
├── tests/                        # 🧪 104 testes automatizados
│   ├── test_api.py              # Integração dos endpoints principais
│   ├── test_scenarios.py        # Cenários de uso específicos
│   ├── test_edge_cases.py       # Edge cases parametrizados
│   ├── test_history.py          # Testes de trajetória e IPV×IDA
│   ├── test_diagnostic.py       # Testes de diagnóstico pedagógico
│   └── test_analysis_api.py     # Integração dos endpoints de análise
│
├── requirements.txt
├── Dockerfile
├── Makefile
├── conftest.py
└── README.md
```

### Arquitetura de Serviços

```
ModelService ─────────────────────────────────┐
  │                                           │
  ├── StudentService                          │
  ├── SuggestionService                       │
  │     └── PredictionService(model, suggestions)
  │           └── SimulationService(model, prediction)
  ├── HistoryService(model)                   │
  │     └── DiagnosticService(model, history) │
  └───────────────────────────────────────────┘
```

Todos os serviços seguem o **Princípio de Responsabilidade Única (SRP)** e são conectados por injeção de dependência no startup da aplicação (`main.py`).

## Testes

### Executar Testes

```bash
# Todos os testes
pytest tests/ -v

# Com coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Apenas edge cases
pytest tests/test_edge_cases.py -v

# Testes em paralelo (mais rápido)
pytest tests/ -n auto

# Com timeout de 30s por teste
pytest tests/ --timeout=30
```

### Cobertura de Testes

Os testes cobrem:
- ✅ **104 testes** (100% passing)
- ✅ Validação de entrada e edge cases
- ✅ Thresholds de DEFA (-3, -2, +2, +3)
- ✅ Valores extremos (min/max)
- ✅ Consistência de resposta
- ✅ Trajetória e cruzamento IPV × IDA
- ✅ Diagnóstico pedagógico (acadêmico, engajamento, psicossocial)
- ✅ Simulação contrafactual
- ✅ Integração de todos os endpoints (incluindo novos)
- ✅ Regressão (endpoints antigos continuam funcionando)

```bash
# Gerar relatório HTML de coverage
pytest tests/ --cov=app --cov-report=html
# Ver em: htmlcov/index.html
```

## CI/CD Pipeline

O projeto possui pipeline completo de CI/CD com GitHub Actions:

### Workflows Disponíveis

#### 🧪 CI - Tests, Lint & Security (`ci.yml`)
Executa em cada push e pull request:
- ✅ Testes em Python 3.10, 3.11, 3.12
- ✅ Coverage reporting (Codecov)
- ✅ Linting (black, isort, flake8)
- ✅ Security scanning (safety, bandit)

#### 🚀 CD - Build & Deploy (`cd.yml`)
Executa em tags e branch main:
- 🐳 Build de imagem Docker
- 📦 Push para GitHub Container Registry
- 🚢 Deploy automatizado (configurável)

#### 📊 Test Report (`test-report.yml`)
Comenta em PRs com:
- 📈 Resultados dos testes
- 🎯 Badges de coverage
- 📋 Logs detalhados

### Configuração do Pipeline

Para ativar o pipeline:
1. Push do código para GitHub
2. Os workflows serão executados automaticamente
3. Verificar status na aba "Actions"

## Tecnologias Utilizadas

- **Backend**: FastAPI, Uvicorn
- **Machine Learning**: XGBoost, Scikit-learn, SHAP
- **Data Processing**: Pandas, NumPy
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Canvas API
- **Testing**: Pytest, pytest-cov, pytest-xdist, HTTPX
- **CI/CD**: GitHub Actions, Docker
- **Code Quality**: Black, isort, flake8
- **Security**: Safety, Bandit
- **Containerization**: Docker

## Quick Start

```bash
# 1. Clonar repositório
git clone <repository-url>
cd ProjetoFIAP

# 2. Criar ambiente virtual
python -m venv .venv
.\.venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar API
uvicorn app.main:app --reload

# 5. Executar testes
pytest tests/ -v --cov=app

# 6. Acessar
# Dashboard: http://localhost:8000
# Swagger:   http://localhost:8000/docs
```
