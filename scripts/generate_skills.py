from backend.app.agent.skills import SKILLS
from backend.app.config import ROOT

for skill in SKILLS.values():
    folder = ROOT / "skills" / skill.name
    folder.mkdir(parents=True,exist_ok=True)
    (folder / "SKILL.md").write_text(f"""---
name: {skill.name}
description: {skill.purpose}.
---

# {skill.name}

## Purpose and trigger conditions
{skill.purpose}. Select when an employee request requires this procedure.

## Inputs
- Required: {skill.required}.
- Optional: {skill.optional}.

## Business rules
{skill.rules}

## Execution procedure
1. Validate required inputs using the runtime's Pydantic schemas; ask for missing information.
2. Execute the allowed tools in their declared dependency order: {', '.join(skill.tools)}.
3. Inspect structured results and evidence; record skill, tool, status and latency.
4. Return the expected output. Stop before any protected action and request approval.

## Allowed tools
{', '.join(skill.tools)}. Enforced by `backend/app/agent/skills.py` and the orchestrator.
For protected tools, the orchestrator proposes the action and the approval service executes it.

## Failure handling
Unknown identity or ambiguous evidence: request clarification. Tool failure: surface a sanitized error,
roll back unfinished drafts, and preserve an execution trace. Never fill missing facts by guessing.

## Expected output
{skill.output}. Results include synthetic-data labels and evidence references.

## Example
Employee: {skill.example}.
Use the procedure above with actual database and catalog results, never a hardcoded final answer.
""",encoding="utf-8")
print(f"Wrote {len(SKILLS)} skill specifications.")

