# Cenários de Teste para API de Desempenho do Aluno

Este documento descreve os cenários de teste para o endpoint `/predict` da API, utilizando o formato "Dado que... É esperado que...".

## Estrutura da Resposta da API

A API retorna um objeto JSON com os seguintes campos:

| Campo                          | Tipo   | Descrição                                                      |
| ------------------------------ | ------ | -------------------------------------------------------------- |
| `prediction`                   | string | Label da classe predita (ex: "Topázio", "Quartzo")             |
| `prediction_index`             | int    | Índice numérico da classe predita                              |
| `probabilities`                | object | Mapa de probabilidades por classe {classe: probabilidade}      |
| `risk_score`                   | float  | Score de risco calculado (0.0 a 1.0, onde maior = maior risco) |
| `risk_tier`                    | string | Tier de risco ("Crítico", "Alto", "Médio", "Baixo")            |
| `acao_sugerida`                | string | Ação sugerida principal baseada em DEFA e risco                |
| `suggested_messages.family`    | string | Mensagem contextualizada para a família                        |
| `suggested_messages.professor` | string | Mensagem contextualizada para o professor                      |
| `top_drivers`                  | array  | Principais fatores que influenciam a predição                  |
| `input_features`               | object | Features processadas usadas na predição                        |
| `defa_int`                     | int    | Valor de DEFA arredondado para inteiro                         |
| `model_version`                | string | Versão do modelo utilizado                                     |

## Legenda das Métricas de Entrada

- **IAN**: Indicador de Aproveitamento no Nível (0-10)
- **IDA**: Indicador de Desempenho Acadêmico (0-10)
- **IEG**: Indicador de Engajamento (0-10)
- **IAA**: Indicador de Autoavaliação (0-10)
- **IPS**: Indicador Psicossocial (0-10)
- **IPP**: Indicador Psicopedagógico (0-10)
- **IPV**: Indicador de Ponto de Virada (0-10)
- **FASE**: Fase do curso (inteiro)
- **DEFA**: Defasagem (float, negativo = atrasado, positivo = adiantado, 0 = no tempo)

## Lógica de Ações Sugeridas

A lógica de geração de ações sugeridas segue estas regras:

### DEFA < 0 (Defasagem - Aluno Atrasado)
- **DEFA <= -3**: "Recuperação Intensiva (grave)" - Intervenção urgente
- **-3 < DEFA < 0**: "Recuperação de Aprendizagem" - Plano de recuperação

### DEFA > 0 (Aluno Adiantado)
- **DEFA >= 3**: "Aprofundamento / Enriquecimento (alto)" - Possível aceleração
- **0 < DEFA < 3**: "Enriquecimento Curricular (moderado)" - Atividades de extensão

### DEFA = 0 (No Tempo)
Baseado no `risk_score`:
- **risk_score >= 0.75**: "Intervenção Psicopedagógica" (Risco Crítico)
- **0.5 <= risk_score < 0.75**: "Acompanhamento Intensivo" (Risco Alto)
- **prediction = "Topázio"**: "Enriquecimento Curricular"
- **Outros casos**: "Monitoramento e Micro-intervenção"

---

## Cenários de Teste

### Cenário 1: O Aluno "Excelente"

**Dado que** o aluno tem o seguinte perfil de notas:
- IAN: 9.5
- IDA: 9.0
- IEG: 9.5
- IAA: 9.0
- IPS: 8.5
- IPP: 8.0
- IPV: 9.0
- FASE: 2
- DEFA: 1.0 (Adiantado)

**É esperado que** a API retorne:
- `prediction`: Classe de alto desempenho (ex: "Topázio" ou similar)
- `risk_score`: Baixo (< 0.3)
- `risk_tier`: "Baixo" ou "Médio"
- `acao_sugerida`: "Enriquecimento Curricular (moderado)"
- `suggested_messages.family`: Mensagem indicando que o aluno está adiantado e sugerindo atividades de extensão
- `suggested_messages.professor`: Orientação para oferecer desafios adicionais
- `defa_int`: 1

**Validações:**
- ✓ Status code: 200
- ✓ Todos os campos obrigatórios presentes
- ✓ `risk_score` entre 0.0 e 1.0
- ✓ `probabilities` contém ao menos uma classe
- ✓ Soma das probabilidades ≈ 1.0

---

### Cenário 2: O Aluno "Médio"

**Dado que** o aluno tem o seguinte perfil de notas:
- IAN: 6.0
- IDA: 6.5
- IEG: 7.0
- IAA: 6.0
- IPS: 7.0
- IPP: 6.0
- IPV: 6.0
- FASE: 3
- DEFA: 0.0 (No limite)

**É esperado que** a API retorne:
- `prediction`: Classe de desempenho mediano (ex: "Pedra B" ou "Pedra C")
- `risk_score`: Moderado (0.3 - 0.6)
- `risk_tier`: "Médio"
- `acao_sugerida`: "Monitoramento e Micro-intervenção" ou "Acompanhamento Intensivo"
- `suggested_messages.family`: Mensagem de acompanhamento de rotina
- `suggested_messages.professor`: Orientação para monitorar evolução
- `defa_int`: 0

**Validações:**
- ✓ Status code: 200
- ✓ Ação sugerida apropriada para DEFA = 0 e risco moderado
- ✓ Mensagens contextualizadas presentes

---

### Cenário 3: O Aluno "Com Dificuldades"

**Dado que** o aluno tem o seguinte perfil de notas:
- IAN: 3.0
- IDA: 4.0
- IEG: 3.0
- IAA: 4.0
- IPS: 4.0
- IPP: 3.0
- IPV: 2.0
- FASE: 1
- DEFA: -2.0 (Defasagem significativa)

**É esperado que** a API retorne:
- `prediction`: Classe de baixo desempenho (ex: "Pedra D" ou "Quartzo")
- `risk_score`: Alto (> 0.6)
- `risk_tier`: "Alto" ou "Crítico"
- `acao_sugerida`: "Recuperação de Aprendizagem"
- `suggested_messages.family`: Mensagem alertando sobre defasagem e recomendando plano de recuperação
- `suggested_messages.professor`: Orientação para atividades focalizadas e monitoramento
- `defa_int`: -2

**Validações:**
- ✓ Status code: 200
- ✓ Ação sugerida reflete defasagem negativa
- ✓ `risk_tier` indica risco elevado
- ✓ Mensagens contêm informação sobre DEFA negativo

---

### Cenário 4: O Aluno "Em Recuperação" (Esforço Alto / Histórico Baixo)

**Dado que** o aluno tem o seguinte perfil de notas:
- IAN: 5.0
- IDA: 5.0
- IEG: 8.5 (Alto Engajamento)
- IAA: 7.0
- IPS: 6.0
- IPP: 5.0
- IPV: 9.0 (Ponto de Virada Alto)
- FASE: 4
- DEFA: 0.0

**É esperado que** a API retorne:
- `prediction`: Classe que reflete o esforço de recuperação
- `risk_score`: Moderado a baixo (impacto positivo de IEG e IPV)
- `risk_tier`: "Médio" ou "Baixo"
- `acao_sugerida`: "Monitoramento e Micro-intervenção" ou "Manutenção do Desempenho"
- `suggested_messages.family`: Mensagem reconhecendo esforço e orientando continuidade
- `suggested_messages.professor`: Orientação para apoiar o momento de virada
- `defa_int`: 0
- `top_drivers`: Deve incluir IEG e/ou IPV como fatores importantes

**Validações:**
- ✓ Status code: 200
- ✓ Predição reflete impacto positivo de engajamento alto
- ✓ `top_drivers` identifica IEG ou IPV como relevantes

---

### Cenário 5: O Aluno "Em Declínio" (Histórico Bom / Esforço Baixo)

**Dado que** o aluno tem o seguinte perfil de notas:
- IAN: 8.0
- IDA: 8.0
- IEG: 3.0 (Baixo Engajamento)
- IAA: 5.0
- IPS: 5.0
- IPP: 5.0
- IPV: 2.0
- FASE: 5
- DEFA: 0.0

**É esperado que** a API retorne:
- `prediction`: Classe que reflete o risco de declínio
- `risk_score`: Moderado a alto (impacto negativo de baixo engajamento)
- `risk_tier`: "Médio" ou "Alto"
- `acao_sugerida`: "Acompanhamento Intensivo" ou "Monitoramento e Micro-intervenção"
- `suggested_messages.family`: Mensagem alertando sobre queda de engajamento
- `suggested_messages.professor`: Orientação para investigar causas do baixo engajamento
- `defa_int`: 0
- `top_drivers`: Deve incluir IEG como fator de risco

**Validações:**
- ✓ Status code: 200
- ✓ Predição reflete impacto negativo de baixo engajamento
- ✓ Mensagens abordam questão de engajamento

---

### Cenário 6: O Aluno "Em Risco Crítico" (Alta Defasagem)

**Dado que** o aluno tem o seguinte perfil de notas:
- IAN: 7.0
- IDA: 7.0
- IEG: 7.0
- IAA: 7.0
- IPS: 7.0
- IPP: 7.0
- IPV: 7.0
- FASE: 6
- DEFA: -5.0 (Defasagem muito alta)

**É esperado que** a API retorne:
- `prediction`: Classe impactada negativamente pela alta defasagem
- `risk_score`: Alto (> 0.6)
- `risk_tier`: "Alto" ou "Crítico"
- `acao_sugerida`: "Recuperação Intensiva (grave)"
- `suggested_messages.family`: Mensagem alertando sobre defasagem grave e necessidade de reunião imediata
- `suggested_messages.professor`: Orientação para acionar plano de intervenção intensiva
- `defa_int`: -5

**Validações:**
- ✓ Status code: 200
- ✓ Ação sugerida reflete gravidade da defasagem (DEFA <= -3)
- ✓ Mensagens indicam urgência e necessidade de intervenção intensiva
- ✓ `risk_tier` indica risco crítico ou alto

---

## Critérios Gerais de Validação

Para todos os cenários, os testes devem validar:

1. **Estrutura da Resposta:**
   - Status code: 200
   - Todos os campos obrigatórios presentes
   - Tipos de dados corretos

2. **Validações de Range:**
   - `risk_score`: 0.0 ≤ valor ≤ 1.0
   - `prediction_index`: inteiro >= 0
   - `defa_int`: inteiro

3. **Validações de Probabilidades:**
   - `probabilities` não vazio
   - Todas as probabilidades entre 0.0 e 1.0
   - Soma das probabilidades ≈ 1.0 (±0.01)

4. **Consistência Lógica:**
   - `risk_tier` consistente com `risk_score`
   - `acao_sugerida` consistente com `defa_int` e `risk_score`
   - Mensagens não vazias e contextualizadas

5. **Validações Específicas de DEFA:**
   - DEFA < 0: Ações de recuperação
   - DEFA > 0: Ações de enriquecimento
   - DEFA = 0: Ações baseadas em risk_score
