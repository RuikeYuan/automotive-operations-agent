---
name: marketplace-publishing
description: Publish reviewed drafts to the local mock marketplace.
---

# marketplace-publishing

## Purpose and trigger conditions
Publish reviewed drafts to the local mock marketplace. Select when an employee request requires this procedure.

## Inputs
- Required: Stored listing snapshot and employee approval.
- Optional: none.

## Business rules
The agent must stop at a pending approval. Only the approval service can consume it. Reject changed snapshots and repeats. No real network integrations.

## Execution procedure
1. Validate required inputs using the runtime's Pydantic schemas; ask for missing information.
2. Execute the allowed tools in their declared dependency order: publish_marketplace_listing.
3. Inspect structured results and evidence; record skill, tool, status and latency.
4. Return the expected output. Stop before any protected action and request approval.

## Allowed tools
publish_marketplace_listing. Enforced by `backend/app/agent/skills.py` and the orchestrator.
For protected tools, the orchestrator proposes the action and the approval service executes it.

## Failure handling
Unknown identity or ambiguous evidence: request clarification. Tool failure: surface a sanitized error,
roll back unfinished drafts, and preserve an execution trace. Never fill missing facts by guessing.

## Expected output
pending approval or mock external ID after review. Results include synthetic-data labels and evidence references.

## Example
Employee: Review and publish the BMW alternator draft.
Use the procedure above with actual database and catalog results, never a hardcoded final answer.
