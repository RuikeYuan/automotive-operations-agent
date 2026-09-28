---
name: part-identification
description: Resolve incomplete part descriptions into evidenced catalog candidates.
---

# part-identification

## Purpose and trigger conditions
Resolve incomplete part descriptions into evidenced catalog candidates. Select when an employee request requires this procedure.

## Inputs
- Required: Employee description or OEM.
- Optional: manufacturer, model, year, VIN, category.

## Business rules
Normalize names. Rank catalog matches. Never invent OEM identifiers. Stop and ask for an OEM when multiple candidates remain.

## Execution procedure
1. Validate required inputs using the runtime's Pydantic schemas; ask for missing information.
2. Execute the allowed tools in their declared dependency order: search_parts_catalog, lookup_oem.
3. Inspect structured results and evidence; record skill, tool, status and latency.
4. Return the expected output. Stop before any protected action and request approval.

## Allowed tools
search_parts_catalog, lookup_oem. Enforced by `backend/app/agent/skills.py` and the orchestrator.
For protected tools, the orchestrator proposes the action and the approval service executes it.

## Failure handling
Unknown identity or ambiguous evidence: request clarification. Tool failure: surface a sanitized error,
roll back unfinished drafts, and preserve an execution trace. Never fill missing facts by guessing.

## Expected output
candidate_parts, confidence, evidence, missing_information, recommended_next_action. Results include synthetic-data labels and evidence references.

## Example
Employee: Identify DEMO-BMW-ALT-001.
Use the procedure above with actual database and catalog results, never a hardcoded final answer.
