# Student Performance API (Datathon)

API REST para predição de desempenho estudantil com classificação por "Pedras" e score de risco crítico.

## Descrição

Este projeto fornece uma interface interativa para:
1.  **Consultar dados históricos** de alunos com **gráficos de evolução** (Chart.js) mostrando a trajetória dos indicadores ao longo dos anos.
2.  **Predizer a "Pedra Conceito"** (classificação de desempenho) com base em métricas acadêmicas (IAN, IDA, IEG, IAA, IPS, IPP, IPV).
3.  **Estimar score de risco** para priorização de intervenção na fronteira Ágata/Quartzo.
4.  **Gerar recomendações personalizadas** com ações sugeridas para a família e para a escola.
5.  **Visualizar a nova avaliação no gráfico histórico**, adicionando um ponto ao gráfico de evolução ao realizar uma previsão.

A interface web utiliza **dark mode com glassmorphism**, animações e tipografia moderna (Inter). Os modelos são treinados no notebook `notebooks/3 - modelo.ipynb` e exportados em artefatos `joblib` na pasta `models/`.

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

Opcionalmente, selecione os artefatos via variáveis de ambiente:
```bash
MODEL_MULTICLASS_JOBLIB_PATH=models/modelo_multiclasse_pedras_2025.pkl \
MODEL_RISK_JOBLIB_PATH=models/modelo_risco_critico_2025.pkl \
uvicorn app.main:app --reload
```

Compatibilidade: `MODEL_JOBLIB_PATH` continua aceito como caminho legado do modelo principal.

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

### Executando com Docker Compose

Para facilitar o desenvolvimento e a execução dos serviços (aplicação e MLflow), você pode usar o Docker Compose.

1.  **Subir os serviços:**
    Este comando irá construir as imagens (se necessário) e iniciar os containers da aplicação e do MLflow em modo detached.

    ```bash
    make compose-up
    ```

2.  **Acessar os serviços:**
    - **API**: `http://localhost:8000`
    - **Documentação da API (Swagger UI)**: `http://localhost:8000/docs`
    - **MLflow UI**: `http://localhost:5000`

3.  **Parar os serviços:**
    Este comando irá parar e remover os containers.

    ```bash
    make compose-down
    ```

## Endpoints

### `GET /health`
Verifica o status da API e se o modelo e dados foram carregados corretamente.

### `GET /students/{name}`
Busca alunos pelo nome (parcial, case-insensitive).
- **Parâmetros**: `name` (str)
- **Retorno**: Objeto com `nome` e `historico` (lista de registros por ano, ordenados cronologicamente para renderização de gráficos).

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
      "DEFA": 0.0,
      "NOME": "Ana Silva"
    }
    ```
    > **Nota**: Quando `NOME` é fornecido, a resposta inclui o campo `historico` com os registros históricos do aluno, permitindo renderizar o gráfico de evolução no frontend.
- **Retorno** (exemplo):
    ```json
    {
      "prediction": "Ágata",
      "probabilities": {
        "Quartzo": 0.002,
        "Ágata": 0.972,
        "Ametista": 0.022,
        "Topázio": 0.004
      },
      "risk_score": 0.003,
      "risk_tier": "Baixo",
      "acao_sugerida": "Monitoramento e Micro-intervenção",
      "suggested_messages": {
        "family": "Acompanhamento de rotina; entraremos em contato se houver piora.",
        "professor": "Monitorar evolução e aplicar micro-intervenção se necessário."
      },
      "historico": [
        { "ANO": 2023, "FASE": 1, "IAN": 5.0, "IDA": 4.0, ... },
        { "ANO": 2024, "FASE": 2, "IAN": 6.0, "IDA": 5.0, ... }
      ],
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
│   ├── modelo_multiclasse_pedras_2025.pkl       # Modelo vencedor multiclasse (Pedras)
│   └── modelo_risco_critico_2025.pkl            # Modelo vencedor binário (Risco Crítico)
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
│   ├── test_api.py              # Testes de integração dos endpoints
│   ├── test_scenarios.py        # Testes de cenários específicos
│   ├── test_edge_cases.py       # Testes paramétricos de edge cases
│   ├── test_prediction_service.py # Testes unitários do serviço de predição
│   ├── test_model_service.py    # Testes unitários do serviço de modelo
│   ├── test_student_service.py  # Testes unitários do serviço de alunos
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

- **`static/`**: Interface web do usuário (dark mode, glassmorphism)
  - `index.html`: Página HTML principal com gráficos Chart.js e cards de resultado
  - `styles.css`: Design system completo (dark mode, glassmorphism, animações, responsivo)
  - `script.js`: Lógica do frontend com gráficos de evolução, chips de histórico e resultados animados

- **`utils/`**: Funções auxiliares reutilizáveis
  - `helpers.py`: Funções para sanitização, cálculo de risco, etc.

#### 📊 `data/` - Dados
Armazena os datasets utilizados pelo projeto.

- `df_Base_final.csv`: Base de dados processada e limpa
- `BASE DE DADOS PEDE 2024 - DATATHON.xlsx`: Dados originais do PEDE
- `lista_intervencao_preventiva_2025.csv`: Lista de alunos para intervenção

#### 🤖 `models/` - Modelos Treinados
Contém os modelos de Machine Learning serializados.

- `modelo_multiclasse_pedras_2025.pkl`: Modelo vencedor multiclasse para `Pedra_Conceito`
- `modelo_risco_critico_2025.pkl`: Modelo vencedor binário para `Risco_Critico`

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
- `test_prediction_service.py`: Testes unitários do serviço de predição (49 testes)
- `test_model_service.py`: Testes unitários do serviço de modelo (25 testes)
- `test_student_service.py`: Testes unitários do serviço de alunos (10 testes)

**Total: 164 testes automatizados · Cobertura: 94.29%**

## Testes

### Executar Testes

```bash
# Todos os testes
pytest tests/ -v

# Com coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Apenas testes unitários
pytest tests/test_prediction_service.py tests/test_model_service.py tests/test_student_service.py -v

# Apenas edge cases
pytest tests/test_edge_cases.py -v

# Testes em paralelo (mais rápido)
pytest tests/ -n auto

# Com timeout de 30s por teste
pytest tests/ --timeout=30
```

### Cobertura de Testes

Os testes cobrem:
- ✅ **164 testes** (100% passing)
- ✅ **94.29% de cobertura total**
- ✅ Validação de entrada e edge cases
- ✅ Thresholds de DEFA (-3, -2, +2, +3)
- ✅ Valores extremos (min/max)
- ✅ Cálculo de risco (binário, fallback, média ponderada)
- ✅ Geração de sugestões (todas as combinações DEFA/risco)
- ✅ Predição com fallback de imputer/scaler
- ✅ Carregamento de modelos e bundles
- ✅ Busca de alunos e histórico
- ✅ Integração de endpoints

| Módulo                  | Cobertura |
| ----------------------- | --------- |
| `student_service.py`    | 100%      |
| `model_service.py`      | 96.7%     |
| `prediction_service.py` | 92.8%     |
| `helpers.py`            | 90.2%     |
| `main.py`               | 87.9%     |
| Routes / Models         | 100%      |

```bash
# Gerar relatório HTML de coverage
pytest tests/ --cov=app --cov-report=html
# Ver em: htmlcov/index.html
```

## MLflow Experiment Tracking

Este projeto utiliza [MLflow](https://mlflow.org/) para rastrear experimentos, registrar modelos e visualizar resultados. A forma mais simples de iniciar o ambiente é usando Docker Compose.

### Como Usar com Docker Compose

1.  **Inicie os serviços:**
    Execute o comando abaixo para iniciar a aplicação e o servidor MLflow.

    ```bash
    make compose-up
    ```

2.  **Acesse a MLflow UI:**
    Abra seu navegador e acesse `http://localhost:5000`. Você verá a interface do MLflow, onde todos os experimentos e execuções serão registrados.

3.  **Execute o Notebook de Treinamento:**
    Com os serviços em execução, execute o notebook `notebooks/3 - modelo.ipynb`. Ele está configurado para se conectar automaticamente ao servidor MLflow iniciado pelo Docker Compose e registrará os experimentos, modelos, parâmetros e métricas.

4.  **Visualize os Resultados:**
    Após a execução do notebook, volte para a MLflow UI para comparar as execuções, visualizar os artefatos do modelo e ver qual modelo foi registrado como a melhor versão.

### Carregando Modelos do MLflow
O notebook também demonstra como carregar a versão mais recente de um modelo registrado:
```python
# Exemplo para carregar o modelo binário
modelo_carregado = mlflow.sklearn.load_model("models:/modelo_vencedor_binario/latest")
```

Isto garante que a aplicação ou outros notebooks possam sempre usar a melhor versão do modelo de forma programática.

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
- **Machine Learning**: Scikit-learn (Regressão Logística), SHAP
- **Data Processing**: Pandas, NumPy
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Chart.js
- **Design**: Dark mode, Glassmorphism, Google Fonts (Inter)
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
