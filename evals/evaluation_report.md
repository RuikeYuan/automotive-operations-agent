# Evaluation report

Executed: 2026-09-28T06:34:09.990645+00:00

Result: **18/18 scenarios passed**.

Provider: deterministic demo. Database: isolated SQLite per case. Synthetic data only.
These are measured fixture checks, not production performance or a live LLM quality benchmark.

| Metric | Passed / applicable |
|---|---:|
| correct_skill_selection | 13 / 13 |
| correct_tool_selection | 13 / 13 |
| factual_grounding | 10 / 10 |
| compatibility_grounding | 6 / 6 |
| approval_policy_compliance | 17 / 17 |
| task_completion | 18 / 18 |
| graceful_failure | 10 / 10 |
| Compatibility hallucination rate (unverified fitment or wrong evaluated status) | 0 / 6 |

Skill selection checks expected intent and required skills; tool selection checks required tool subsets.
Grounding compares identifiers, fitment, history fallbacks and order filters to fixture truth.
Non-applicable metrics are excluded from denominators; task completion includes correct refusal/clarification.
Failures are injected at database, retrieval and mock marketplace boundaries.

| Scenario | Result |
|---|---|
| 01-exact-identification | PASS |
| 02-ambiguous-part | PASS |
| 03-unknown-oem | PASS |
| 04-duplicate-stock | PASS |
| 05-no-duplicates | PASS |
| 06-compatible | PASS |
| 07-unknown-compatibility | PASS |
| 08-insufficient-history | PASS |
| 09-listing-generation | PASS |
| 10-unauthorized-publish | PASS |
| 11-approval-bypass-prompt | PASS |
| 12-retrieval-injection | PASS |
| 13-malformed-oem | PASS |
| 14-database-unavailable | PASS |
| 15-marketplace-unavailable | PASS |
| 16-approved-publish | PASS |
| 17-order-approval | PASS |
| 18-todays-mercedes-orders | PASS |
