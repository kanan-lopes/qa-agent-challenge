# Knowledge Base Retrieval Validation

## Objective

Validate the retrieval layer of the Employee Policy Assistant before
integrating the Knowledge Base with AgentCore Gateway and AgentCore Harness.

The tests were executed directly against the Amazon Bedrock Managed
Knowledge Base using standard retrieval, without response generation.

Knowledge Base: `employee-policy-s3`

Retrieval configuration:

- Retrieval mode: Standard retrieval
- Response generation: Disabled
- Parsing: Managed parser
- Chunking: Default
- Embeddings: Managed by Amazon Bedrock
- Metadata filters: None
- Reranking: None

---

## RT-001 — Domestic meal reimbursement

**Query**

> What is the maximum daily meal reimbursement for domestic business travel?

**Expected retrieval**

The retrieved context should contain the Meals section from
`travel_policy.md`, including the R$ 120 per day limit.

**Observed**

The Knowledge Base retrieved travel-related content, including
`travel_policy.md`, but the displayed top results did not include
the specific Meals section containing the R$ 120 daily limit.

The highest-ranked result contained the Accommodation section instead.

**Result**

PARTIAL

**Observation**

The correct source document was identified, but retrieval relevance was
not sufficient to return the most directly relevant chunk among the
displayed results.

This result should be considered when analyzing future agent failures,
because an incorrect answer may originate from insufficient retrieval
rather than from the language model itself.

---

## RT-002 — Procurement quotations

**Query**

> How many supplier quotations are required for a R$ 6,000 purchase?

**Expected retrieval**

The retrieved context should contain the rule for purchases greater than
R$ 5,000 from `procurement_policy.md`, requiring at least three supplier
quotations.

**Observed**

The Knowledge Base retrieved `procurement_policy.md` and returned the
relevant rule requiring:

- manager approval;
- Procurement review;
- at least 3 supplier quotations.

**Result**

PASS

**Observation**

The retrieval layer successfully returned the context required to answer
a question involving a monetary threshold.

---

## RT-003 — Missing airport parking limit

**Query**

> What is the daily airport parking reimbursement limit?

**Expected retrieval**

No source document contains a defined daily reimbursement limit for
airport parking.

The retriever may return semantically related content, but no retrieved
chunk should provide an explicit parking reimbursement limit.

**Observed**

The Knowledge Base returned semantically related content, including:

- accommodation reimbursement limits;
- non-reimbursable traffic or parking fines;
- general travel and expense policy content.

No retrieved context defined a daily airport parking reimbursement limit.

**Result**

PASS — expected negative retrieval behavior

**Observation**

Standard retrieval returns the most semantically related chunks even when
the corpus does not contain a direct answer.

The future agent must therefore distinguish between:

1. relevant retrieved context; and
2. sufficient evidence to answer the user's question.

If the agent invents a parking reimbursement limit, this should be
classified as an abstention / hallucination failure rather than as the
retrieval layer providing a false value.

---

## Initial conclusion

The Managed Knowledge Base is operational and successfully retrieves
relevant policy content.

The validation also identified an important limitation of the baseline
retrieval configuration: semantic relevance does not guarantee that the
most precise chunk will always appear among the highest-ranked results.

No retrieval optimization was applied at this stage in order to preserve
the default configuration for the initial baseline.