# Notebooks do Projeto Datathon

Este diretório contém os notebooks desenvolvidos para a análise de dados, exploração e modelagem preditiva do projeto. Abaixo, você encontra uma descrição detalhada do propósito e conteúdo de cada um.

## 1. Obtenção e Preparação dos Dados (`1 - obtendoDados.ipynb`)

Este notebook é responsável pela carga inicial e validação dos dados brutos.

*   **Fonte de Dados**: Lê o arquivo Excel `BASE DE DADOS PEDE 2024 - DATATHON.xlsx` localizado na pasta `../data`.
*   **Separação por Ano**: Cria DataFrames individuais para cada aba da planilha (`PEDE2022`, `PEDE2023`, `PEDE2024`).
*   **Verificação de Qualidade**: Executa um script de validação para garantir que as colunas essenciais para o cálculo do INDE (como IAN, IDA, IEG, IPP, IPV) estejam presentes e não contenham valores nulos críticos que inviabilizem a análise.

## 2. Análise Exploratória de Dados (`2 - EDA.ipynb`)

Focado na compreensão profunda dos indicadores educacionais e na distribuição dos dados.

*   **Estatística Descritiva**: Gera resumos estatísticos (média, desvio padrão, quartis) para o INDE e seus componentes (IAN, IDA, IEG, IAA, IPS, IPP, IPV).
*   **Insights por Dimensão**:
    *   **Acadêmica**: Analisa o desempenho (IDA) e a adequação de nível (IAN).
    *   **Psicossocial**: Avalia a autopercepção (IAA) e aspectos psicossociais (IPS).
    *   **Psicopedagógica**: Monitora o ponto de virada (IPV) e aspectos psicopedagógicos (IPP).
*   **Visualização**: Contém histogramas e gráficos de distribuição para visualizar a dispersão do INDE e identificar a concentração de alunos em cada faixa de classificação (Quartzo, Ágata, Ametista, Topázio).

## 3. Modelagem Preditiva (`3 - modelo.ipynb`)

Desenvolvimento de um modelo de Machine Learning para prever a classificação dos alunos.

*   **Definição do Target**: Cria a variável alvo `Pedra_Conceito` baseada nas faixas de nota do INDE (Quartzo < 6.1, Ágata < 7.2, Ametista < 8.2, Topázio >= 8.2).
*   **Engenharia de Features**: Criação de novas variáveis, como o `Status_DEFA` para categorizar a defasagem escolar.
*   **Pré-processamento**: Tratamento de valores ausentes utilizando imputação pela mediana.
*   **Modelo**: Treinamento de um classificador **Random Forest** para prever o conceito do aluno com base nos indicadores parciais.
*   **Avaliação**: Medição da acurácia do modelo e análise da importância das variáveis (feature importance) para entender quais indicadores mais influenciam a classificação final.