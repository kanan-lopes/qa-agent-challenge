# DeepEval Reference Contexts — Methodology Note

## Purpose

`reference_contexts.json` contains curated policy evidence for the 18 Golden Dataset cases used in the Asteria Systems Employee Policy Assistant project.

For the Agent v1 baseline, these contexts must be interpreted as **reference contexts**, not runtime retrieval contexts.

## Why this is necessary

The Agent v1 baseline did not execute the Knowledge Base `Retrieve` operation in the policy-dependent Golden Dataset cases. As a result, there are no genuine runtime-retrieved chunks that can be supplied to DeepEval as evidence of what the model actually received.

To avoid fabricating runtime evidence while still measuring whether the generated answer is supported by the official policies, the project uses these curated policy excerpts for a metric reported as:

**Reference-grounded Faithfulness**

This answers: *Is the agent's response supported by the official policy content relevant to the test case?*

It does not answer: *Is the response faithful to the chunks actually retrieved by the Agent v1 runtime?*

Actual Knowledge Base use is measured separately through AgentCore trajectory/tool-use evaluation.

## Negative / abstention cases

GD-011, GD-012, and GD-013 use `context_kind = "negative_reference_summary"`.

For these cases, the expected behavior depends on the absence of a rule in the provided policy corpus. Their reference contexts therefore include a concise statement that the relevant provision is not specified in the supplied policies. These are curated summaries of policy coverage, not verbatim runtime retrieval chunks.

## Out-of-scope case

GD-018 is excluded from Faithfulness because it intentionally tests scope control with a general-knowledge question and has no relevant company-policy context.

## Agent v2

If Agent v2 successfully executes `Retrieve`, the project can add a separate **Runtime RAG Faithfulness** evaluation using the chunks that were actually retrieved. The reference-grounded metric can remain unchanged for direct v1 × v2 comparison.
