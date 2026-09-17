# Agent v1 Initial Validation

## SMK-001 — Procurement threshold

**Input**

> How many supplier quotations are required for a R$ 6,000 purchase?

**Expected behavior**

The agent should consult the corporate knowledge base and identify that
purchases greater than R$ 5,000 require at least 3 supplier quotations.

**Observed behavior**

The agent asked the user to specify the type of purchase before answering,
suggesting examples such as IT equipment, office supplies, and travel expenses.

**Result**

FAIL

**Preliminary finding**

The clarification was unnecessary because the procurement policy defines
the quotation requirement according to the purchase amount.

The exact failure type will be determined after reviewing the execution trace:
- tool-selection failure;
- retrieval failure; or
- reasoning/response failure.

**Evidence**

`results/baseline/evidence/harness/smoke-001-procurement-unnecessary-clarification.png`

### Trace follow-up

The test was repeated in a fresh session after AgentCore Observability
was enabled.

**Observed response**

The agent answered that a R$ 6,000 purchase requires three supplier
quotations. However, it stated that:

- the relevant policy was "PP-003"; and
- the three-quotation threshold applied above R$ 3,000.

Both statements are inconsistent with the project Knowledge Base.
The actual policy is `PRC-001`, and the three-quotation requirement
applies to purchases greater than R$ 5,000.

**Trace analysis**

The trace showed an MCP `tools/list` operation, confirming that the
Gateway tools were successfully discovered.

However, no `tools/call`, Gateway Call Tool, or Knowledge Base
`Retrieve` invocation occurred.

`Bedrock AgentCore.RetrieveMemoryRecords` was present, but this operation
belongs to AgentCore Memory and is not a Knowledge Base retrieval.

The model therefore generated the answer without consulting the
corporate Knowledge Base.

**Result**

FAIL

**Failure classification**

- Tool-use omission
- Unsupported factual hallucination
- Policy/source hallucination
- Behavioral inconsistency across repeated executions

**Root cause**

The Gemma 3 4B IT baseline discovered the retrieval tool but did not
invoke it before answering a policy-dependent question.

## SMK-002 — Annual leave allowance

**Input**

> What is the annual vacation allowance for a full-time employee?

**Expected behavior**

The agent should invoke the corporate Knowledge Base and retrieve the
Employee Leave Policy.

The correct policy states that eligible full-time employees receive
20 business days of annual leave per calendar year after completing
90 calendar days of employment.

**Observed behavior**

The agent did not invoke the Knowledge Base retrieval tool.

Instead, it generated a tenure-based vacation policy:

- Years 1–5: 10 days
- Years 6–10: 15 days
- Years 11+: 20 days

It also referred to an "Employee Handbook – Time Off Policy", which is
not part of the project Knowledge Base.

**Trace evidence**

The execution trajectory contained only:

`invoke_agent → execute_event_loop_cycle → chat`

No Gateway or Retrieve invocation was observed.

The memory logs also showed that no previous memories were retrieved.

**Result**

FAIL

**Failure classification**

- Tool-use omission
- Unsupported factual hallucination
- Policy hallucination

**Preliminary root cause**

The model answered a policy-dependent question without consulting the
available Knowledge Base, despite the system prompt requiring retrieval.

**Evidence**

`results/baseline/evidence/traces/smk-002-annual-leave-no-retrieve.png`

### Test isolation note

An initial SMK-003 execution was discarded as an isolated baseline result.

Although a new session was created, the Harness retrieved long-term memory
from a previous Procurement test under the same actor scope. The response
therefore referenced the previous supplier quotation question.

Subsequent isolated tests use a unique actor ID in addition to a unique
session ID.

## SMK-003 — Domestic meal reimbursement

**Input**

> What is the maximum daily meal reimbursement for domestic business travel?

**Expected behavior**

The agent should invoke the corporate Knowledge Base and retrieve the
Business Travel Policy.

The correct policy states that meal expenses for domestic business travel
are reimbursable up to R$ 120 per day.

**Tool expected**

Yes — Knowledge Base Retrieve.

**Observed behavior**

The agent stated that it was using the Knowledge Base, but returned:

- Breakfast: R$ 35
- Lunch: R$ 60
- Dinner: R$ 75
- Total daily limit: R$ 170

None of these values are defined in the project Knowledge Base.

**Trace evidence**

The trace showed MCP `tools/list`, confirming that the Knowledge Base
retrieval tool was available to the agent.

However, no `tools/call` or Knowledge Base `Retrieve` invocation occurred.

`Bedrock AgentCore.RetrieveMemoryRecords` was present, but this operation
belongs to AgentCore Memory and is not Knowledge Base retrieval.

**Result**

FAIL

**Failure classification**

- Tool-use omission
- Unsupported factual hallucination
- False grounding claim

**Root cause**

Gemma 3 4B IT discovered the Knowledge Base retrieval tool but generated
the answer without invoking it.

**Evidence**

Response:
`results/baseline/evidence/harness/smk-003-travel-meal-response.png`

Trace:
`results/baseline/evidence/traces/smk-003-travel-meal-trace.png`

## SMK-004 — Remote work limit

**Input**

> How many days per week can an eligible employee work remotely?

**Expected behavior**

The agent should invoke the corporate Knowledge Base and retrieve the
Remote Work Policy.

The correct policy states that eligible employees may work remotely
up to 2 days per week.

**Tool expected**

Yes — Knowledge Base Retrieve.

**Observed behavior**

The agent asked the user to provide the employee's role and department
before answering.

It stated that remote work policy varies based on those factors and said
that it would consult the Knowledge Base only after receiving that
additional information.

The requested clarification was not necessary to answer the question
based on the available policy.

**Trace evidence**

The trace showed MCP `tools/list`, confirming that the Knowledge Base
retrieval tool was available.

However, no `tools/call` or Knowledge Base `Retrieve` invocation occurred.

`Bedrock AgentCore.RetrieveMemoryRecords` was present, but this belongs
to AgentCore Memory and is not Knowledge Base retrieval.

**Result**

FAIL

**Failure classification**

- Tool-use omission
- Unnecessary clarification
- Unsupported policy assumption

**Root cause**

Gemma 3 4B IT discovered the retrieval tool but did not invoke it before
responding to a policy-dependent question.

**Evidence**

Response:
`results/baseline/evidence/harness/smk-004-remote-work-response.png`

Trace:
`results/baseline/evidence/traces/smk-004-remote-work-trace.png`

## SMK-005 — Missing airport parking reimbursement limit

**Input**

> What is the daily airport parking reimbursement limit?

**Expected behavior**

The agent should invoke the corporate Knowledge Base.

The available policies do not define a daily airport parking
reimbursement limit. The agent should therefore state that the requested
limit is not specified in the provided company policies and should not
invent a value.

**Tool expected**

Yes — Knowledge Base Retrieve.

**Observed behavior**

The agent stated that it was using the Knowledge Base and claimed:

- Daily airport parking reimbursement limit: $30.00

No such value or airport parking reimbursement limit exists in the
project Knowledge Base.

**Trace evidence**

The trace showed MCP `tools/list`, confirming that the Knowledge Base
retrieval tool was available.

However, no `tools/call` or Knowledge Base `Retrieve` invocation occurred.

`Bedrock AgentCore.RetrieveMemoryRecords` was present, but this operation
belongs to AgentCore Memory and is not Knowledge Base retrieval.

**Result**

FAIL

**Failure classification**

- Tool-use omission
- Abstention failure
- Unsupported factual hallucination
- False grounding claim

**Root cause**

Gemma 3 4B IT generated a specific policy value without consulting the
available Knowledge Base and incorrectly represented the answer as being
grounded in the Knowledge Base.

**Evidence**

Response:
`results/baseline/evidence/harness/smk-005-airport-parking-response.png`

Trace:
`results/baseline/evidence/traces/smk-005-airport-parking-trace.png`

