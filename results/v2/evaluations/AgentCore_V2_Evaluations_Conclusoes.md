# Conclusões — AgentCore Evaluations da Agent v2

## 1. Objetivo

Este documento consolida os resultados formais da **Agent v2 congelada**, avaliada no Amazon Bedrock AgentCore com a mesma régua utilizada na baseline.

Foram aplicados:

- `Builtin.Correctness`;
- `Builtin.GoalSuccessRate`;
- `Builtin.TrajectoryAnyOrderMatch`.

A execução formal do AgentCore é independente da execução bruta anterior do Golden Dataset: o runner de avaliação invoca o Harness novamente e cria novas sessões. Portanto, diferenças caso a caso entre o Golden bruto e esta avaliação são evidência de variabilidade de execução, e não de alteração da configuração congelada.

## 2. Resultado consolidado

| Métrica | Baseline v1 | Agent v2 | Variação |
|---|---:|---:|---:|
| Correctness | 1/20 (5.0%) | 15/20 (75.0%) | +70.0 p.p. |
| GoalSuccessRate | 0/18 (0.0%) | 14/18 (77.8%) | +77.8 p.p. |
| TrajectoryAnyOrderMatch | 0/17 (0.0%) | 13/17 (76.5%) | +76.5 p.p. |

### Leitura

A v2 apresentou uma melhora forte nas três métricas. O `Correctness` passou de 5,0% para 75.0%, o `GoalSuccessRate` passou de 0% para 77.8% e o `TrajectoryAnyOrderMatch` passou de 0% para 76.5%.

O ganho de trajetória é especialmente importante porque confirma que o problema central da v1 — não executar o `Retrieve` real — foi reduzido de forma substancial. Na rodada formal da v2, 13 dos 17 cenários que esperavam uso da Knowledge Base apresentaram a ferramenta esperada na trajetória.

## 3. Resultado por cenário

| Caso | Correctness | GoalSuccessRate | TrajectoryAnyOrderMatch |
|---|---|---|---|
| GD-001 | PASS | PASS | PASS |
| GD-002 | PASS | PASS | PASS |
| GD-003 | PASS | PASS | PASS |
| GD-004 | PASS | PASS | PASS |
| GD-005 | PASS | PASS | PASS |
| GD-006 | PASS | PASS | PASS |
| GD-007 | FAIL | FAIL | FAIL |
| GD-008 | PASS | PASS | PASS |
| GD-009 | PASS | PASS | PASS |
| GD-010 | FAIL | FAIL | FAIL |
| GD-011 | PASS | PASS | PASS |
| GD-012 | FAIL | FAIL | FAIL |
| GD-013 | PASS | PASS | PASS |
| GD-014 | PASS | PASS | PASS |
| GD-015 | PASS | PASS | PASS |
| GD-016 | FAIL / FAIL | FAIL | FAIL |
| GD-017 | PASS / PASS | PASS | PASS |
| GD-018 | PASS | PASS | N/A |

## 4. Falhas residuais

As falhas formais ficaram concentradas em quatro cenários: `GD-007`, `GD-010`, `GD-012`, `GD-016`.

- `GD-007`: prazo de submissão de despesas;
- `GD-010`: valor-limite de recibo em R$ 50;
- `GD-012`: abstention para coworking;
- `GD-016`: fluxo multi-turn de hotel doméstico/internacional.

Nos quatro casos, o padrão dominante foi o mesmo observado durante smoke tests e na execução bruta: a interação com a ferramenta não resultou em uma resposta final completa. Em alguns casos, o modelo iniciou ou textualizou o tool call, mas não concluiu o fluxo com a informação solicitada.

## 5. Observação sobre não determinismo

Os resultados desta avaliação formal não são idênticos aos resultados brutos do Golden Dataset executado imediatamente antes. Isso ocorre porque o AgentCore Evaluation realizou novas invocações do Harness. Apesar de `temperature = 0`, o comportamento de agentes com tool use pode continuar apresentando variação de execução.

Esse ponto é relevante para o relatório: a v2 melhorou claramente a capacidade de retrieval, mas ainda apresenta instabilidade na orquestração da ferramenta. A existência de resultados diferentes em execuções separadas deve ser registrada como limitação residual, e não eliminada por novas tentativas.

## 6. Conclusão

A Agent v2 apresentou melhora mensurável e substancial em relação à baseline. A principal mudança foi a passagem de uma agente que não executava `Retrieve` nos cenários esperados para uma agente que utilizou a ferramenta corretamente em 76.5% dos cenários avaliados por trajetória.

Ao mesmo tempo, os resultados mostram que a correção não eliminou totalmente a falha de tool calling. Os quatro cenários residuais devem permanecer registrados como limitações da v2 e serão importantes na comparação final, no DeepEval e no reteste de Red Teaming.

## 7. Próxima etapa

Executar o evaluator customizado `PolicyCompliance` usando a mesma configuração, o mesmo evaluator ID e a mesma régua aplicada à baseline, para preservar comparabilidade.