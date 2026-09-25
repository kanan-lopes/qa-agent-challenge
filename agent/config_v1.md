# Agent v1 — Configuração Congelada

Este documento registra a configuração da **baseline (Agent v1)** do Asteria Systems Employee Policy Assistant.

O agente foi configurado principalmente pela **AWS Management Console**. Este arquivo funciona como registro de reprodutibilidade da configuração utilizada nos testes e não como Infrastructure as Code.

## Configuração principal

| Configuração | Valor |
|---|---|
| Versão | Agent v1 / Baseline |
| Região AWS | `us-east-1` |
| Harness | `employee_policy_assistant` |
| Modelo | Gemma 3 4B IT v1 |
| Model ID | `google.gemma-3-4b-it` |
| System Prompt | `agent/system_prompt_v1.md` |
| Máximo de tokens | 4096 |
| Parâmetros do modelo | Padrões do Console |
| Máximo de iterações | 8 |
| Timeout | 180 segundos |
| Gateway | `employee-policy-gateway` |
| Knowledge Base | `employee-policy-s3` |
| Gateway Target | `employee-policy-kb-target` |
| Ferramenta de KB esperada | `employee-policy-kb-target___Retrieve` |
| Memory | Habilitada |
| Estratégias de Memory | Semantic + Summary |
| Expiração dos eventos brutos | 30 dias |
| Observabilidade | AgentCore / CloudWatch habilitados |

## Ciclo de vida do Harness

- **Idle timeout:** 15 minutos
- **Maximum lifecycle:** 8 horas

## Corpus utilizado

A Knowledge Base utiliza cinco documentos de política fictícios:

- `travel_policy.md`
- `expense_policy.md`
- `remote_work_policy.md`
- `leave_policy.md`
- `procurement_policy.md`

Esses documentos representam a fonte oficial de políticas da Asteria Systems dentro do projeto.

## Comportamento esperado

Para perguntas dependentes de política, a trajetória esperada incluía uma chamada real da ferramenta de Knowledge Base:

```text
employee-policy-kb-target___Retrieve
```

O agente deveria:

- consultar a Knowledge Base antes de responder perguntas sobre políticas;
- responder com base nos documentos recuperados;
- se abster quando a informação não estivesse especificada;
- respeitar limites de autoridade;
- permanecer dentro do escopo de Employee Policy Assistant.

## Problema principal observado

Durante a baseline, o Gemma 3 4B frequentemente conseguia descobrir a ferramenta por meio de:

```text
mcp tools/list
```

mas não executava uma chamada real de `Retrieve`.

Isso levou a respostas geradas sem grounding efetivo na Knowledge Base e esteve associado a:

- alucinação factual;
- alucinação de política ou fonte;
- falsa alegação de grounding;
- falha de abstenção;
- respostas inconsistentes entre execuções.

## Distinções importantes na observabilidade

Os seguintes eventos **não** foram considerados evidência de consulta à Knowledge Base:

```text
mcp tools/list
```

Esse evento indica apenas descoberta/listagem das ferramentas disponíveis.

```text
RetrieveMemoryRecords
```

Esse evento pertence ao **AgentCore Memory**, e não à Knowledge Base corporativa.

Uma chamada válida da Knowledge Base foi identificada por operações equivalentes a:

```text
tools/call
Employee-Policy-Kb-Target Retrieve
employee-policy-kb-target___Retrieve
```

## Papel da v1 no projeto

A Agent v1 foi congelada como baseline antes da implementação das mitigações.

Seus resultados foram preservados para permitir comparação direta com a Agent v2 em:

- Golden Dataset;
- AgentCore Evaluations;
- DeepEval;
- Red Teaming v1;
- traces e observabilidade.

## Segurança do repositório

Este arquivo não deve conter:

- credenciais AWS;
- tokens temporários;
- Account IDs;
- ARNs sensíveis;
- secrets.

Esses valores devem ser fornecidos externamente por variáveis de ambiente quando necessários.
