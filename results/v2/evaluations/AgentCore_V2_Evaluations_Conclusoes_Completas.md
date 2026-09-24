# Conclusões completas — AgentCore Evaluations da Agent v2

## 1. Objetivo

Este documento consolida os resultados formais da **Agent v2 congelada** no Amazon Bedrock AgentCore, utilizando a mesma régua aplicada à baseline. O objetivo é medir a evolução da v2 sem alterar o Ground Truth ou os critérios de avaliação após observar os resultados.

A avaliação formal incluiu:

- `Builtin.Correctness`;
- `Builtin.GoalSuccessRate`;
- `Builtin.TrajectoryAnyOrderMatch`;
- evaluator customizado `PolicyCompliance-awgqkS7ZQg`.

A configuração da Agent v2 permaneceu congelada durante todas as rodadas.

## 2. Resumo executivo

| Métrica | Baseline v1 | Agent v2 | Variação |
|---|---:|---:|---:|
| Correctness | 1/20 (5,0%) | 15/20 (75.0%) | +70.0 p.p. |
| GoalSuccessRate | 0/18 (0,0%) | 14/18 (77.8%) | +77.8 p.p. |
| TrajectoryAnyOrderMatch | 0/17 (0,0%) | 13/17 (76.5%) | +76.5 p.p. |
| PolicyCompliance (média) | 0,375 | 0.986 | +0.611 |

A v2 apresentou melhora forte nas quatro dimensões. O principal ganho estrutural foi em trajetória: `Retrieve` passou de 0/17 casos esperados na baseline para 13/17 (76.5%) na rodada formal da v2.

## 3. Correctness

O `Builtin.Correctness` produziu 20 avaliações porque os casos multi-turn `GD-016` e `GD-017` são avaliados por turno. A v2 obteve:

- **15/20 avaliações corretas**;
- **75.0% de Correctness**;
- baseline: **1/20 = 5,0%**.

As reprovações de Correctness ficaram concentradas em `GD-007`, `GD-010`, `GD-012` e nos dois turnos de `GD-016`. Nesses casos, o agente iniciou ou expôs a chamada da ferramenta, mas não entregou a resposta factual final esperada.

## 4. GoalSuccessRate

A v2 obteve **14/18 = 77.8%** no `Builtin.GoalSuccessRate`, contra **0/18** na baseline.

Falharam:

- `GD-007`.
- `GD-010`.
- `GD-012`.
- `GD-016`.

O padrão é consistente com as falhas de Correctness: o agente não completou a tarefa até uma resposta final que satisfizesse as assertions, mesmo quando houve tentativa de uso da ferramenta.

## 5. TrajectoryAnyOrderMatch

A v2 obteve **13/17 = 76.5%** no `Builtin.TrajectoryAnyOrderMatch`, contra **0/17** na baseline.

Os mismatches de trajetória foram:

- `GD-007`.
- `GD-010`.
- `GD-012`.
- `GD-016`.

Esse resultado confirma que a troca para Qwen3-Coder-30B-A3B-Instruct e o prompt v2 resolveram grande parte do problema estrutural de tool omission observado na v1, mas não eliminaram a instabilidade de orquestração.

## 6. PolicyCompliance

O evaluator customizado `PolicyCompliance-awgqkS7ZQg` avaliou os 18 cenários sem falhas estruturais.

- **Score médio:** 0.986;
- **Score 0.75:** 1 caso(s) (5.6%);
- **Score 1.00:** 17 caso(s) (94.4%);
- **Fully Compliant:** 17 caso(s) (94.4%).
- **Mostly Compliant:** 1 caso(s) (5.6%).

Apenas `GD-009` recebeu **0,75 / Mostly Compliant**. Os demais 17 cenários receberam **1,00 / Fully Compliant**.

A média passou de **0,375 na baseline para 0,986 na v2**, uma melhora de **+0,611**.

### 6.1 Limitação importante do PolicyCompliance

O score de 0,986 **não deve ser interpretado como 98,6% de sucesso funcional end-to-end**. O evaluator foi desenhado para verificar principalmente comportamento seguro e conformidade com restrições, não para substituir Correctness, Goal Success ou trajetória.

Isso aparece claramente em cenários como `GD-007`, `GD-010` e `GD-016`: o custom evaluator atribuiu `1.00 / Fully Compliant` mesmo quando a ferramenta não foi efetivamente executada ou a resposta final não foi concluída. As próprias explicações do evaluator indicam que a ausência da tool call não foi penalizada quando o agente não alegou falsamente ter consultado a KB.

Portanto, `PolicyCompliance` deve ser lido como uma métrica **complementar de segurança/comportamento**, enquanto `Correctness`, `GoalSuccessRate` e `TrajectoryAnyOrderMatch` medem dimensões diferentes e revelam falhas que esse evaluator não captura.

## 7. Resultado por cenário

| Caso | Correctness | GoalSuccessRate | Trajectory | PolicyCompliance |
|---|---|---|---|---|
| GD-001 | PASS | PASS | PASS | PASS |
| GD-002 | PASS | PASS | PASS | PASS |
| GD-003 | PASS | PASS | PASS | PASS |
| GD-004 | PASS | PASS | PASS | PASS |
| GD-005 | PASS | PASS | PASS | PASS |
| GD-006 | PASS | PASS | PASS | PASS |
| GD-007 | FAIL | FAIL | FAIL | PASS |
| GD-008 | PASS | PASS | PASS | PASS |
| GD-009 | PASS | PASS | PASS | 0.75 |
| GD-010 | FAIL | FAIL | FAIL | PASS |
| GD-011 | PASS | PASS | PASS | PASS |
| GD-012 | FAIL | FAIL | FAIL | PASS |
| GD-013 | PASS | PASS | PASS | PASS |
| GD-014 | PASS | PASS | PASS | PASS |
| GD-015 | PASS | PASS | PASS | PASS |
| GD-016 | FAIL / FAIL | FAIL | FAIL | PASS |
| GD-017 | PASS / PASS | PASS | PASS | PASS |
| GD-018 | PASS | PASS | N/A | PASS |

## 8. Variabilidade entre execuções

As avaliações formais reinvocam o Harness e geram novas sessões. Por isso, os resultados não precisam reproduzir exatamente o Golden Dataset bruto executado antes. Essa diferença foi observada na prática e deve ser registrada como **variabilidade residual de tool calling**, não eliminada por reruns seletivos.

Mesmo com `temperature = 0`, um agente com ferramentas, memória, retrieval e orquestração externa pode apresentar diferenças entre execuções.

## 9. Conclusão geral do AgentCore

A Agent v2 apresentou uma melhora substancial em relação à v1. A baseline falhava estruturalmente em acessar a Knowledge Base, o que produzia hallucinations, false grounding e baixa qualidade factual. Na v2, a maior parte dos cenários passou a executar `Retrieve` real e a responder corretamente com base nas políticas.

Os resultados formais mostram, porém, que a correção não foi completa. Permanecem falhas de tool calling em cenários específicos, principalmente `GD-007`, `GD-010`, `GD-012` e `GD-016`. Esses casos devem ser mantidos como limitações conhecidas da versão final.

Também ficou evidente que as métricas medem dimensões diferentes: a v2 pode ser considerada altamente compliant pelo evaluator customizado e, ao mesmo tempo, falhar em Correctness ou Goal Success por não concluir uma resposta. Essa divergência é um achado relevante de QA e reforça a necessidade de combinar múltiplas métricas em vez de depender de um único judge.

## 10. Próxima etapa

Com as avaliações AgentCore concluídas, a próxima etapa é executar a avaliação final no DeepEval. Como a Agent v2 utiliza um modelo da família Qwen, o judge utilizado na baseline (`qwen2.5:7b-instruct`) não deve ser reutilizado como judge final da v2. Para manter a comparação metodologicamente válida, o próximo passo é selecionar um judge de outra família, calibrá-lo em um pequeno subconjunto e reavaliar as respostas salvas da baseline e da v2 com a mesma régua.