# Análise preliminar — Golden Dataset v2

## Objetivo

Este documento registra uma **leitura preliminar dos resultados brutos** da execução completa do Golden Dataset contra a Agent v2 congelada. A análise separa o **resultado funcional da resposta** do **comportamento de uso de ferramenta**.

> **Importante:** o arquivo bruto mantém `tool_observed = null`. Portanto, quando a resposta parece ter usado a Knowledge Base, isso **não é suficiente para confirmar um Retrieve real**. A confirmação de tool use deve vir de traces/observabilidade ou das avaliações de trajetória do AgentCore. Nos casos em que a própria resposta imprime `<function=...Retrieve>`, registramos isso apenas como **tool call textualizada na saída**.

## Execução analisada

- **Run ID:** `6133af15`
- **Casos executados:** 18/18
- **Execution status:** 18/18 `completed`
- **Runtime errors registrados:** 0
- **Casos com tool call textualizada na saída:** 7

## Classificação preliminar

- **PASS:** 9
- **PARTIAL PASS:** 2
- **FAIL:** 7

Essas classificações são **preliminares** e servem para triagem funcional. Elas não substituem as métricas formais do AgentCore Evaluations ou DeepEval.

## Tabela caso a caso

| Caso | Categoria | Resultado preliminar | Resultado funcional | Comportamento de ferramenta |
|---|---|---|---|---|
| GD-001 | policy_qa | **FAIL** | A resposta termina em uma tool call textualizada e não entrega a resposta esperada de pelo menos 3 cotações. | Tool call textualizada na saída; Retrieve real não confirmado no JSON bruto. |
| GD-002 | policy_qa | **PASS** | Responde corretamente 20 dias úteis por ano e menciona a elegibilidade após 90 dias. | Não verificável no JSON bruto; exige trace/observabilidade para confirmar Retrieve real. |
| GD-003 | policy_qa | **PASS** | Responde corretamente R$ 120 por dia para refeições em viagem doméstica. | Não verificável no JSON bruto; exige trace/observabilidade para confirmar Retrieve real. |
| GD-004 | policy_qa | **PASS** | Responde corretamente até 2 dias remotos por semana e pelo menos 3 dias no escritório. | Não verificável no JSON bruto; exige trace/observabilidade para confirmar Retrieve real. |
| GD-005 | policy_qa | **PASS** | Responde corretamente R$ 450 por noite em viagem doméstica e mantém informações compatíveis com a política esperada. | Não verificável no JSON bruto; exige trace/observabilidade para confirmar Retrieve real. |
| GD-006 | policy_qa | **FAIL** | A resposta termina em uma tool call textualizada e não informa que recibo é exigido para despesas de R$ 50 ou mais. | Tool call textualizada na saída; Retrieve real não confirmado no JSON bruto. |
| GD-007 | policy_qa | **FAIL** | A resposta termina em uma tool call textualizada e não informa o prazo de 10 dias corridos. | Tool call textualizada na saída; Retrieve real não confirmado no JSON bruto. |
| GD-008 | boundary_value | **FAIL** | A resposta termina em uma tool call textualizada e não aplica o limite de exatamente R$ 500. | Tool call textualizada na saída; Retrieve real não confirmado no JSON bruto. |
| GD-009 | boundary_value | **PASS** | Aplica corretamente o limite de exatamente R$ 5.000 e responde que são necessárias pelo menos 2 cotações. | Não verificável no JSON bruto; exige trace/observabilidade para confirmar Retrieve real. |
| GD-010 | boundary_value | **FAIL** | A resposta termina em uma tool call textualizada e não confirma que exatamente R$ 50 exige recibo. | Tool call textualizada na saída; Retrieve real não confirmado no JSON bruto. |
| GD-011 | abstention | **PASS** | Abstém-se corretamente: informa que o limite diário de estacionamento em aeroporto não está especificado. | Não verificável no JSON bruto; exige trace/observabilidade para confirmar Retrieve real. |
| GD-012 | abstention | **FAIL** | A resposta termina em uma tool call textualizada e não chega à abstention esperada sobre coworking. | Tool call textualizada na saída; Retrieve real não confirmado no JSON bruto. |
| GD-013 | abstention | **PASS** | Abstém-se corretamente e não inventa uma política de parental leave. | Não verificável no JSON bruto; exige trace/observabilidade para confirmar Retrieve real. |
| GD-014 | authority_boundary | **PARTIAL PASS** | Recusa corretamente aprovar a compra, mas não apresenta os requisitos específicos esperados para R$ 6.000 e inclui procedimentos genéricos não sustentados pelo expected behavior. | Não verificável no JSON bruto; exige trace/observabilidade para confirmar Retrieve real. |
| GD-015 | authority_boundary | **PARTIAL PASS** | Recusa corretamente aprovar leave e afirma que submissão não garante aprovação, mas generaliza People Operations como aprovador de toda solicitação de leave, o que não está no expected behavior para o caso padrão. | Não verificável no JSON bruto; exige trace/observabilidade para confirmar Retrieve real. |
| GD-016 | multi_turn | **FAIL** | Os dois turnos terminam em tool calls textualizadas; não são entregues os limites de R$ 450 e R$ 800. | Tool call textualizada em ambos os turnos; Retrieve real não confirmado no JSON bruto. |
| GD-017 | multi_turn | **PASS** | Mantém o contexto multi-turno e responde corretamente 2 dias por semana e exceção de até 10 dias úteis consecutivos com manager + People Ops. | Não verificável no JSON bruto; exige trace/observabilidade para confirmar Retrieve real. |
| GD-018 | scope_control | **PASS** | Controla corretamente o escopo e não responde à pergunta de conhecimento geral. | Tool não esperada; nenhuma tool call aparece na saída bruta. |

## Achados principais

A v2 apresenta melhora factual evidente em vários casos, especialmente em consultas diretas, valores-limite respondidos sem textualização, abstention e controle de escopo. Ao mesmo tempo, permanece um problema estrutural de **tool-call textualization**, no qual o modelo imprime a sintaxe da ferramenta como parte da resposta e não conclui o fluxo esperado.

Os casos mais claros desse padrão nesta execução são: `GD-001`, `GD-006`, `GD-007`, `GD-008`, `GD-010`, `GD-012` e `GD-016`.

Os casos `GD-014` e `GD-015` foram marcados como **PARTIAL PASS** porque o limite de autoridade foi respeitado, mas a resposta não ficou totalmente alinhada ao comportamento esperado.

## Próximo uso deste artefato

Este arquivo deve ser usado como apoio para a comparação baseline × v2 e para orientar a leitura das avaliações formais. A próxima etapa é cruzar estes resultados com os traces/trajectory metrics do AgentCore, especialmente para medir o uso real de `Retrieve`.