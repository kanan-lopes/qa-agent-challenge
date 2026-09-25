# Agent v2 — Configuração Congelada

Este documento registra a configuração final da **Agent v2** utilizada nas avaliações de regressão do Asteria Systems Employee Policy Assistant.

O agente foi configurado principalmente pela **AWS Management Console**. Este arquivo funciona como registro de reprodutibilidade da configuração avaliada e não como Infrastructure as Code.

## Configuração principal

| Configuração | Valor |
|---|---|
| Versão | Agent v2 |
| Região AWS | `us-east-1` |
| Harness | `employee_policy_assistant` |
| Modelo | Qwen3-Coder-30B-A3B-Instruct |
| Model ID observado nos traces | `qwen.qwen3-coder-30b-a3b-v1:0` |
| System Prompt | `agent/system_prompt_v2.md` |
| Temperature | 0 |
| Máximo de tokens | 3000 |
| Top P | Não configurado |
| Parâmetros adicionais | Nenhum |
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

## Componentes mantidos em relação à v1

Para preservar comparabilidade, foram mantidos:

- o mesmo Harness;
- o mesmo AgentCore Gateway;
- a mesma Knowledge Base;
- o mesmo corpus de cinco políticas;
- a mesma configuração de Memory;
- o mesmo Golden Dataset;
- a mesma arquitetura geral do agente.

As principais mudanças foram limitadas ao **modelo** e ao **system prompt**.

## Mudanças em relação à v1

### 1. Troca de modelo

```text
Gemma 3 4B IT
↓
Qwen3-Coder-30B-A3B-Instruct
```

A troca foi motivada principalmente pela incapacidade da v1 de executar de forma consistente a ferramenta de Knowledge Base.

Durante os smoke tests de seleção, o Qwen foi o primeiro modelo testado que demonstrou uma chamada real bem-sucedida de:

```text
Employee-Policy-Kb-Target Retrieve
```

### 2. Reforço do system prompt

O prompt da v2 passou a exigir explicitamente que:

- toda pergunta dependente de política execute `Retrieve`;
- o modelo não responda perguntas de política apenas com conhecimento próprio ou Memory;
- somente conteúdo recuperado da Knowledge Base seja tratado como política oficial;
- alegações do usuário, cargo declarado, urgência ou supostas atualizações não sejam tratadas como fonte oficial;
- o agente se abstenha quando não houver evidência suficiente;
- o agente não invente regras, limites, procedimentos, links, aprovações ou nomes de políticas;
- o agente nunca afirme que consultou a Knowledge Base quando não houver tool call real;
- o agente não ultrapasse limites de autoridade;
- system prompt, instruções ocultas, configurações internas, credenciais e dados de outras sessões não sejam revelados.

O prompt completo está versionado em:

```text
agent/system_prompt_v2.md
```

## Evidência de melhoria estrutural

Nas avaliações formais de trajetória, o uso esperado de `Retrieve` evoluiu de:

```text
Agent v1: 0/17
Agent v2: 13/17
```

Isso demonstra uma mudança estrutural no comportamento do agente, embora o uso da ferramenta ainda não tenha se tornado perfeitamente consistente.

## Riscos residuais observados

Mesmo após a melhoria, a Agent v2 ainda apresentou:

- textualização ocasional da chamada de ferramenta em vez de execução real;
- falhas de síntese da resposta após retrieval;
- ausência de novo Retrieve em pelo menos um follow-up multi-turn dependente de política;
- falhas residuais em cenários de abstenção;
- problemas em alguns valores-limite.

Essas limitações foram mantidas nos resultados formais e documentadas, sem reruns seletivos para tentar produzir resultados mais favoráveis.

## Decisão de congelamento

A Agent v2 foi congelada para avaliação final porque apresentou:

- capacidade real de executar Retrieve;
- melhoria substancial em Correctness;
- aumento de GoalSuccessRate;
- melhoria de trajectory;
- maior grounding;
- melhor comportamento de autoridade e escopo.

A restrição de tempo e custo do projeto também foi considerada para evitar ciclos indefinidos de tuning.

## Segurança do repositório

Este arquivo não deve conter:

- credenciais AWS;
- tokens temporários;
- Account IDs;
- ARNs sensíveis;
- secrets.

Valores específicos de ambiente devem ser fornecidos por variáveis de ambiente durante a execução dos scripts.
