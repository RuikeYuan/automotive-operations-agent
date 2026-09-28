---
name: listing-generation
description: Prepare a fact-grounded local marketplace draft.
---

# listing-generation

## Purpose and trigger conditions
Prepare a fact-grounded local marketplace draft. Select when an employee request requires this procedure.

## Inputs
- Required: Draft inventory ID.
- Optional: condition.

## Business rules
Only use verified catalog facts. Separate marketing copy. Do not invent warranty or fitment. The draft must not publish itself.

## Execution procedure
1. Validate required inputs using the runtime's Pydantic schemas; ask for missing information.
2. Execute the allowed tools in their declared dependency order: generate_listing_draft.
3. Inspect structured results and evidence; record skill, tool, status and latency.
4. Return the expected output. Stop before any protected action and request approval.

## Allowed tools
generate_listing_draft. Enforced by `backend/app/agent/skills.py` and the orchestrator.
For protected tools, the orchestrator proposes the action and the approval service executes it.

## Failure handling
Unknown identity or ambiguous evidence: request clarification. Tool failure: surface a sanitized error,
roll back unfinished drafts, and preserve an execution trace. Never fill missing facts by guessing.

## Expected output
listing_id, title, description, price, facts, marketing_copy. Results include synthetic-data labels and evidence references.

## Example
Employee: Prepare a listing for the identified alternator.
Use the procedure above with actual database and catalog results, never a hardcoded final answer.
