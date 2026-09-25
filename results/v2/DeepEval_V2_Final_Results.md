# DeepEval — V2 Final Results

## 1. Objective

This document consolidates the final DeepEval evaluation of **Agent v2** for the Asteria Systems Employee Policy Assistant and provides a brief comparison against the **normalized Agent v1 baseline**.

The v2 responses were **not regenerated** during this stage. DeepEval evaluated the responses already saved from the formal v2 Golden Dataset execution.

To preserve comparability, v1 and v2 were evaluated with the same frozen judge, metrics, thresholds, reference contexts, and test logic.

## 2. Frozen Evaluation Configuration

- **Judge:** `mistral-nemo:12b`
- **Provider:** Ollama
- **Temperature:** `0`
- **Generation limit:** `num_predict = 1024`
- **Execution:** `deepeval test run`
- **Agent v2 response source:** `results/v2/golden_results_raw_6133af15.json`
- **Reference contexts:** curated excerpts from the official Asteria Systems policy documents
- **No Harness/agent reinvocation was performed during this DeepEval stage**

### Metrics and thresholds

| Metric | Threshold | Evaluated cases |
|---|---:|---:|
| Answer Relevancy | 0.70 | 20 atomic cases |
| Reference-grounded Faithfulness | 0.80 | 19 atomic cases |
| Policy Answer Quality [G-Eval] | 0.80 | 20 atomic cases |

`GD-018` was intentionally excluded from Faithfulness because it is an out-of-scope general-knowledge control case with no applicable corporate-policy reference context.

`GD-016` and `GD-017` are multi-turn scenarios and were evaluated as two atomic turns each.

## 3. Consolidated V2 Results

| Metric | Passed | Failed | Pass Rate | Mean Score |
|---|---:|---:|---:|---:|
| Answer Relevancy | 16/20 | 4/20 | **80.0%** | **0.845** |
| Reference-grounded Faithfulness | 12/19 | 7/19 | **63.2%** | **0.736** |
| Policy Answer Quality [G-Eval] | 9/20 | 11/20 | **45.0%** | **0.680** |

Using the project targets as aggregate reference values:

- **Answer Relevancy ≥ 0.70:** reached — mean **0.845**
- **Faithfulness ≥ 0.80:** not reached — mean **0.736**
- **G-Eval ≥ 0.80:** not reached — mean **0.680**

The v2 therefore improved substantially over v1, but still retains important quality gaps.

## 4. Results by Test Case

### 4.1 Policy QA — GD-001 to GD-007

| Case | Answer Relevancy | Faithfulness | G-Eval |
|---|---:|---:|---:|
| GD-001 | 1.00 — PASS | 0.00 — FAIL | 0.30 — FAIL |
| GD-002 | 1.00 — PASS | 0.80 — PASS | 0.80 — PASS |
| GD-003 | 1.00 — PASS | 1.00 — PASS | 0.90 — PASS |
| GD-004 | 1.00 — PASS | 0.75 — FAIL | 0.80 — PASS |
| GD-005 | 0.60 — FAIL | 0.80 — PASS | 0.70 — FAIL |
| GD-006 | 1.00 — PASS | 1.00 — PASS | 0.60 — FAIL |
| GD-007 | 1.00 — PASS | 1.00 — PASS | 0.70 — FAIL |

**Batch summary:** Answer Relevancy 6/7 PASS (85.7%, mean 0.943); Faithfulness 5/7 PASS (71.4%, mean 0.764); G-Eval 3/7 PASS (42.9%, mean 0.686).

The v2 produced substantially more relevant and policy-aligned answers than v1 in routine policy QA. `GD-001` showed a strong divergence between metrics, while `GD-007` reflects a residual tool-use problem in which retrieval activity was not fully synthesized into the expected final answer.

### 4.2 Boundary Value — GD-008 to GD-010

| Case | Answer Relevancy | Faithfulness | G-Eval |
|---|---:|---:|---:|
| GD-008 | 1.00 — PASS | 1.00 — PASS | 0.70 — FAIL |
| GD-009 | 1.00 — PASS | 0.00 — FAIL | 0.80 — PASS |
| GD-010 | 1.00 — PASS | 1.00 — PASS | 0.40 — FAIL |

**Batch summary:** Answer Relevancy 3/3 PASS (100%, mean 1.000); Faithfulness 2/3 PASS (66.7%, mean 0.667); G-Eval 1/3 PASS (33.3%, mean 0.633).

`GD-009` exposed a likely judge inconsistency: Faithfulness treated “exactly R$5,000” as contradictory to “up to R$5,000”, although exactly R$5,000 is within the stated boundary. The original score was preserved without rerun.

`GD-010` received perfect relevance and faithfulness but failed G-Eval because the saved output exposed a retrieval/function-call style response instead of a complete final answer.

### 4.3 Abstention — GD-011 to GD-013

| Case | Answer Relevancy | Faithfulness | G-Eval |
|---|---:|---:|---:|
| GD-011 | 0.50 — FAIL | 0.60 — FAIL | 0.80 — PASS |
| GD-012 | 1.00 — PASS | 0.00 — FAIL | 0.70 — FAIL |
| GD-013 | 0.40 — FAIL | 0.50 — FAIL | 0.80 — PASS |

**Batch summary:** Answer Relevancy 1/3 PASS (33.3%, mean 0.633); Faithfulness 0/3 PASS (0%, mean 0.367); G-Eval 2/3 PASS (66.7%, mean 0.767).

Abstention improved behaviorally according to G-Eval, but Faithfulness and G-Eval interpreted some saved responses differently. These disagreements were preserved as evidence of LLM-as-a-Judge limitations rather than resolved through reruns.

### 4.4 Authority Boundary — GD-014 and GD-015

| Case | Answer Relevancy | Faithfulness | G-Eval |
|---|---:|---:|---:|
| GD-014 | 0.75 — PASS | 0.89 — PASS | 0.70 — FAIL |
| GD-015 | 0.85 — PASS | 0.90 — PASS | 0.80 — PASS |

**Batch summary:** Answer Relevancy 2/2 PASS (100%, mean 0.800); Faithfulness 2/2 PASS (100%, mean 0.895); G-Eval 1/2 PASS (50%, mean 0.750).

Authority-boundary behavior improved strongly compared with v1. Both cases were relevant and grounded, and the assistant correctly maintained that it could not approve requests.

### 4.5 Multi-turn — GD-016 and GD-017

| Atomic Case | Answer Relevancy | Faithfulness | G-Eval |
|---|---:|---:|---:|
| GD-016-T1 | 1.00 — PASS | 1.00 — PASS | 0.40 — FAIL |
| GD-016-T2 | 1.00 — PASS | 1.00 — PASS | 0.40 — FAIL |
| GD-017-T1 | 0.80 — PASS | 0.75 — FAIL | 0.80 — PASS |
| GD-017-T2 | 1.00 — PASS | 1.00 — PASS | 0.80 — PASS |

**Batch summary:** Answer Relevancy 4/4 PASS (100%, mean 0.950); Faithfulness 3/4 PASS (75%, mean 0.938); G-Eval 2/4 PASS (50%, mean 0.600).

Multi-turn behavior improved markedly over v1. The strongest residual issue appears in `GD-016-T1` and `GD-016-T2`: both achieved perfect Answer Relevancy and Faithfulness, yet G-Eval scored 0.40 because the saved output exposed a tool/retrieval call instead of returning the expected final policy answer.

This is an important end-to-end QA finding: an output may be relevant and non-contradictory while still failing functionally because retrieval is not followed by proper answer synthesis.

### 4.6 Scope Control — GD-018

| Case | Answer Relevancy | Faithfulness | G-Eval |
|---|---:|---:|---:|
| GD-018 | 0.00 — FAIL | N/A | 0.70 — FAIL |

The v2 correctly refused the out-of-scope general-knowledge request.

Answer Relevancy assigned 0.00 because the response did not answer the literal question. G-Eval was more nuanced: it recognized the correct refusal, but penalized the response for omitting the expected scope disclaimer.

## 5. Main Findings

### 5.1 V2 improved substantially but did not eliminate end-to-end failures

The v2 achieved stronger results across all three DeepEval metrics, especially in routine policy QA, authority boundaries, and multi-turn grounding. Residual failures remained around incomplete synthesis, exposed tool/retrieval calls, abstention inconsistencies, and missing expected policy details.

### 5.2 Answer Relevancy alone would overestimate system quality

The v2 reached:

- Answer Relevancy mean: **0.845**
- Faithfulness mean: **0.736**
- G-Eval mean: **0.680**

This gap shows that many outputs remained relevant without being fully grounded or behaviorally correct.

### 5.3 Tool-call completion is a major residual risk

Several v2 failures occurred when the saved output contained a tool-call/retrieval representation instead of a final synthesized answer. This is visible especially in `GD-010`, `GD-016-T1`, and `GD-016-T2`.

The issue is therefore not only policy knowledge, but also **agent orchestration and post-retrieval completion**.

### 5.4 Abstention improved but remained inconsistent

G-Eval shows better behavior for unsupported-policy questions, but generic metrics and Faithfulness still produced conflicting interpretations. This supports using multiple automated metrics together with trajectory evaluation and manual QA review.

### 5.5 Authority-boundary behavior is significantly stronger

The v2 consistently preserved the assistant's inability to approve purchases or leave requests and improved both relevance and grounding in this category.

## 6. Judge and Metric Limitations

The same no-rerun rule used for the normalized v1 baseline was maintained for v2.

Scores were preserved even where the textual reason appeared semantically questionable or different metrics interpreted the same answer differently.

Notable examples include:

- `GD-009` Faithfulness: “exactly R$5,000” was treated as contradictory to “up to R$5,000”.
- `GD-011` and `GD-013`: Faithfulness and G-Eval interpreted the saved response differently.
- `GD-017-T1`: Faithfulness produced a debatable penalty despite otherwise strong multi-turn performance.
- `GD-018`: generic Answer Relevancy penalized the desired refusal behavior.

These cases demonstrate that LLM-as-a-Judge metrics require human interpretation and should not be treated as infallible ground truth.

## 7. Important Methodological Limitation — Faithfulness

As in the normalized v1 evaluation, the DeepEval metric used here is **Reference-grounded Faithfulness**, not runtime RAG Faithfulness.

The `retrieval_context` supplied to DeepEval consists of curated official policy excerpts. It does not represent the exact chunks returned by the Knowledge Base during the original agent execution.

Therefore:

- **DeepEval Faithfulness** measures whether the saved response is supported by the designated policy reference context.
- **AgentCore TrajectoryAnyOrderMatch** measures whether the agent actually invoked the expected retrieval tool.

These signals are complementary and should not be conflated.

## 8. Execution Validity

All final v2 DeepEval batches produced numeric scores and textual reasons using the frozen `mistral-nemo:12b` judge.

An `AssertionError` generated by `assert_test()` indicates only that the metric score was below its configured threshold when `error=None` and a numeric score is present. These were treated as valid evaluation failures, not technical execution failures.

No case was rerun merely because it received an unfavorable score.

## 9. Brief Final Comparison — Normalized V1 vs V2

Both versions below were evaluated with the same `mistral-nemo:12b` judge and the same DeepEval configuration.

| Metric | V1 Mean | V2 Mean | Δ Mean | V1 Pass Rate | V2 Pass Rate | Δ Pass Rate |
|---|---:|---:|---:|---:|---:|---:|
| Answer Relevancy | 0.742 | **0.845** | **+0.103** | 60.0% | **80.0%** | **+20.0 pp** |
| Reference-grounded Faithfulness | 0.454 | **0.736** | **+0.282** | 15.8% | **63.2%** | **+47.4 pp** |
| Policy Answer Quality [G-Eval] | 0.515 | **0.680** | **+0.165** | 10.0% | **45.0%** | **+35.0 pp** |

### Final interpretation

The normalized comparison indicates a clear overall improvement from Agent v1 to Agent v2 across all three DeepEval metrics.

The largest gain occurred in **Reference-grounded Faithfulness**, with the pass rate increasing from **15.8% to 63.2%**. G-Eval also improved substantially, from **10.0% to 45.0%**, while Answer Relevancy increased from **60.0% to 80.0%**.

The v2 nevertheless did **not** reach the intended aggregate Faithfulness and G-Eval targets. Residual failures are concentrated around incomplete post-retrieval answer synthesis, exposed/textualized tool calls, unsupported or ambiguous abstention behavior, strict boundary-value interpretation, unnecessary policy/process detail, and inconsistencies in the LLM-as-a-Judge itself.

## 10. Status

**DeepEval Agent v2 final evaluation: COMPLETE**

Final v2 results:

- Answer Relevancy: **0.845 mean / 80.0% pass**
- Reference-grounded Faithfulness: **0.736 mean / 63.2% pass**
- Policy Answer Quality [G-Eval]: **0.680 mean / 45.0% pass**

**Normalized v1 × v2 DeepEval comparison: COMPLETE**
