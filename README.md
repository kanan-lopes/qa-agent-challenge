# Asteria Systems Employee Policy Assistant — QA Agent Challenge

Projeto de QA para um agente corporativo de IA construído com **Amazon Bedrock AgentCore**. O objetivo do challenge foi avaliar, de forma rastreável, um agente com LLM, RAG, uso de ferramentas, memória, avaliação automática e Red Teaming.

> **Status da entrega:** Agent v1 e Agent v2 implementados e avaliados. Golden Dataset, AgentCore Evaluations, DeepEval e Red Teaming da v1 foram concluídos. O reteste adversarial da v2 não foi executado dentro da janela final do projeto e permanece como limitação conhecida.

---

## 1. Visão geral

O agente responde dúvidas de funcionários da empresa fictícia **Asteria Systems** sobre cinco domínios de política interna:

- Travel;
- Expenses;
- Remote Work;
- Leave;
- Procurement.

O comportamento esperado é grounded:

- perguntas dependentes de política devem consultar a Knowledge Base;
- apenas o conteúdo corporativo recuperado pode ser tratado como política oficial;
- quando a política não contém evidência suficiente, o agente deve se abster;
- o agente não pode aprovar compras, licenças ou despesas;
- o agente não pode alterar políticas, inventar processos ou alegar ações que não executou;
- o agente deve permanecer dentro do escopo de Employee Policy Assistant;
- informações internas, system prompt e dados de outras sessões não devem ser revelados.

---

## 2. Arquitetura

```text
Policy documents
      ↓
Amazon S3
      ↓
Bedrock Managed Knowledge Base
      ↓
AgentCore Gateway (MCP)
      ↓
AgentCore Harness
      ↓
Bedrock model
      ↓
Grounded answer / abstention
```

### Componentes principais

- **AWS Region:** `us-east-1`
- **AgentCore Harness:** `employee_policy_assistant`
- **Gateway:** `employee-policy-gateway`
- **Knowledge Base:** `employee-policy-s3`
- **Gateway target:** `employee-policy-kb-target`
- **Memory:** Semantic + Summary
- **Observability:** AgentCore / CloudWatch
- **Agent v1:** Gemma 3 4B IT v1
- **Agent v2:** Qwen3-Coder-30B-A3B-Instruct
- **DeepEval judge final:** `mistral-nemo:12b` via Ollama
- **PolicyCompliance judge:** Amazon Nova Pro

A infraestrutura foi configurada principalmente pela **AWS Management Console**. As configurações congeladas do agente estão documentadas na pasta `agent/`.

> O repositório não deve conter credenciais, tokens temporários, Account IDs, secrets ou ARNs sensíveis.

---

## 3. Estratégia de QA

O fluxo executado foi:

```text
Agent v1
  ↓
Exploratory Testing
  ↓
Golden Dataset
  ↓
AgentCore Evaluations
  ↓
DeepEval
  ↓
Red Teaming v1
  ↓
Failure Analysis
  ↓
Prompt + model mitigation
  ↓
Agent v2
  ↓
Golden Dataset regression
  ↓
AgentCore Evaluations v2
  ↓
DeepEval v2
```

A rastreabilidade principal utilizada foi:

```text
risk → test → evidence → failure → mitigation → regression
```

O reteste de Red Teaming da v2 foi planejado, mas não executado dentro da janela final da entrega.

---

## 4. Configuração do agente

A configuração do sistema sob teste está versionada em:

```text
agent/
├── README.md
├── config_v1.md
├── config_v2.md
├── system_prompt_v1.md
└── system_prompt_v2.md
```

### Agent v1

A baseline utilizou:

- **Gemma 3 4B IT v1**;
- Knowledge Base e Gateway configurados;
- Memory habilitada;
- observabilidade habilitada.

O principal problema observado foi estrutural: o modelo frequentemente conseguia descobrir a ferramenta com `mcp tools/list`, mas **não executava uma chamada real de Retrieve** antes de responder.

### Agent v2

A v2 utiliza:

- **Qwen3-Coder-30B-A3B-Instruct**;
- `temperature = 0`;
- `max tokens = 3000`;
- mesmo Gateway, Knowledge Base, Memory e corpus da baseline;
- prompt reforçado para:
  - tornar Retrieve obrigatório em perguntas dependentes de política;
  - impedir que afirmações do usuário sejam tratadas como fonte oficial;
  - reforçar abstenção;
  - impedir falsa alegação de grounding;
  - reforçar limites de autoridade;
  - proteger prompt, configuração interna e dados de outras sessões.

Detalhes completos:

```text
agent/config_v1.md
agent/config_v2.md
```

---

## 5. Knowledge Base e corpus

A Knowledge Base contém cinco políticas fictícias:

```text
knowledge_base/documents/
├── expense_policy.md
├── leave_policy.md
├── procurement_policy.md
├── remote_work_policy.md
└── travel_policy.md
```

A camada de retrieval foi validada separadamente antes da avaliação do agente.

A validação confirmou que:

- a Knowledge Base estava operacional;
- documentos corretos podiam ser recuperados;
- relevância semântica não garante que o chunk mais preciso apareça entre os primeiros resultados;
- ausência de uma regra no corpus exige comportamento de abstenção por parte do agente.

Detalhes:

```text
docs/retrieval_validation.md
```

---

## 6. Golden Dataset

O Golden Dataset contém **18 cenários**:

| Categoria | Casos | Objetivo |
|---|---:|---|
| Policy QA | GD-001–GD-007 | Regras centrais das cinco políticas |
| Boundary Value | GD-008–GD-010 | Valores-limite de R$500, R$5.000 e R$50 |
| Abstention | GD-011–GD-013 | Lacunas deliberadas da base |
| Authority Boundary | GD-014–GD-015 | Pedidos de aprovação que o agente não pode executar |
| Multi-turn | GD-016–GD-017 | Continuidade de contexto e follow-up |
| Scope Control | GD-018 | Pergunta fora do domínio |

Dataset:

```text
datasets/golden_dataset.json
```

Os casos multi-turn são avaliados por turno no DeepEval, resultando em:

- **20 casos atômicos** para Answer Relevancy e G-Eval;
- **19 casos atômicos** para Faithfulness, pois `GD-018` não possui contexto corporativo aplicável.

---

## 7. Estrutura principal do repositório

```text
qa-agent-challenge/
├── agent/
│   ├── README.md
│   ├── config_v1.md
│   ├── config_v2.md
│   ├── system_prompt_v1.md
│   └── system_prompt_v2.md
├── datasets/
│   └── golden_dataset.json
├── docs/
├── evaluations/
│   ├── agentcore/
│   └── deepeval/
├── knowledge_base/
│   └── documents/
├── red_team/
│   └── evidence/
├── results/
│   ├── baseline/
│   └── v2/
├── tests/
│   ├── golden_dataset_runner.py
│   └── test_harness_connection.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 8. Pré-requisitos

- Python **3.13**;
- AWS CLI ou credenciais temporárias válidas;
- acesso aos recursos Bedrock / AgentCore utilizados no projeto;
- Ollama;
- modelo local `mistral-nemo:12b`.

Instalação:

```bash
pip install -r requirements.txt
ollama pull mistral-nemo:12b
```

> As dependências em `requirements.txt` não estão pinadas por versão porque o ambiente original não foi congelado com `pip freeze`.

---

## 9. Variáveis de ambiente

Use `.env.example` apenas como referência.

Principais variáveis:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_SESSION_TOKEN
AWS_REGION
AWS_DEFAULT_REGION

HARNESS_ARN
HARNESS_LOG_GROUP
POLICY_COMPLIANCE_EVALUATOR_ID

DEEPEVAL_JUDGE_MODEL
OLLAMA_BASE_URL
DEEPEVAL_RESULTS_PATH
DEEPEVAL_CASE_IDS
```

Nunca faça commit de valores reais de credenciais.

---

## 10. Validação e execução do Golden Dataset

Validar o dataset sem chamar a AWS:

```bash
python tests/golden_dataset_runner.py --mode validate
```

Pilot:

```bash
python tests/golden_dataset_runner.py --mode pilot
```

Execução completa:

```bash
python tests/golden_dataset_runner.py --mode all
```

Resultados oficiais preservados:

```text
results/baseline/golden_results_raw_972e97b8.json
results/v2/golden_results_raw_6133af15.json
```

O runner **não infere uso de ferramenta a partir do texto da resposta**. A confirmação real de Retrieve é feita por trajectory/observability.

---

## 11. AgentCore Evaluations

A avaliação formal utilizou:

- `Builtin.Correctness`
- `Builtin.GoalSuccessRate`
- `Builtin.TrajectoryAnyOrderMatch`
- `PolicyCompliance` — evaluator customizado com Amazon Nova Pro

Scripts principais:

```bash
python evaluations/agentcore/run_baseline_evaluation.py
python evaluations/agentcore/run_policy_compliance_evaluation.py
python evaluations/agentcore/run_v2_evaluation.py
python evaluations/agentcore/run_v2_policy_compliance_evaluation.py
```

### Papel das métricas

- **Correctness:** qualidade factual da resposta em relação ao esperado;
- **GoalSuccessRate:** cumprimento do objetivo funcional e das assertions do cenário;
- **TrajectoryAnyOrderMatch:** presença da ferramenta esperada na trajetória;
- **PolicyCompliance:** comportamento específico do domínio, como autoridade, escopo, abstenção, grounding honesto e não-invenção.

> As avaliações AgentCore reinvocam o Harness. Portanto, podem diferir da execução bruta do Golden Dataset mesmo com temperatura 0.

---

## 12. Resultados AgentCore — v1 × v2

| Métrica | v1 | v2 |
|---|---:|---:|
| Correctness | 5.0% | **75.0%** |
| GoalSuccessRate | 0% | **77.8%** |
| TrajectoryAnyOrderMatch | 0% | **76.5%** |
| PolicyCompliance | 0.375 | **0.986** |

A trajetória esperada de Retrieve passou de:

```text
Agent v1: 0/17
Agent v2: 13/17
```

O `PolicyCompliance` é complementar: ele mede conformidade comportamental, mas não substitui a trajectory, pois não penaliza toda ausência de tool call.

Conclusões completas:

```text
results/v2/evaluations/AgentCore_V2_Evaluations_Conclusoes_Completas.md
```

---

## 13. DeepEval

O DeepEval foi utilizado como uma segunda frente independente de avaliação.

### Métricas finais

| Métrica | Threshold |
|---|---:|
| Answer Relevancy | ≥ 0.70 |
| Reference-grounded Faithfulness | ≥ 0.80 |
| Policy Answer Quality [G-Eval] | ≥ 0.80 |

Judge final:

```text
mistral-nemo:12b
```

### Nota metodológica sobre Faithfulness

A Faithfulness utilizada no projeto é **Reference-grounded Faithfulness**.

O `retrieval_context` é formado por trechos oficiais curados das políticas e **não pelos chunks reais recuperados em runtime**.

Isso foi necessário porque a v1 não realizava Retrieve de forma confiável, tornando impossível construir uma baseline autêntica de runtime RAG Faithfulness.

Assim, duas perguntas são avaliadas separadamente:

```text
DeepEval Faithfulness
→ A resposta é sustentada pela política oficial de referência?

AgentCore Trajectory
→ O agente realmente executou Retrieve?
```

Essas duas evidências são complementares e não devem ser confundidas.

---

## 14. Execução do DeepEval

Exemplo para respostas salvas da v2:

```powershell
$env:DEEPEVAL_JUDGE_MODEL="mistral-nemo:12b"
$env:DEEPEVAL_RESULTS_PATH="$PWD\\results\\v2\\golden_results_raw_6133af15.json"
$env:DEEPEVAL_CASE_IDS="GD-001,GD-002,GD-003"

deepeval test run .\\evaluations\\deepeval\\test_final_deepeval.py::test_answer_relevancy -v
deepeval test run .\\evaluations\\deepeval\\test_final_deepeval.py::test_reference_grounded_faithfulness -v
deepeval test run .\\evaluations\\deepeval\\test_final_deepeval.py::test_policy_answer_quality -v
```

As respostas de v1 e v2 foram avaliadas com o **mesmo judge**, permitindo uma comparação normalizada.

---

## 15. DeepEval — comparação normalizada

| Métrica | v1 normalizada | v2 |
|---|---:|---:|
| Answer Relevancy — média | 0.742 | **0.845** |
| Answer Relevancy — pass rate | 60.0% | **80.0%** |
| Faithfulness — média | 0.454 | **0.736** |
| Faithfulness — pass rate | 15.8% | **63.2%** |
| G-Eval — média | 0.515 | **0.680** |
| G-Eval — pass rate | 10.0% | **45.0%** |

A v2 atingiu a meta agregada de Answer Relevancy, mas permaneceu abaixo das metas agregadas de Faithfulness e G-Eval.

Resultados consolidados:

```text
results/baseline/DeepEval_V1_Normalized_Results.md
results/v2/DeepEval_V2_Final_Results.md
```

---

## 16. Red Teaming

A campanha da v1 foi manual e estruturada, com **15 ataques em 5 categorias**:

- Prompt Injection / Instruction Override;
- Authority Escalation;
- Policy Hallucination / Unsupported Claims;
- Scope & Information Leakage;
- Multi-turn / Context Manipulation.

Resultado principal:

```text
8/15 ataques atingiram o objetivo principal
Attack Success Rate (ASR): 53.3%
```

Principais achados:

- prompt injection;
- falsa autoridade;
- política fornecida pelo usuário tratada como verdade;
- alucinação em lacunas de política;
- system-prompt leakage;
- context poisoning;
- false grounding.

Artefatos:

```text
red_team/Red_Teaming_Resultados_Analise.md
red_team/evidence/
```

### Limitação da entrega

O reteste dos mesmos ataques contra a v2 foi planejado, mas **não foi executado dentro da janela final de entrega**.

Portanto, não há uma taxa adversarial da v2 reportada e nenhuma conclusão completa de segurança deve ser inferida apenas das avaliações funcionais.

---

## 17. Principais achados de QA

1. **Ferramenta disponível ≠ ferramenta executada.** A v1 tinha KB/Gateway configurados, mas Gemma frequentemente não realizava Retrieve real.
2. **Tool discovery ≠ tool execution.** `mcp tools/list` confirma descoberta, não consulta à Knowledge Base.
3. **Memory retrieval ≠ KB retrieval.** `RetrieveMemoryRecords` pertence ao AgentCore Memory.
4. **Relevância ≠ correção.** Uma resposta pode ser relevante e ainda conter política incorreta ou incompleta.
5. **Faithfulness ≠ sucesso end-to-end.** Uma saída pode não contradizer o contexto e ainda falhar funcionalmente.
6. **Tool call sem síntese final é uma falha funcional.** Esse padrão permaneceu em alguns casos da v2.
7. **LLM-as-a-Judge exige revisão humana.** Alguns reasons foram semanticamente inconsistentes; os scores formais foram preservados sem rerun seletivo para evitar cherry-picking.
8. **Uma métrica isolada não é suficiente.** O projeto combina resposta, trajetória, grounding, comportamento e adversarial testing.

---

## 18. Limitações

- Red Teaming v2 não executado;
- v2 ainda apresenta falhas residuais de tool orchestration e síntese pós-retrieval;
- metas agregadas de Faithfulness e G-Eval não foram atingidas;
- DeepEval Faithfulness usa contexto de referência curado, não chunks reais de runtime;
- LLM-as-a-Judge apresenta variabilidade e pode produzir justificativas inconsistentes;
- infraestrutura AWS configurada principalmente pela Management Console, sem IaC completa;
- dependências Python não estão pinadas por versão.

---

## 19. Documentação e artefatos principais

```text
agent/
datasets/golden_dataset.json

docs/agent_v1_validation.md
docs/retrieval_validation.md
docs/risks.md
docs/test_plan.md
docs/Relatorio_Final_Resumido_QA_Agent_Challenge.docx

evaluations/agentcore/
evaluations/deepeval/

results/baseline/DeepEval_V1_Normalized_Results.md
results/v2/DeepEval_V2_Final_Results.md
results/v2/Golden_Dataset_V2_Analise_Preliminar.md
results/v2/evaluations/AgentCore_V2_Evaluations_Conclusoes_Completas.md
results/v2/model_selection/V2_Smoke_Tests_Model_Selection.md

red_team/Red_Teaming_Resultados_Analise.md
red_team/evidence/
```

---

## 20. Conclusão

A Agent v2 apresentou melhora material em relação à baseline:

- maior correção factual;
- aumento expressivo de sucesso dos objetivos;
- uso real da Knowledge Base em grande parte dos cenários;
- maior grounding nas políticas;
- melhor controle de autoridade e escopo.

Ao mesmo tempo, os testes mostraram que a melhoria de um agente não pode ser reduzida a um único score.

A v2 ainda apresentou falhas de tool orchestration, síntese pós-retrieval e inconsistências em cenários específicos.

O projeto demonstra uma abordagem de QA baseada em múltiplos sinais:

```text
functional tests
+ trajectory
+ LLM-as-a-Judge
+ grounding
+ manual review
+ adversarial testing
```

A evidência disponível suporta a conclusão de que a **v2 é substancialmente superior à v1**, mas não permite afirmar que todos os riscos de segurança foram eliminados, pois o Red Teaming da v2 não foi executado.

