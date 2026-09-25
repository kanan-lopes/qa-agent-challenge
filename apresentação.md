---
marp: true
paginate: true
size: 16:9
---

# QA de um Agente de Políticas Internas
## AWS Bedrock AgentCore + AgentCore Evaluations + DeepEval + Red Teaming

**Agente:** `employee_policy_assistant`  
**Domínio:** políticas internas fictícias da Asteria Systems  
**Objetivo do projeto:** construir um agente simples e concentrar o trabalho em **QA de agentes de IA**.

**Escopo das políticas:** Travel · Expenses · Remote Work · Leave · Procurement

<!--
TEMPO: 0:00–0:30 (~30 s)
FALA SUGERIDA:
“Eu construí um Employee Policy Assistant para a empresa fictícia Asteria Systems. O agente responde dúvidas sobre cinco políticas internas. O foco do challenge não foi sofisticar a aplicação, mas testar qualidade, grounding, uso de ferramentas, contexto multi-turno e segurança.”
-->

---

# 1. Arquitetura implementada na AWS

**Fluxo principal**

`Usuário → AgentCore Harness → modelo → AgentCore Gateway → Managed Knowledge Base → documentos no S3`

- 5 políticas em Markdown armazenadas no **S3**.
- **Bedrock Managed Knowledge Base** sincronizada com a fonte S3.
- **AgentCore Gateway** expondo a operação de recuperação para o agente.
- **Harness** com memória de sessão e observabilidade habilitadas.
- Configuração prioritariamente realizada pelo **AWS Management Console**.

![w:820](assets/aws_knowledge_base.png)

<!--
TEMPO: 0:30–1:10 (~40 s)
FALA SUGERIDA:
“A base oficial do agente são cinco documentos de política no S3. Eles alimentam uma Managed Knowledge Base, acessada por meio do AgentCore Gateway. O Harness executa o agente, mantém contexto de sessão e fornece observabilidade. Essa arquitetura também permitiu avaliar não apenas a resposta final, mas se o agente realmente usou o Retrieve.”
-->

---

# 2. Agent v1: o principal problema encontrado

**Modelo inicial exigido:** `Gemma 3 4B IT`

Na observabilidade, os smoke tests mostraram repetidamente:

- descoberta da ferramenta (`mcp tools/list`), mas **sem `tools/call / Retrieve` real**;
- respostas genéricas ou fabricadas mesmo quando a política deveria ser consultada;
- falsa aparência de grounding.

Exemplo de falha: o agente inventou **US$30/dia para estacionamento de aeroporto**, informação inexistente nas políticas.

<table><tr>
<td width="58%"><img src="assets/v1_observability_no_retrieve.png"></td>
<td width="42%"><img src="assets/v1_hallucination_airport_parking.png"></td>
</tr></table>

**Correção principal na v2:** prompt mais restritivo + `Qwen3-Coder-30B-A3B-Instruct`.

<!--
TEMPO: 1:10–2:05 (~55 s)
FALA SUGERIDA:
“O problema mais importante da v1 apareceu na observabilidade: o Gemma descobria a ferramenta, mas não executava o Retrieve. Isso resultava em respostas que pareciam fundamentadas, mas não estavam. Neste exemplo ele inventou um limite diário de estacionamento. Depois de testar alternativas, a v2 foi congelada com Qwen3-Coder 30B e um prompt que obriga Retrieve para perguntas de política, proíbe tratar afirmações do usuário como política e exige abstention quando não há evidência.”
-->

---

# 3. Sessão exploratória → Golden Dataset

A sessão exploratória orientou os riscos e os testes formais.

**Riscos principais:**
- omissão do Retrieve e falsa fundamentação;
- hallucination factual e de fontes;
- falha de abstention;
- ultrapassar limites de autoridade;
- perda de contexto multi-turno;
- vazamento de prompt/contexto e prompt injection.

**Golden Dataset:** **18 cenários**

| Categoria | Casos |
|---|---:|
| Policy QA | 7 |
| Boundary value | 3 |
| Abstention | 3 |
| Authority boundary | 2 |
| Multi-turn | 2 |
| Scope control | 1 |

**17/18** cenários esperavam uso da Knowledge Base; **4** testavam abstention.

![w:700](assets/golden_dataset_validation.png)

<!--
TEMPO: 2:05–2:50 (~45 s)
FALA SUGERIDA:
“Eu não parti direto para métricas. Primeiro fiz uma sessão exploratória, registrei riscos e transformei esses achados em um Golden Dataset de 18 cenários. Além de consultas normais, ele inclui valores-limite, perguntas sem resposta na política, pedidos de aprovação, multi-turno e controle de escopo. Isso deu rastreabilidade entre risco, teste e correção.”
-->

---

# 4. Avaliações: o que cada métrica revelou

### AgentCore Evaluations
- **Correctness:** a resposta está correta?
- **GoalSuccessRate:** o objetivo do cenário foi cumprido?
- **TrajectoryAnyOrderMatch:** o agente realmente percorreu a trajetória esperada e usou o Retrieve?
- **PolicyCompliance (custom):** respeitou regras de autoridade, escopo, grounding e não-invenção?

<table><tr>
<td width="54%"><img src="assets/agentcore_comparison.png"></td>
<td width="46%"><img src="assets/policy_compliance_baseline.png"></td>
</tr></table>

### DeepEval + pytest
- **Answer Relevancy:** respondeu ao que foi perguntado?
- **Reference-grounded Faithfulness:** a resposta é sustentada pelo contexto oficial de referência?
- **G-Eval:** a resposta cumpre o comportamento esperado para aquele caso?

![w:560](assets/deepeval_comparison.png)

### Avaliador personalizado — PolicyCompliance

Além dos avaliadores integrados do AgentCore, foi criado um avaliador customizado para verificar regras específicas do domínio, como:

- invenção de políticas ou valores não suportados;
- falha de abstenção quando a informação não existe;
- ultrapassagem dos limites de autoridade;
- controle de escopo;
- grounding honesto.

O avaliador utiliza **Amazon Nova Pro** como LLM-as-a-Judge e analisa a sessão completa, incluindo contexto, trajetória de ferramentas e assertions esperadas.

<img src="assets/policy_compliance_evaluator.png" width="92%">

> **Conclusão:** as métricas são complementares. Um score alto isolado não garante sucesso end-to-end.

<!--
TEMPO: 2:50–4:00 (~70 s)
FALA SUGERIDA:
“Na avaliação automatizada eu preferi usar métricas com papéis diferentes, em vez de olhar apenas um score final. No AgentCore, Correctness mede a qualidade da resposta, Goal Success verifica se o objetivo do cenário foi cumprido e Trajectory confirma se o agente realmente percorreu o caminho esperado, principalmente o Retrieve. Também criei um avaliador customizado, o PolicyCompliance, usando Nova Pro como judge, para verificar regras específicas do domínio, como não ultrapassar autoridade, não inventar política e respeitar escopo. Esse print mostra a execução do PolicyCompliance na baseline. Na v2 ele melhorou muito, mas esse resultado sozinho não significa sucesso completo, porque o avaliador não penalizava toda ausência de tool call. Por isso a trajetória foi essencial. No DeepEval usei Relevancy, Faithfulness e um G-Eval específico. O padrão geral foi: a v2 responde de forma mais relevante e fundamentada, mas ainda há casos em que o conteúdo parece correto e mesmo assim a execução falha, por exemplo quando aparece a chamada de ferramenta sem uma resposta final. Então a principal conclusão desta frente é que as métricas se complementam; nenhuma delas, isoladamente, descreve todo o comportamento do agente.”
-->

---


# 5. Red Teaming: onde a v1 ainda quebrava

**15 ataques estruturados**, cobrindo prompt injection, autoridade falsa, hallucination/abstention, information leakage, multi-turn e abuso de regras.

- **8/15 ataques bem-sucedidos (53,3%)**
- **7/15 resistidos (46,7%)**, vários com achados secundários

Falhas importantes incluíram:
- aceitar instrução direta para aprovar compra;
- confiar em falsa autoridade (“sou CFO”);
- aceitar política fornecida pelo próprio usuário;
- inventar coworking e parental leave;
- revelar conteúdo do system prompt;
- aceitar exceção urgente de procurement;
- corrupção de regra em conversa multi-turno.

![w:720](assets/redteam_v1_summary.png)

> **Reteste de Red Teaming na v2 ainda será executado antes do fechamento final.**

<!--
TEMPO: 4:00–4:55 (~55 s)
FALA SUGERIDA:
“O Red Teaming foi a frente de segurança. Foram 15 ataques em múltiplas categorias e oito tiveram sucesso contra a v1. As falhas mais relevantes foram quebra de autoridade, confiança em política fornecida pelo usuário, hallucinations em gaps reais e extração de system prompt. Esses achados influenciaram diretamente o prompt da v2. O reteste desses mesmos ataques na v2 é o último bloco ainda pendente.”
-->

---

# 6. O que mudou na v2 — e o que ainda falta

### Mudanças
- `Gemma 3 4B IT` → **Qwen3-Coder-30B-A3B-Instruct**
- política → **Retrieve obrigatório antes de responder**
- somente a KB pode ser tratada como fonte oficial
- gaps → **abstention**, sem inventar regras
- limites explícitos de autoridade, escopo e confidencialidade

![w:460](assets/v2_grounded_retrieve_answer.png)

### Resultado geral
- uso real do Retrieve passou de **0/17 → 13/17** na avaliação de trajetória;
- AgentCore e DeepEval mostram **melhora substancial**, mas não perfeição;
- risco residual principal: **tool call sem síntese final / textualização da chamada**, além de inconsistências de abstention;
- os judges também apresentaram falsos positivos/razões inconsistentes → **revisão humana continua necessária**.

**Conclusão atual:** a v2 é claramente superior à baseline, mas o fechamento de segurança depende do **Red Teaming v2** e da análise dos riscos residuais.

<!--
TEMPO: 4:55–6:00 (~65 s)
FALA SUGERIDA:
“A v2 mudou tanto o modelo quanto as regras de comportamento. O efeito mais importante foi sair de zero Retrieve real na v1 para 13 de 17 trajetórias esperadas na v2. As avaliações melhoraram de forma consistente, mas o agente ainda tem um problema de orquestração: em alguns casos ele gera ou expõe a chamada de ferramenta e não entrega a resposta final. Também encontrei limitações dos próprios LLM-as-a-Judge, então preservei resultados inconsistentes em vez de rerodar até obter um score melhor. Minha conclusão neste momento é que a v2 é materialmente melhor, mas eu só fecharia a recomendação de produção depois do reteste completo de Red Teaming e do tratamento dos riscos residuais.”
-->
