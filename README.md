# Datathon — Esqueleto de Repositório

Este repositório é um esqueleto inicial para o seu projeto Datathon. Contém:
- Estrutura de código (src/, app/)
- Templates de issues, PR, CONTRIBUTING e Code of Conduct
- Exemplo mínimo de API (FastAPI)
- Makefile, Dockerfile e testes básicos

## Como usar
1. Clone este repositório.
2. Crie e ative um virtualenv:
   ```
   python -m venv .venv
   source .venv/bin/activate   # Linux/Mac
   .venv\Scripts\activate    # Windows PowerShell
   ```
3. Instale dependências:
   ```
   pip install -r requirements.txt
   ```
4. Rode testes:
   ```
   make test
   ```
5. Rode a API (desenvolvimento):
   ```
   uvicorn app.main:app --reload
   ```

## Estrutura sugerida
- `app/` — API FastAPI mínima
- `src/` — módulos de preprocessamento, treino e avaliação
- `notebooks/` — EDA e experimentos
- `tests/` — testes unitários
- `.github/` — templates de issue/PR/contributing
