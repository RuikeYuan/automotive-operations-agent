---
name: inventory-management
description: Search current SQL stock and create isolated intake drafts.
---

# inventory-management

## Purpose and trigger conditions
Search current SQL stock and create isolated intake drafts. Select when an employee request requires this procedure.

## Inputs
- Required: Part ID for drafting; search text for reads.
- Optional: OEM, manufacturer, category, price.

## Business rules
Read from SQL. Drafts do not count as available stock. No public price changes or destructive mutations. Draft publication requires review.

## Execution procedure
1. Validate required inputs using the runtime's Pydantic schemas; ask for missing information.
2. Execute the allowed tools in their declared dependency order: search_inventory, get_inventory_item, create_inventory_draft.
3. Inspect structured results and evidence; record skill, tool, status and latency.
4. Return the expected output. Stop before any protected action and request approval.

## Allowed tools
search_inventory, get_inventory_item, create_inventory_draft. Enforced by `backend/app/agent/skills.py` and the orchestrator.
For protected tools, the orchestrator proposes the action and the approval service executes it.

## Failure handling
Unknown identity or ambiguous evidence: request clarification. Tool failure: surface a sanitized error,
roll back unfinished drafts, and preserve an execution trace. Never fill missing facts by guessing.

## Expected output
items, stock counts, locations, draft SKU. Results include synthetic-data labels and evidence references.

## Example
Employee: Find BMW alternators in stock.
Use the procedure above with actual database and catalog results, never a hardcoded final answer.
