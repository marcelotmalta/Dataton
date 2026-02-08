
# Dicionário de Dados: `df_Base_final.csv`

| Nome da Variável | Descrição                                               | Dimensão / Categoria     | Fonte do Dado                            |
| ---------------- | ------------------------------------------------------- | ------------------------ | ---------------------------------------- |
| **NOME**         | Identificador do aluno                                  | Identificação            | Registro administrativo                  |
| **INDE**         | Índice de Desenvolvimento Educacional (Indicador Geral) | Geral                    | Composto                                 |
| **IAN**          | Indicador de adequação de nível                         | Dimensão Acadêmica       | Registros administrativos                |
| **IDA**          | Indicador de desempenho acadêmico                       | Dimensão Acadêmica       | Notas de Provas e Média Geral            |
| **IEG**          | Indicador de Engajamento                                | Dimensão Acadêmica       | Lição de casa e voluntariado             |
| **IAA**          | Indicador de Autoavaliação                              | Dimensão Psicossocial    | Questionário de autoavaliação individual |
| **IPS**          | Indicador Psicossocial                                  | Dimensão Psicossocial    | Questionário de avaliação das psicólogas |
| **IPP**          | Indicador Psicopedagógico                               | Dimensão Psicopedagógica | Questionário de pedagogos e professores  |
| **IPV**          | Indicador do Ponto de Virada                            | Dimensão Psicopedagógica | Questionário de pedagogos e professores  |
| **ANO**          | Ano de referência da coleta dos dados                   | Identificação            | Registro histórico                       |
| **FASE**         | Fase escolar do aluno (Ex: 0 a 7 ou Fase 8)             | Identificação            | Registro administrativo                  |
| **FASE IDEAL**   | Fase escolar ideal para o aluno                         | Identificação            | Calculado / Registro                     |
| **DEFA**         | Diferença entre a fase atual e a fase ideal             | Análise de Desempenho    | Calculado                                |

### Categorização dos Indicadores (Conforme Metodologia)

* **Indicadores de Avaliação:** IAN, IDA, IEG e IAA.
* **Indicadores de Conselho:** IPS, IPP e IPV.

### Observações Técnicas para `df_Base_final`

* **IAA (Fases 0 a 7):** Conforme sua análise anterior, este campo é calculado via fórmula de resíduo do INDE quando os dados originais estão zerados.
* **IPP:** Deve ser validado para garantir que não existam valores negativos decorrentes de erros de cálculo na base de origem.
* **Limpeza:** Registros onde `INDE == 'INCLUIR'` foram removidos para garantir a integridade estatística da base.

