---
name: duplicate-detection
description: Find exact and similar inventory records.
---

# duplicate-detection

## Purpose and trigger conditions
Find exact and similar inventory records. Select when an employee request requires this procedure.

## Inputs
- Required: Resolved part ID.
- Optional: source vehicle.

## Business rules
Match OEM first, then same manufacturer/category and name similarity. Explain same-source-vehicle evidence. Never automatically merge or delete.

## Execution procedure
1. Validate required inputs using the runtime's Pydantic schemas; ask for missing information.
2. Execute the allowed tools in their declared dependency order: find_duplicates.
3. Inspect structured results and evidence; record skill, tool, status and latency.
4. Return the expected output. Stop before any protected action and request approval.

## Allowed tools
find_duplicates. Enforced by `backend/app/agent/skills.py` and the orchestrator.
For protected tools, the orchestrator proposes the action and the approval service executes it.

## Failure handling
Unknown identity or ambiguous evidence: request clarification. Tool failure: surface a sanitized error,
roll back unfinished drafts, and preserve an execution trace. Never fill missing facts by guessing.

## Expected output
duplicate_probability, candidate_records, reasons, recommended_action. Results include synthetic-data labels and evidence references.

## Example
Employee: Check duplicates of DEMO-BMW-ALT-001.
Use the procedure above with actual database and catalog results, never a hardcoded final answer.
