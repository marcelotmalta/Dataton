# Notebooks
Coloque aqui os notebooks de EDA e experimentos. Não inclua dados sensíveis.

## EDA_datathon_eda.ipynb

Este notebook contém o esqueleto da Análise Exploratória de Dados (EDA) para o desafio do Datathon 2024.

### Objetivo
Analisar os dados para entender os fatores relacionados à **Defasagem Escolar (`Defas`)** e preparar o terreno para modelagem preditiva.

### Pré-requisitos
Certifique-se de ter as seguintes bibliotecas instaladas no seu ambiente Python:
- `pandas`: Para manipulação de dados.
- `numpy`: Para operações numéricas.
- `matplotlib`: Para visualização de dados.
- `scikit-learn`: Para divisões de treino/teste e métricas (se aplicável).
- `openpyxl`: Necessário para leitura de arquivos `.xlsx` com pandas.

### Instruções de Configuração e Execução

1.  **Localização dos Dados**:
    *   O notebook está configurado para ler o arquivo de dados a partir do caminho relativo: `../data/BASE DE DADOS PEDE 2024 - DATATHON.xlsx`.
    *   Certifique-se de que a pasta `data` exista no diretório raiz do projeto e que o arquivo Excel esteja presente com esse nome.
    *   Se o nome do arquivo for diferente, altere a variável `DATA_PATH` na célula de carregamento de dados.

2.  **Passos da Análise**:
    *   **Carregamento e Verificação**: Leitura do Excel e exibição das primeiras linhas.
    *   **Padronização**: As colunas são renomeadas automaticamente para letras maiúsculas e espaços substituídos por `_` (ex: `Ano ingresso` -> `ANO_INGRESSO`).
    *   **Análise de Missingness**: Identificação de colunas com muitos valores nulos.
    *   **Distribuição do Target**: Análise da variável alvo `DEFAS`.

3.  **Dica**:
    *   Caso encontre erros de leitura, verifique se o caminho do arquivo está correto em relação à pasta onde o notebook está sendo executado.