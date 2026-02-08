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
Realiza a predição da Pedra Conceito.
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
      "probabilities": { ... },
      "input_features": { ... }
    }
    ```

## Estrutura do Projeto

- `app/`: Código fonte da API (`main.py`).
- `data/`: Arquivos de dados (`df_Base_final.csv`).
- `models/`: Modelos treinados (`.pkl`).
- `tests/`: Testes automatizados.
