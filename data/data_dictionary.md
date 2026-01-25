# Dicionário de Dados - processed_train.csv

Este arquivo descreve as variáveis presentes no dataset processado `processed_train.csv`.

## Visão Geral

O arquivo contém dados de alunos, incluindo indicadores acadêmicos, psicossociais e informações de identificação (anonimizadas ou codificadas), juntamente com a variável alvo `TARGET`.

## Descrição das Colunas

| Coluna                                   | Descrição                                                                                                                                                    | Tipo de Dado       |
| :--------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------- |
| **PORTUG**                               | Nota obtida na disciplina de Português.                                                                                                                      | Numérico (Float)   |
| **MATEM**                                | Nota obtida na disciplina de Matemática.                                                                                                                     | Numérico (Float)   |
| **INDE_22**                              | Índice de Desenvolvimento Educacional (referência 2022). Indicador composto geral.                                                                           | Numérico (Float)   |
| **IPS**                                  | Índice Psicosocial. Mede aspectos sociais e emocionais do aluno.                                                                                             | Numérico (Float)   |
| **IEG**                                  | Índice de Engajamento. Mede o envolvimento do aluno com as atividades escolares.                                                                             | Numérico (Float)   |
| **IDA**                                  | Índice de Desempenho Acadêmico. Composto por notas e avaliações.                                                                                             | Numérico (Float)   |
| **IPV**                                  | Índice de Ponto de Virada. Avalia a superação de desafios pelo aluno.                                                                                        | Numérico (Float)   |
| **IAA**                                  | Índice de Autoavaliação. Nota atribuída pelo próprio aluno.                                                                                                  | Numérico (Float)   |
| **ANO_INGRESSO**                         | Ano em que o aluno ingressou na instituição.                                                                                                                 | Numérico (Inteiro) |
| **PEDRA_22**                             | Classificação do aluno em 2022 (codificada numericamente). Ex: Quartzo=1, Ágata=2, Ametista=3, Topázio=4.                                                    | Numérico (Inteiro) |
| **TARGET**                               | Variável alvo binarizada. 0 indica "Sem Defasagem" (Defasagem = 0) e 1 indica "Com Defasagem" (Defasagem diferente de 0). Baseado na distribuição dos dados. | Numérico (Inteiro) |
| **MEDIA_GERAL**                          | Média geral das notas do aluno (calculada a partir de Português e Matemática ).                                                                              | Numérico (Float)   |
| **INSTITUIÇÃO_DE_ENSINO_Escola Pública** | Variável *Dummy* (One-Hot). 1 se a instituição for Escola Pública, 0 caso contrário.                                                                         | Numérico (Binário) |
| **INSTITUIÇÃO_DE_ENSINO_Rede Decisão**   | Variável *Dummy* (One-Hot). 1 se a instituição for Rede Decisão, 0 caso contrário.                                                                           | Numérico (Binário) |
| **FASE_1**                               | Variável *Dummy* para a Fase 1.                                                                                                                              | Numérico (Binário) |
| **FASE_2**                               | Variável *Dummy* para a Fase 2.                                                                                                                              | Numérico (Binário) |
| **FASE_3**                               | Variável *Dummy* para a Fase 3.                                                                                                                              | Numérico (Binário) |
| **FASE_4**                               | Variável *Dummy* para a Fase 4.                                                                                                                              | Numérico (Binário) |
| **FASE_5**                               | Variável *Dummy* para a Fase 5.                                                                                                                              | Numérico (Binário) |
| **FASE_6**                               | Variável *Dummy* para a Fase 6.                                                                                                                              | Numérico (Binário) |
| **FASE_7**                               | Variável *Dummy* para a Fase 7.                                                                                                                              | Numérico (Binário) |
