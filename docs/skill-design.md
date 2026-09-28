# Skill design

Each `skills/<name>/SKILL.md` contains purpose, trigger, required and optional inputs,
business rules, execution procedure, allowed tools, failure behavior, output and an example.
The eight skills are identification, compatibility, inventory, duplicates, pricing, listing,
orders and marketplace publication.

Runtime mapping lives in `backend/app/agent/skills.py`; the agent verifies that deployed
specifications exist and enforces the audited tool allowlist from that registry. Markdown is
the human-readable procedure; it is not dynamically interpreted as executable authorization.
`python -m scripts.generate_skills` regenerates specifications from the canonical registry.

Skill outputs are structured tool results, plus an approval proposal where appropriate.
`ToolInput` and `ToolResult` enforce the common typed invocation boundary. Individual tools
check their required IDs and business preconditions. Protected tools are registered for
discoverability but reject direct agent execution. The review service executes the authorized
operation separately and adds a trace event under the same skill.

