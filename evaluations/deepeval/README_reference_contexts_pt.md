# Contextos de Referência do DeepEval — Nota Metodológica

## Objetivo

O arquivo `reference_contexts.json` contém evidências de política selecionadas para os 18 casos do Golden Dataset utilizados no projeto **Asteria Systems Employee Policy Assistant**.

Na baseline do Agent v1, esses conteúdos devem ser interpretados como **contextos de referência**, e não como contextos recuperados em runtime.

## Por que isso é necessário

Na baseline, o Agent v1 não executou a operação `Retrieve` da Knowledge Base nos casos do Golden Dataset que dependiam das políticas internas.

Como consequência, não existem chunks realmente recuperados em runtime que possam ser fornecidos ao DeepEval como evidência do conteúdo que o modelo de fato recebeu durante a execução.

Para evitar fabricar uma evidência de retrieval e, ao mesmo tempo, ainda conseguir medir se a resposta produzida pelo agente é sustentada pelas políticas oficiais, o projeto utiliza trechos selecionados das políticas como contexto de referência.

Essa avaliação será reportada como:

**Reference-grounded Faithfulness**

Ela responde à seguinte pergunta:

> A resposta produzida pelo agente é sustentada pelo conteúdo oficial da política relevante ao caso de teste?

Ela **não** responde:

> A resposta é fiel aos chunks realmente recuperados pelo Agent v1 em runtime?

O uso efetivo da Knowledge Base é medido separadamente pelas métricas de trajetória e uso de ferramentas do AgentCore.

## Relação com o problema de Retrieve

A ausência de `retrieval_context` real não é a causa principal do problema. Ela é uma consequência da falha de tool use observada no Agent v1.

O fluxo esperado seria:

`Pergunta do usuário → chamada Retrieve → chunks da Knowledge Base → resposta do modelo`

Na baseline, o comportamento observado foi:

`Pergunta do usuário → modelo não chama Retrieve → nenhum chunk é recuperado → resposta é produzida sem grounding real da KB`

Portanto, o problema principal é que o Agent v1 **não inicia a consulta à Knowledge Base**, mesmo quando a pergunta depende claramente das políticas internas.

## Casos negativos / de abstenção

Os casos `GD-011`, `GD-012` e `GD-013` utilizam:

`context_kind = "negative_reference_summary"`

Nesses casos, o comportamento esperado depende justamente da **ausência de uma regra específica nas políticas fornecidas**.

Por isso, os contextos de referência incluem uma indicação concisa de que aquela informação não está especificada no corpus de políticas.

Esses textos são resumos curados da cobertura documental e **não representam chunks recuperados pelo Agent v1**.

Exemplos:

- `GD-011`: a política não especifica limite diário de reembolso para estacionamento em aeroporto.
- `GD-012`: as políticas não especificam reembolso de coworking.
- `GD-013`: a política não especifica licença parental.

## Caso fora de escopo

O caso `GD-018` é excluído da métrica de Faithfulness.

Ele testa controle de escopo por meio de uma pergunta de conhecimento geral, sem relação com as políticas internas da Asteria Systems.

Por isso, não existe um contexto corporativo relevante que possa ser utilizado de forma coerente em uma comparação de Faithfulness.

Esse caso continuará sendo avaliado por outras métricas, especialmente as relacionadas a qualidade da resposta e controle de escopo.

## Como interpretar os resultados da baseline

Na baseline do Agent v1, teremos duas evidências diferentes e complementares:

- **Trajectory / tool-use evaluation:** verifica se o agente realmente executou `Retrieve`.
- **Reference-grounded Faithfulness:** verifica se a resposta é sustentada pela política oficial de referência.

Isso permite separar duas perguntas distintas:

1. O agente realmente consultou a Knowledge Base?
2. A resposta produzida está de acordo com o conteúdo oficial da política?

Essa separação é importante porque uma resposta pode, por coincidência ou conhecimento paramétrico do modelo, estar correta mesmo sem ter utilizado a KB.

## Agent v2

Se o Agent v2 passar a executar `Retrieve` corretamente, será possível adicionar uma avaliação separada de:

**Runtime RAG Faithfulness**

Nesse caso, a métrica poderá utilizar os chunks que foram realmente recuperados durante a execução do agente.

A métrica de **Reference-grounded Faithfulness** poderá ser mantida em paralelo para permitir comparação direta entre Agent v1 e Agent v2.

Assim, na v2 será possível distinguir:

- se o agente consultou a KB;
- se recuperou conteúdo relevante;
- se a resposta foi fiel ao conteúdo realmente recuperado;
- se a resposta permaneceu consistente com a política oficial de referência.
