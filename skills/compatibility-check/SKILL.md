---
name: compatibility-check
description: Check fitment using synthetic catalog evidence.
---

# compatibility-check

## Purpose and trigger conditions
Check fitment using synthetic catalog evidence. Select when an employee request requires this procedure.

## Inputs
- Required: Resolved part ID.
- Optional: target manufacturer, model, year.

## Business rules
Use catalog records only. Absence is uncertain. Explicit exclusions alone establish incompatibility. A partial target cannot establish fitment.

## Execution procedure
1. Validate required inputs using the runtime's Pydantic schemas; ask for missing information.
2. Execute the allowed tools in their declared dependency order: check_vehicle_compatibility.
3. Inspect structured results and evidence; record skill, tool, status and latency.
4. Return the expected output. Stop before any protected action and request approval.

## Allowed tools
check_vehicle_compatibility. Enforced by `backend/app/agent/skills.py` and the orchestrator.
For protected tools, the orchestrator proposes the action and the approval service executes it.

## Failure handling
Unknown identity or ambiguous evidence: request clarification. Tool failure: surface a sanitized error,
roll back unfinished drafts, and preserve an execution trace. Never fill missing facts by guessing.

## Expected output
status, vehicles, evidence, missing_information. Results include synthetic-data labels and evidence references.

## Example
Employee: Check DEMO-BMW-ALT-001 for BMW 3 Series 2019.
Use the procedure above with actual database and catalog results, never a hardcoded final answer.
