---
name: pricing
description: Calculate an evidence based selling-price recommendation.
---

# pricing

## Purpose and trigger conditions
Calculate an evidence based selling-price recommendation. Select when an employee request requires this procedure.

## Inputs
- Required: Resolved part ID and condition.
- Optional: Configured minimum margin.

## Business rules
Use historical median or marked synthetic reference. Apply condition, available-stock and age factors, then margin floor. Low history lowers confidence. Never update public prices.

## Execution procedure
1. Validate required inputs using the runtime's Pydantic schemas; ask for missing information.
2. Execute the allowed tools in their declared dependency order: get_historical_sales, calculate_suggested_price.
3. Inspect structured results and evidence; record skill, tool, status and latency.
4. Return the expected output. Stop before any protected action and request approval.

## Allowed tools
get_historical_sales, calculate_suggested_price. Enforced by `backend/app/agent/skills.py` and the orchestrator.
For protected tools, the orchestrator proposes the action and the approval service executes it.

## Failure handling
Unknown identity or ambiguous evidence: request clarification. Tool failure: surface a sanitized error,
roll back unfinished drafts, and preserve an execution trace. Never fill missing facts by guessing.

## Expected output
suggested_price, price_range, factors, evidence, confidence. Results include synthetic-data labels and evidence references.

## Example
Employee: Recommend price for DEMO-TOYOTA-SNS-001.
Use the procedure above with actual database and catalog results, never a hardcoded final answer.
