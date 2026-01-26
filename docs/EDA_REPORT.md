# Relatório de Análise Exploratória de Dados (EDA)

**Data de Geração**: 2026-01-26 19:25

**Total de Registros**: 860
**Total de Colunas**: 13

## 1. Tipos de Dados
| Coluna | Tipo |
| --- | --- |
| DEFAS | int64 |
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

Não há valores ausentes no dataset filtrado.

## 3. Estatísticas Descritivas (Numéricas)
| Coluna | Count | Mean | Std | Min | 25% | 50% | 75% | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEFAS | 860.0 | -0.94 | 0.85 | -5.0 | -1.0 | -1.0 | 0.0 | 2.0 |
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
| IAN | DEFAS | 0.84 |
| IDA | INDE_22 | 0.82 |
| IEG | INDE_22 | 0.8 |
| IPV | INDE_22 | 0.79 |
| IPV | IDA | 0.62 |
| IPV | IEG | 0.59 |
| IDA | IEG | 0.56 |