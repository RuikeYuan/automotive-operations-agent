---
name: order-processing
description: Read SQL orders and propose reviewed processing changes.
---

# order-processing

## Purpose and trigger conditions
Read SQL orders and propose reviewed processing changes. Select when an employee request requires this procedure.

## Inputs
- Required: Order ID for processing or query for reads.
- Optional: manufacturer, status, today.

## Business rules
Read directly. Processing requires approval tied to order ID and previous status. Never infer customer data.

## Execution procedure
1. Validate required inputs using the runtime's Pydantic schemas; ask for missing information.
2. Execute the allowed tools in their declared dependency order: get_orders, prepare_order.
3. Inspect structured results and evidence; record skill, tool, status and latency.
4. Return the expected output. Stop before any protected action and request approval.

## Allowed tools
get_orders, prepare_order. Enforced by `backend/app/agent/skills.py` and the orchestrator.
For protected tools, the orchestrator proposes the action and the approval service executes it.

## Failure handling
Unknown identity or ambiguous evidence: request clarification. Tool failure: surface a sanitized error,
roll back unfinished drafts, and preserve an execution trace. Never fill missing facts by guessing.

## Expected output
orders or approval request. Results include synthetic-data labels and evidence references.

## Example
Employee: Prepare order 1024 for processing.
Use the procedure above with actual database and catalog results, never a hardcoded final answer.
