# Relatório de Análise Exploratória de Dados (EDA)

**Data de Geração**: 2026-01-25 12:01

**Total de Registros**: 860
**Total de Colunas**: 16

## 1. Tipos de Dados
| Coluna | Tipo |
| --- | --- |
| DEFAS | int64 |
| PORTUG | float64 |
| MATEM | float64 |
| INGLÊS | float64 |
| INDE_22 | float64 |
| IPS | float64 |
| IEG | float64 |
| IDA | float64 |
| IPV | float64 |
| IAA | float64 |
| IAN | float64 |
| FASE | int64 |
| TURMA | str |
| ANO_INGRESSO | int64 |
| INSTITUIÇÃO_DE_ENSINO | str |
| PEDRA_22 | str |

## 2. Valores Ausentes (Missingness)
| Coluna | Qtd Missing | % Missing |
| --- | --- | --- |
| INGLÊS | 577.0 | 67.09% |
| PORTUG | 2.0 | 0.23% |
| MATEM | 2.0 | 0.23% |

## 3. Estatísticas Descritivas (Numéricas)
| Coluna | Count | Mean | Std | Min | 25% | 50% | 75% | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEFAS | 860.0 | -0.94 | 0.85 | -5.0 | -1.0 | -1.0 | 0.0 | 2.0 |
| PORTUG | 858.0 | 6.32 | 2.08 | 0.0 | 5.2 | 6.7 | 7.8 | 10.0 |
| MATEM | 858.0 | 5.81 | 2.41 | 0.0 | 4.3 | 6.0 | 7.8 | 10.0 |
| INGLÊS | 283.0 | 5.88 | 2.96 | 0.0 | 3.5 | 6.3 | 8.5 | 10.0 |
| INDE_22 | 860.0 | 7.04 | 1.02 | 3.03 | 6.49 | 7.2 | 7.75 | 9.44 |
| IPS | 860.0 | 6.9 | 1.07 | 2.5 | 6.3 | 7.5 | 7.5 | 10.0 |
| IEG | 860.0 | 7.89 | 1.64 | 0.0 | 7.0 | 8.3 | 9.1 | 10.0 |
| IDA | 860.0 | 6.09 | 2.05 | 0.0 | 4.8 | 6.3 | 7.6 | 9.9 |
| IPV | 860.0 | 7.25 | 1.09 | 2.5 | 6.72 | 7.33 | 7.92 | 10.0 |
| IAA | 860.0 | 8.27 | 2.06 | 0.0 | 7.9 | 8.8 | 9.5 | 10.0 |
| IAN | 860.0 | 6.42 | 2.39 | 2.5 | 5.0 | 5.0 | 10.0 | 10.0 |
| FASE | 860.0 | 2.1 | 1.79 | 0.0 | 1.0 | 2.0 | 3.0 | 7.0 |
| ANO_INGRESSO | 860.0 | 2020.5 | 1.79 | 2016.0 | 2019.0 | 2021.0 | 2022.0 | 2022.0 |

## 4. Distribuição do Target (DEFAS)
| Categoria | Contagem | % |
| --- | --- | --- |
| -1 | 410 | 47.67% |
| 0 | 247 | 28.72% |
| -2 | 163 | 18.95% |
| -3 | 23 | 2.67% |
| 1 | 9 | 1.05% |
| -4 | 4 | 0.47% |
| 2 | 3 | 0.35% |
| -5 | 1 | 0.12% |

## 5. Correlações (Pearson)
| Variável 1 | Variável 2 | Correlação |
| --- | --- | --- |
| IDA | INGLÊS | 0.9 |
| IDA | MATEM | 0.87 |
| IAN | DEFAS | 0.84 |
| IDA | PORTUG | 0.83 |
| IDA | INDE_22 | 0.82 |
| IEG | INDE_22 | 0.8 |
| IPV | INDE_22 | 0.79 |
| INDE_22 | INGLÊS | 0.72 |
| INDE_22 | PORTUG | 0.69 |
| INDE_22 | MATEM | 0.69 |
| IPV | IDA | 0.62 |
| IPV | INGLÊS | 0.61 |
| IPV | IEG | 0.59 |
| IEG | INGLÊS | 0.58 |
| INGLÊS | PORTUG | 0.56 |
| IDA | IEG | 0.56 |
| INGLÊS | MATEM | 0.55 |
| IPV | MATEM | 0.55 |
| IEG | PORTUG | 0.54 |
| MATEM | PORTUG | 0.53 |