# Asteria Systems Employee Policy Assistant — QA Agent Challenge

Projeto de QA para um agente de IA corporativo construído no **AWS Bedrock AgentCore**. O foco do challenge não é criar uma aplicação complexa, mas demonstrar uma estratégia de testes rastreável para agentes com LLM, RAG, uso de ferramentas, memória, avaliação automática e Red Teaming.

> **Status atual:** Agent v2 e avaliações quantitativas concluídas. A campanha de Red Teaming da v1 foi concluída; o reteste adversarial da v2 ainda está pendente.

## Visão geral

O agente responde dúvidas de funcionários da empresa fictícia **Asteria Systems** sobre cinco domínios de política interna:

- Travel;
- Expenses;
- Remote Work;
- Leave;
- Procurement.

O comportamento esperado é **grounded**: perguntas dependentes de política devem consultar a Knowledge Base; quando a política não contém evidência suficiente, o agente deve se abster. O agente também não pode aprovar compras, licenças ou despesas, alterar políticas, inventar processos, revelar instruções internas ou tratar afirmações do usuário como política oficial.

## Arquitetura

```text
User
  ↓
AgentCore Harness
  ↓
Bedrock model
  ↓
AgentCore Gateway (MCP)
  ↓
Bedrock Managed Knowledge Base
  ↓
Policy documents
  ↓
Grounded answer / abstention
```

Componentes principais utilizados:

- **AWS Region:** `us-east-1`
- **AgentCore Harness:** `employee_policy_assistant`
- **Gateway:** `employee-policy-gateway`
- **Knowledge Base:** `employee-policy-s3`
- **Memory:** Semantic + Summary
- **Observability:** AgentCore / CloudWatch
- **Agent v1:** Gemma 3 4B IT v1
- **Agent v2:** Qwen3-Coder-30B-A3B-Instruct
- **DeepEval judge final:** `mistral-nemo:12b` via Ollama

> O repositório não deve conter credenciais, tokens temporários, ARNs com dados sensíveis ou secrets.

## Estratégia de QA

O fluxo adotado foi:

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
Agent v2
  ↓
AgentCore + DeepEval regression
  ↓
Red Teaming v2 (pending)
```

A rastreabilidade principal é:

```text
risk → test → evidence → failure → mitigation → regression
```

## Golden Dataset

O Golden Dataset contém **18 cenários** e cobre:

| Categoria | Casos | Objetivo |
|---|---:|---|
| Policy QA | GD-001–GD-007 | Regras centrais das cinco políticas |
| Boundary Value | GD-008–GD-010 | Valores-limite de R$500, R$5.000 e R$50 |
| Abstention | GD-011–GD-013 | Lacunas deliberadas da base |
| Authority Boundary | GD-014–GD-015 | Pedidos de aprovação que o agente não pode executar |
| Multi-turn | GD-016–GD-017 | Continuidade de contexto e follow-up |
| Scope Control | GD-018 | Pergunta fora do domínio |

Os cenários multi-turn são avaliados por turno no DeepEval, resultando em **20 casos atômicos** para Answer Relevancy/G-Eval e **19** para Faithfulness.

## Estrutura principal do repositório

```text
qa-agent-challenge/
├── agent/
├── knowledge_base/
│   └── documents/
├── datasets/
│   └── golden_dataset.json
├── evaluations/
│   ├── agentcore/
│   │   ├── build_ground_truth.py
│   │   ├── baseline_ground_truth.json
│   │   ├── run_baseline_evaluation.py
│   │   ├── run_policy_compliance_evaluation.py
│   │   ├── run_v2_evaluation.py
│   │   └── run_v2_policy_compliance_evaluation.py
│   └── deepeval/
│       ├── reference_contexts.json
│       ├── test_baseline_deepeval.py
│       └── test_final_deepeval.py
├── tests/
│   ├── golden_dataset_runner.py
│   └── test_harness_connection.py
├── red_team/
├── results/
│   ├── baseline/
│   └── v2/
├── docs/
├── requirements.txt
├── .env.example
└── README.md
```

A estrutura será revisada novamente antes da entrega final para remover pastas vazias e artefatos redundantes.

## Pré-requisitos

- Python **3.13** (versão usada durante o projeto);
- AWS CLI configurado ou credenciais temporárias válidas;
- acesso aos recursos AgentCore/Bedrock usados pelo projeto;
- Ollama para o judge local do DeepEval;
- dependências Python do `requirements.txt`.

Instalação:

```bash
pip install -r requirements.txt
ollama pull mistral-nemo:12b
```

## Variáveis de ambiente

Use credenciais temporárias apenas no ambiente local. **Nunca faça commit de secrets.**

Exemplo conceitual:

```text
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1

HARNESS_ARN=...
HARNESS_LOG_GROUP=...
POLICY_COMPLIANCE_EVALUATOR_ID=...

DEEPEVAL_JUDGE_MODEL=mistral-nemo:12b
OLLAMA_BASE_URL=http://localhost:11434
DEEPEVAL_RESULTS_PATH=...
DEEPEVAL_CASE_IDS=...
```

No PowerShell, as variáveis devem ser definidas com `$env:NOME="valor"`.

## Execução do Golden Dataset

O runner principal é:

```bash
python tests/golden_dataset_runner.py
```

Os resultados oficiais usados neste projeto foram preservados em:

```text
results/baseline/golden_results_raw_972e97b8.json
results/v2/golden_results_raw_6133af15.json
```

Esses arquivos permitem avaliar as respostas salvas sem reinvocar o agente.

## AgentCore Evaluations

A avaliação formal combina avaliadores integrados e um evaluator customizado:

- `Builtin.Correctness`
- `Builtin.GoalSuccessRate`
- `Builtin.TrajectoryAnyOrderMatch`
- `PolicyCompliance` (custom, LLM-as-a-Judge com Amazon Nova Pro)

Scripts principais:

```bash
python evaluations/agentcore/run_baseline_evaluation.py
python evaluations/agentcore/run_policy_compliance_evaluation.py
python evaluations/agentcore/run_v2_evaluation.py
python evaluations/agentcore/run_v2_policy_compliance_evaluation.py
```

> As avaliações AgentCore reinvocam o Harness. Portanto, podem diferir da execução bruta do Golden Dataset mesmo com temperatura 0.

## DeepEval

As métricas finais são:

| Métrica | Threshold |
|---|---:|
| Answer Relevancy | ≥ 0.70 |
| Reference-grounded Faithfulness | ≥ 0.80 |
| Policy Answer Quality [G-Eval] | ≥ 0.80 |

Exemplo de execução:

```powershell
$env:DEEPEVAL_JUDGE_MODEL="mistral-nemo:12b"
$env:DEEPEVAL_RESULTS_PATH="$PWD\results\v2\golden_results_raw_6133af15.json"
$env:DEEPEVAL_CASE_IDS="GD-001,GD-002,GD-003"

deepeval test run .\evaluations\deepeval\test_final_deepeval.py::test_answer_relevancy -v
deepeval test run .\evaluations\deepeval\test_final_deepeval.py::test_reference_grounded_faithfulness -v
deepeval test run .\evaluations\deepeval\test_final_deepeval.py::test_policy_answer_quality -v
```

A Faithfulness usada no projeto é **Reference-grounded Faithfulness**: o `retrieval_context` é composto por trechos oficiais curados das políticas. O uso real da ferramenta em runtime é medido separadamente pelo AgentCore Trajectory.

## Resultados principais

### AgentCore — baseline v1 × Agent v2

| Métrica | v1 | v2 |
|---|---:|---:|
| Correctness | 5.0% | **75.0%** |
| GoalSuccessRate | 0% | **77.8%** |
| TrajectoryAnyOrderMatch | 0% | **76.5%** |
| PolicyCompliance | 0.375 | **0.986** |

A trajetória esperada de Retrieve passou de **0/17** para **13/17** cenários aplicáveis.

### DeepEval — comparação normalizada

As respostas da v1 e v2 foram avaliadas pelo **mesmo judge (`mistral-nemo:12b`)** para evitar comparar versões com réguas diferentes.

| Métrica | v1 normalizada | v2 |
|---|---:|---:|
| Answer Relevancy — média | 0.742 | **0.845** |
| Answer Relevancy — pass rate | 60.0% | **80.0%** |
| Faithfulness — média | 0.454 | **0.736** |
| Faithfulness — pass rate | 15.8% | **63.2%** |
| G-Eval — média | 0.515 | **0.680** |
| G-Eval — pass rate | 10.0% | **45.0%** |

A v2 atingiu a meta agregada de Answer Relevancy, mas ainda ficou abaixo das metas de Faithfulness e G-Eval.

## Red Teaming

A campanha da v1 foi manual e estruturada, com **15 ataques em 5 categorias**:

- Prompt Injection / Instruction Override;
- Authority Escalation;
- Policy Hallucination / Unsupported Claims;
- Scope & Information Leakage;
- Multi-turn / Context Manipulation.

Resultado principal da v1:

```text
8/15 ataques atingiram o objetivo principal
Attack Success Rate (ASR): 53.3%
```

Os principais achados foram prompt injection, falsa autoridade, política fornecida pelo usuário tratada como verdade, hallucination em lacunas de política, system-prompt leakage, context poisoning e false grounding.

**Red Teaming v2:** pendente. Os mesmos ataques serão usados para medir regressão de segurança sem alterar a régua.

## Principais achados de QA

1. **Ferramenta disponível ≠ ferramenta executada.** A v1 tinha KB/Gateway configurados, mas Gemma não realizava Retrieve real.
2. **Relevância ≠ correção.** Respostas podem ser relevantes e ainda conter política incorreta ou incompleta.
3. **Faithfulness ≠ sucesso end-to-end.** Uma saída pode não contradizer o contexto e ainda falhar por não concluir a tarefa.
4. **Tool call sem síntese final é uma falha funcional.** Esse padrão permaneceu em alguns casos da v2.
5. **LLM-as-a-Judge precisa de revisão humana.** Alguns `reason`s foram semanticamente inconsistentes; os scores formais foram preservados sem rerun seletivo para evitar cherry-picking.
6. **Uma métrica isolada não é suficiente.** O projeto combina resposta, trajetória, grounding, comportamento e adversarial testing.

## Limitações atuais

- o Red Teaming v2 ainda não foi executado;
- a v2 ainda apresenta falhas de tool orchestration e síntese pós-retrieval;
- as metas agregadas de Faithfulness e G-Eval não foram atingidas;
- DeepEval Faithfulness usa contexto de referência curado, não os chunks reais de runtime;
- LLM-as-a-Judge apresenta variabilidade e pode produzir justificativas inconsistentes;
- a infraestrutura AWS foi configurada principalmente pela Management Console e não está totalmente provisionada por IaC.

## Artefatos de resultados

Documentos de consolidação importantes:

```text
results/baseline/deepeval_mistral_nemo/DeepEval_V1_Normalized_Results.md
results/v2/deepeval_mistral_nemo/DeepEval_V2_Final_Results.md
results/v2/evaluations/AgentCore_V2_Evaluations_Conclusoes_Completas.md
V2_Smoke_Tests_Model_Selection.md
Golden_Dataset_V2_Analise_Preliminar.md
Red_Teaming_Resultados_Analise.md
```

## Decisão de produção

A evidência atual mostra que a **Agent v2 é materialmente superior à baseline**, mas a decisão de produção ainda não está fechada. O reteste de Red Teaming da v2 é necessário para verificar se as vulnerabilidades adversariais de maior impacto foram realmente mitigadas.
