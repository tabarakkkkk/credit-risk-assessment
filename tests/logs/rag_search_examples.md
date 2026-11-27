# RAG Search Examples

## Example 1 — DTI

Query: `What is the standard DTI range?`

Top result:

- Source: `dti_policy.md`
- Section: `Section 1 — Standard DTI range`
- Topic: `dti policy`
- Score: `0.4577`
- Result: A DTI below 36% is within the standard review range in the educational policy bank.

## Example 2 — Previous default

Query: `How does a previous default affect review?`

Expected source: `previous_default_policy.md`

## Example 3 — Loan limits

Query: `What is the illustrative limit for education loans?`

Expected source: `loan_limits_policy.md`

These examples were retrieved through `rag.retriever.policies_search` without
using Streamlit or the future LangGraph agent.
