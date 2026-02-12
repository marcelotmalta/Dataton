# Student Performance API (Datathon)

API REST para predição de desempenho estudantil (Pedra Conceito) utilizando modelo XGBoost.

## Descrição

Este projeto fornece uma interface para:
1.  Consultar dados históricos de alunos.
2.  Prever a "Pedra Conceito" (classificação de desempenho) com base em métricas acadêmicas (IAN, IDA, IEG, IAA, IPS, IPP, IPV).

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
      "IAN": 5.0,
      "IDA": 7.0,
      "IEG": 8.0,
      "IAA": 6.5,
      "IPS": 7.5,
      "IPP": 6.0,
      "IPV": 8.0,
      "FASE": 1,
      "DEFA": 0.0
    }
    ```
- **Retorno**:
    ```json
    {
      "prediction": "Pedra A",
      "probabilities": {
        "Pedra A": 0.85,
        "Pedra B": 0.10,
        "Pedra C": 0.05
      },
      "risk_score": 0.003,
      "risk_tier": "Baixo",
      "acao_sugerida": "Monitoramento e Micro-intervenção",
      "suggested_messages": {
        "family": "Acompanhamento de rotina; entraremos em contato se houver piora.",
        "professor": "Monitorar evolução e aplicar micro-intervenção se necessário."
      },
      "input_features": { ... }
    }
    ```

## Estrutura do Projeto

```
Dataton-1/
├── app/                          # 📦 Código fonte da API
│   ├── routes/                   # Endpoints da API (health, students, predictions)
│   ├── services/                 # Lógica de negócio (model, student, prediction services)
│   ├── static/                   # Arquivos estáticos (HTML, CSS, JS)
│   │   ├── index.html           # Interface web principal
│   │   ├── styles.css           # Estilos da aplicação
│   │   └── script.js            # Lógica JavaScript do frontend
│   ├── utils/                    # Funções auxiliares e helpers
│   ├── config.py                # Configurações centralizadas
│   ├── main.py                  # Ponto de entrada da aplicação FastAPI
│   └── models.py                # Modelos Pydantic para validação de dados
│
├── data/                         # 📊 Dados do projeto
│   ├── df_Base_final.csv        # Base de dados processada para o modelo
│   ├── BASE DE DADOS PEDE 2024 - DATATHON.xlsx  # Dados originais
│   └── lista_intervencao_preventiva_2025.csv    # Lista de intervenções
│
├── models/                       # 🤖 Modelos de Machine Learning
│   └── modelo_pedra_conceito_xgb_2025.pkl       # Modelo XGBoost treinado
│
├── notebooks/                    # 📓 Jupyter Notebooks para análise
│   ├── 1 - obtendoDados.ipynb   # Extração e preparação dos dados
│   ├── 2 - EDA.ipynb            # Análise exploratória de dados
│   ├── 3 - modelo.ipynb         # Treinamento e avaliação do modelo
│   └── README.md                # Documentação dos notebooks
│
├── docs/                         # 📚 Documentação do projeto
│   ├── dicionarioDados.md       # Dicionário de dados com descrição das colunas
│   ├── test_scenarios.md        # Cenários de teste documentados
│   ├── docx/                    # Documentos em formato Word
│   └── pdf/                     # Documentos em formato PDF
│
├── tests/                        # 🧪 Testes automatizados
│   ├── test_api.py              # Testes dos endpoints da API
│   ├── test_scenarios.py        # Testes de cenários específicos
│   └── __init__.py              # Inicialização do pacote de testes
│
├── .github/                      # ⚙️ Configurações do GitHub
│   └── workflows/               # GitHub Actions para CI/CD
│
├── requirements.txt              # 📋 Dependências Python do projeto
├── Dockerfile                    # 🐳 Configuração Docker
├── Makefile                      # 🛠️ Comandos úteis para desenvolvimento
├── conftest.py                   # Configuração do Pytest
└── README.md                     # 📖 Este arquivo
```

### Descrição Detalhada das Pastas

#### 📦 `app/` - Aplicação Principal
Contém todo o código fonte da API REST construída com FastAPI.

- **`routes/`**: Define os endpoints HTTP da API
  - `health.py`: Endpoint de verificação de saúde
  - `students.py`: Endpoints para consulta de alunos
  - `predictions.py`: Endpoints para predições do modelo

- **`services/`**: Camada de lógica de negócio
  - `model_service.py`: Gerenciamento e carregamento do modelo ML
  - `student_service.py`: Operações relacionadas a dados de alunos
  - `prediction_service.py`: Lógica de predição e análise de risco

- **`static/`**: Interface web do usuário
  - `index.html`: Página HTML principal (156 linhas)
  - `styles.css`: Estilos CSS organizados (213 linhas)
  - `script.js`: JavaScript com funções documentadas (203 linhas)

- **`utils/`**: Funções auxiliares reutilizáveis
  - `helpers.py`: Funções para sanitização, cálculo de risco, etc.

#### 📊 `data/` - Dados
Armazena os datasets utilizados pelo projeto.

- `df_Base_final.csv`: Base de dados processada e limpa
- `BASE DE DADOS PEDE 2024 - DATATHON.xlsx`: Dados originais do PEDE
- `lista_intervencao_preventiva_2025.csv`: Lista de alunos para intervenção

#### 🤖 `models/` - Modelos Treinados
Contém os modelos de Machine Learning serializados.

- `modelo_pedra_conceito_xgb_2025.pkl`: Modelo XGBoost para classificação

#### 📓 `notebooks/` - Análises
Jupyter Notebooks com todo o processo de desenvolvimento do modelo.

1. **Obtenção de Dados**: Extração e preparação inicial
2. **EDA**: Análise exploratória e visualizações
3. **Modelo**: Treinamento, validação e exportação

#### 📚 `docs/` - Documentação
Documentação técnica e funcional do projeto.

- `dicionarioDados.md`: Descrição detalhada de todas as colunas
- `test_scenarios.md`: Cenários de teste com exemplos

#### 🧪 `tests/` - Testes
Testes automatizados para garantir qualidade do código.

- `test_api.py`: Testes de integração dos endpoints (5 testes)
- `test_scenarios.py`: Testes de casos de uso específicos (6 testes)
- `test_edge_cases.py`: Testes parametrizados de edge cases (57 testes)

**Total: 68 testes automatizados**

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
- ✅ **68 testes** (100% passing)
- ✅ Validação de entrada e edge cases
- ✅ Thresholds de DEFA (-3, -2, +2, +3)
- ✅ Valores extremos (min/max)
- ✅ Consistência de resposta
- ✅ Casos de sucesso e erro
- ✅ Integração de endpoints

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
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
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
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

