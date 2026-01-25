# Recomendações de Pré-Processamento (Data Prep)

Com base na Análise Exploratória de Dados (EDA) realizada, seguem as recomendações técnicas para a limpeza e transformação dos dados visando a modelagem preditiva.

## 1. Tratamento de Valores Ausentes (Missing Values)

O relatório identificou os seguintes pontos críticos:
- **INGLÊS**: 67.09% de valores ausentes.
- **PORTUG** e **MATEM**: 0.23% (apenas 2 casos).

**Recomendações:**
1.  **Exclusão ou Imputação da coluna `INGLÊS`?**
    - Dado que quase 70% dos dados estão faltando, imputar pela média/mediana pode introduzir muito ruído.
    - **Sugestão A (Conservadora)**: Remover a coluna `INGLÊS` do modelo base.
    - **Sugestão B (Avançada)**: Criar uma flag binária `TEM_NOTA_INGLES` (0/1) e imputar o valor numérico com 0 ou mediana, permitindo que o modelo aprenda se a ausência da nota é relevante.
2.  **Linhas com `PORTUG` e `MATEM` ausentes**:
    - Como são apenas 2 registros (0.23%), recomenda-se **remover essas linhas** do dataset de treino, pois notas são preditores cruciais. Alternativamente, imputar pela mediana da turma (`TURMA`).

## 2. Tratamento do Target (`DEFAS`)

A variável `DEFAS` (Defasagem) apresenta valores numéricos negativos e positivos:
- Valores encontrados: `-1, 0, -2, -3, 1, -4, 2, -5`.
- A maior parte está concentrada em `-1` (47%) e `0` (28%).

**Recomendações:**
1.  **Definição do Problema (Classificação Binária vs Multiclasse)**:
    - O objetivo é "prever risco".
    - **Transformação Binária**: Criar uma nova variável `ALVO_DEFASAGEM`:
        - `1` (Com Defasagem/Risco): Se `DEFAS < 0` (assumindo que negativo indica atraso/defasagem).
        - `0` (Sem Defasagem/Ideal): Se `DEFAS >= 0`.
    - Isso simplifica o problema e lida com o desbalanceamento das classes minoritárias (-3, -4, -5, 1, 2).

## 3. Variáveis Categóricas e encoding

- **`PEDRA_22`**: Variável categórica (ex: Quartzo, Ametista, etc.).
    - **Recomendação**: Usar **Label Encoding** se houver uma ordem implícita de valor ("Pedras preciosas"), ou **One-Hot Encoding** se forem categorias nominais sem ordem. Verificar a cardinalidade.
- **`INSTITUIÇÃO_DE_ENSINO`**:
    - Verificar a quantidade de instituições únicas. Se < 10, usar One-Hot Encoding. Se > 10, considerar agrupar as menos frequentes como 'OUTROS' ou usar Target Encoding.
- **`TURMA`**:
    - Alta cardinalidade provável. Pode conter informação repetitiva com `FASE` e `ANO_INGRESSO`.
    - **Recomendação**: Remover `TURMA` do modelo incialmente para evitar overfitting, mantendo `FASE` como indicador de nível escolar.

## 4. Engenharia de Features (Sugestões)

1.  **Média Geral das Notas**: Criar `MEDIA_GERAL = (PORTUG + MATEM) / 2`. A correlação entre Português e Matemática é de 0.53, indicando que capturam aptidões diferentes, mas a média resume o desempenho acadêmico.
2.  **Tempo de Casa**: `TEMPO_CASA = 2024 - ANO_INGRESSO`. Alunos mais antigos podem ter padrões de defasagem diferentes.

## 5. Seleção de Features (Correlação)

- Observamos altíssima correlação entre:
    - `IDA` e `INGLÊS` (0.90)
    - `IDA` e `MATEM` (0.87)
    - `IAN` e `DEFAS` (0.84) -> **Atenção**: `IAN` parece ser um indicador derivado diretamente do target ou muito próximo dele. Verificar se `IAN` (Indicador de Adequação de Nível?) não é um *data leak* (vazamento de dados) do target `DEFAS`.
    - **Recomendação Crítica**: Validar o significado de `IAN`. Se for calculado com base na defasagem, ele **deve ser removido** das features preditivas para evitar que o modelo "veja o futuro".

## Resumo do Plano de Ação

1.  [ ] Remover linhas com `PORTUG`/`MATEM` nulos.
2.  [ ] Decidir sobre `INGLÊS` (Remover ou Flag+Impute).
3.  [ ] Transformar `DEFAS` em target binário (0 = Ideal, 1 = Defasado).
4.  [ ] Remover `IAN` preventivamente (supeita de data leakage) ou investigar sua fórmula.
5.  [ ] Aplicar One-Hot Encoding em `PEDRA_22`, `INSTITUIÇÃO` e `FASE`.
6.  [ ] Remover `TURMA` (cardinalidade/redundância).
