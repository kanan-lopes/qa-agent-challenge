# Registro de Riscos — Employee Policy Assistant

## 1. Objetivo

Este documento registra os principais riscos de qualidade identificados para o
Employee Policy Assistant da Asteria Systems.

Os riscos foram definidos a partir de:

- comportamentos observados durante os testes exploratórios e smoke tests;
- arquitetura do agente com Knowledge Base, Gateway e Memory;
- limites funcionais definidos para o assistente;
- casos previstos no Golden Dataset.

O objetivo é manter rastreabilidade entre:

Risco → Caso de Teste → Resultado → Mitigação → Reteste

Os riscos classificados como **Observado** já foram identificados durante a
baseline inicial.

Os riscos classificados como **Esperado** ainda não foram necessariamente
observados, mas são relevantes para o domínio do agente e serão verificados
nas etapas seguintes.

---

## 2. Critérios de prioridade

A prioridade considera o impacto potencial do comportamento sobre a
confiabilidade do agente.

- **Alta:** pode produzir informação corporativa incorreta, apresentar
  informação inventada como oficial, ultrapassar os limites de autoridade do
  agente ou comprometer significativamente a confiabilidade das respostas.

- **Média:** prejudica a utilidade, consistência ou experiência do usuário, mas
  tende a apresentar impacto menor do que uma informação factual incorreta ou
  uma violação de autoridade.

- **Baixa:** comportamento indesejado com impacto limitado dentro do escopo
  atual do projeto.

---

## 3. Resumo dos riscos

| ID | Risco | Status | Prioridade | Casos relacionados |
|---|---|---|---|---|
| R01 | Omissão no uso da ferramenta da Knowledge Base | Observado | Alta | GD-001–GD-017 |
| R02 | Alucinação factual sem suporte | Observado | Alta | GD-001–GD-013 |
| R03 | Alucinação de política ou fonte | Observado | Alta | GD-001–GD-013 |
| R04 | Alegação falsa de fundamentação | Observado | Alta | GD-001–GD-013 |
| R05 | Falha de abstenção quando a informação não existe | Observado | Alta | GD-011–GD-013 |
| R06 | Solicitação de esclarecimento desnecessária ou criação de condições inexistentes | Observado | Média | GD-001–GD-007 |
| R07 | Interpretação incorreta de valores-limite | Esperado | Alta | GD-008–GD-010 |
| R08 | Contaminação de memória entre sessões | Observado | Alta | Isolamento dos testes / testes futuros de memória |
| R09 | Inconsistência de comportamento entre execuções | Observado | Média | Reexecuções do Golden Dataset |
| R10 | Violação dos limites de autoridade do agente | Esperado | Alta | GD-014–GD-015 |
| R11 | Falha de contexto em conversas multi-turn | Esperado | Média | GD-016–GD-017 |
| R12 | Falha de controle de escopo | Esperado | Média | GD-018 |

---

## 4. Detalhamento dos riscos

### R01 — Omissão no uso da ferramenta da Knowledge Base

**Status:** Observado  
**Prioridade:** Alta

O agente pode responder a uma pergunta dependente das políticas da empresa sem
executar a ferramenta `Retrieve` da Knowledge Base, mesmo quando ela está
disponível.

Esse risco é especialmente relevante porque as respostas relacionadas às
políticas corporativas devem ser fundamentadas nos documentos fornecidos pela
empresa, e não apenas no conhecimento interno do modelo.

Durante a baseline controlada com Gemma 3 4B IT, cinco smoke tests exigiam
consulta à Knowledge Base e nenhuma chamada bem-sucedida de `Retrieve` foi
observada.

Baseline observada:

- Chamadas `Retrieve` esperadas: 5
- Chamadas `Retrieve` observadas: 0
- Taxa de sucesso no uso da ferramenta: 0/5

**Impactos potenciais**

- respostas geradas sem evidência corporativa;
- aumento do risco de alucinação;
- redução da Faithfulness;
- dificuldade de distinguir políticas reais de conhecimento interno do modelo.

**Casos relacionados**

GD-001 a GD-017, sempre que a pergunta exigir consulta às políticas.

---

### R02 — Alucinação factual sem suporte

**Status:** Observado  
**Prioridade:** Alta

O agente pode inventar regras, limites, valores ou condições que não estão
presentes nas políticas fornecidas.

Durante a baseline foram observados exemplos como:

- valores de reembolso de alimentação inexistentes;
- limite diário de estacionamento em aeroporto inventado;
- regras de férias baseadas em tempo de serviço que não existem no corpus.

**Impactos potenciais**

Funcionários podem interpretar informações inventadas como regras corporativas
oficiais.

**Casos relacionados**

- GD-001–GD-010: perguntas factuais e valores-limite;
- GD-011–GD-013: perguntas sobre informações propositalmente ausentes.

---

### R03 — Alucinação de política ou fonte

**Status:** Observado  
**Prioridade:** Alta

O agente pode inventar nomes de políticas, identificadores ou documentos que
não existem na Knowledge Base.

Durante os testes da baseline, foram observadas referências a políticas e
identificadores inexistentes.

**Impactos potenciais**

- falsa percepção de suporte documental;
- redução da auditabilidade das respostas;
- dificuldade de verificar a resposta contra o corpus oficial.

**Casos relacionados**

GD-001–GD-013.

---

### R04 — Alegação falsa de fundamentação

**Status:** Observado  
**Prioridade:** Alta

O agente pode afirmar explicitamente que uma resposta foi obtida da Knowledge
Base mesmo quando nenhuma chamada de `Retrieve` foi executada.

Esse comportamento foi observado em testes nos quais a resposta utilizou
expressões equivalentes a “using the knowledge base”, enquanto os traces do
AgentCore mostravam que a ferramenta da Knowledge Base não havia sido chamada.

**Impactos potenciais**

Informações inventadas podem parecer oficialmente fundamentadas e confiáveis.

**Casos relacionados**

Principalmente GD-001–GD-013.

---

### R05 — Falha de abstenção quando a informação não existe

**Status:** Observado  
**Prioridade:** Alta

Quando a informação solicitada não está presente nas políticas corporativas, o
agente pode inventar uma resposta em vez de informar que a regra não está
especificada.

Um exemplo observado na baseline ocorreu quando o agente inventou um limite
diário de estacionamento em aeroporto, mesmo que essa informação não exista no
corpus.

**Impactos potenciais**

O usuário pode receber uma regra precisa, porém completamente inventada.

**Casos relacionados**

- GD-011 — limite de estacionamento em aeroporto;
- GD-012 — reembolso de coworking;
- GD-013 — licença parental.

---

### R06 — Solicitação de esclarecimento desnecessária ou criação de condições inexistentes

**Status:** Observado  
**Prioridade:** Média

O agente pode solicitar informações adicionais que não são necessárias para
responder à pergunta ou introduzir condições de elegibilidade que não existem
na política.

Durante a baseline, por exemplo, o agente solicitou cargo e departamento antes
de responder sobre o limite geral de trabalho remoto, embora essas informações
não sejam exigidas pela política fornecida.

**Impactos potenciais**

- redução da usabilidade;
- conversas mais longas sem necessidade;
- criação de condições inexistentes;
- falha em responder perguntas simples e diretamente documentadas.

**Casos relacionados**

GD-001–GD-007.

---

### R07 — Interpretação incorreta de valores-limite

**Status:** Esperado  
**Prioridade:** Alta

O agente pode interpretar incorretamente regras que envolvem limites inclusivos
ou exclusivos.

Os principais casos definidos para avaliação são:

- compra exatamente igual a R$ 500;
- compra exatamente igual a R$ 5.000;
- despesa exatamente igual a R$ 50.

**Impactos potenciais**

O agente pode indicar requisitos incorretos de aprovação, número de cotações ou
obrigatoriedade de comprovante.

**Casos relacionados**

- GD-008;
- GD-009;
- GD-010.

---

### R08 — Contaminação de memória entre sessões

**Status:** Observado  
**Prioridade:** Alta

O AgentCore Memory pode recuperar informações de conversas anteriores quando
testes diferentes utilizam o mesmo `Actor ID`, mesmo quando uma nova sessão é
criada.

Esse comportamento foi observado durante uma execução inicial do SMK-003, na
qual informações do teste anterior de Procurement influenciaram uma nova
pergunta sobre Travel.

A metodologia dos testes controlados foi posteriormente ajustada para utilizar:

- novo `Session ID`;
- `Actor ID` exclusivo para cada caso isolado.

**Impactos potenciais**

- contaminação dos resultados de avaliação;
- respostas influenciadas por contexto não relacionado;
- dificuldade de comparar casos de teste;
- risco de recuperação de informação pertencente a outra sessão lógica.

**Controle atual**

Cada teste independente utiliza um `Actor ID` exclusivo.

---

### R09 — Inconsistência de comportamento entre execuções

**Status:** Observado  
**Prioridade:** Média

Perguntas equivalentes ou repetidas podem gerar comportamentos
significativamente diferentes entre execuções.

Durante a exploração da baseline, uma mesma pergunta sobre Procurement gerou
comportamentos diferentes, incluindo:

- solicitação de esclarecimento desnecessária em uma execução;
- resposta factual sem suporte em outra execução.

**Impactos potenciais**

- baixa reprodutibilidade;
- experiência inconsistente para o usuário;
- maior dificuldade de interpretar os resultados das avaliações.

**Validação planejada**

O comportamento será observado durante as execuções do Golden Dataset e nos
retestes posteriores.

---

### R10 — Violação dos limites de autoridade do agente

**Status:** Esperado  
**Prioridade:** Alta

O agente pode sugerir ou afirmar incorretamente que possui autoridade para
aprovar, autorizar ou executar ações corporativas.

O Employee Policy Assistant pode explicar políticas, mas não pode:

- aprovar compras;
- aprovar pedidos de férias;
- autorizar despesas;
- emitir Purchase Orders;
- autorizar pagamentos;
- afirmar que executou alguma ação corporativa.

**Impactos potenciais**

O usuário pode acreditar incorretamente que uma ação foi oficialmente aprovada
ou executada.

**Casos relacionados**

- GD-014 — aprovação de compra;
- GD-015 — aprovação de férias.

---

### R11 — Falha de contexto em conversas multi-turn

**Status:** Esperado  
**Prioridade:** Média

O agente pode falhar ao manter informações relevantes entre diferentes turnos
da mesma conversa.

Exemplos:

- pergunta inicial sobre limite de hotel doméstico seguida de “And what about
  international travel?”;
- pergunta sobre trabalho remoto regular seguida de uma pergunta sobre exceção
  temporária.

**Impactos potenciais**

- interpretação incorreta de perguntas de follow-up;
- solicitação desnecessária para repetir informações;
- recuperação de política incorreta;
- perda de continuidade da conversa.

**Casos relacionados**

- GD-016;
- GD-017.

---

### R12 — Falha de controle de escopo

**Status:** Esperado  
**Prioridade:** Média

O agente pode responder perguntas que não possuem relação com as políticas da
Asteria Systems, comportando-se como um assistente de propósito geral.

O system prompt define o agente especificamente como Employee Policy Assistant.

**Impactos potenciais**

- expansão não controlada do comportamento do agente;
- uso desnecessário do modelo;
- aumento da superfície para solicitações irrelevantes ou adversariais.

**Caso relacionado**

GD-018.

---

## 5. Síntese dos riscos observados na baseline

A baseline inicial revelou uma relação importante entre diferentes riscos:

Knowledge Base não é consultada
→ ausência de evidência recuperada
→ possibilidade de alucinação factual ou de política
→ possível alegação falsa de fundamentação
→ falha de abstenção quando a informação não existe

Por esse motivo, o uso correto da Knowledge Base e a fundamentação das
respostas são considerados riscos centrais para o Agent v1.

O Golden Dataset e as avaliações automatizadas serão utilizados para medir
esses comportamentos formalmente antes da implementação das mitigações.

---

## 6. Próxima etapa

Os riscos definidos neste documento serão associados a métodos concretos de
validação em `docs/test_plan.md`.

O Test Plan deverá definir:

- quais casos do Golden Dataset cobrem cada risco;
- qual técnica de avaliação será utilizada;
- qual comportamento é esperado;
- quais critérios serão utilizados para determinar sucesso ou falha;
- quais evidências deverão ser coletadas.

A rastreabilidade esperada para o restante do projeto será:

Risco → Teste → Resultado da baseline → Mitigação → Reteste → Resultado final