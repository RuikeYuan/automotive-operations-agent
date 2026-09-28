---
name: automotive-devpanel
description: Operate the re:part automotive-operations-agent backend from the terminal via its automotive-devpanel MCP tools, instead of asking the person to click through the React dashboard. Use this whenever the person asks to run a demo scenario, process a part, check compatibility, get a price, search inventory or orders, triage or approve/reject a pending approval, inspect an agent run's tool trace, or reset/inspect this project's synthetic data — for this project specifically (repo root has AGENTS.md describing "automotive dismantling and recycled OEM-parts" operations, or the person mentions re:part, DEMO-BMW-ALT, the automotive-operations-agent, or its skills/tools). Also use it to sanity-check a backend change by actually running a task end-to-end instead of only running pytest.
---

# automotive-devpanel

Dev-only control surface for this repo's automotive-operations-agent, exposed as MCP tools
(`mcp__automotive-devpanel__*`) by `tools/mcp-devpanel/server.py`. It is a thin HTTP wrapper
around the same FastAPI backend the React dashboard calls — every tool call is one REST request,
enforces no policy of its own, and cannot bypass the approval service, tool whitelisting or
Pydantic validation that already live in the backend. Using it is equivalent to a person using the
web UI, just from the terminal. It is not part of the shipped product (see AGENTS.md: "Build one
orchestration agent..."); never reference it from application code, and it is already excluded
from `scripts/package_submission.py`'s allowlist.

## Prerequisite

The backend must be reachable at `AUTOMOTIVE_API_BASE_URL` (default `http://localhost:18000`).
If a tool call fails with a connection error, check first with `docker compose ps` and start it
with `docker compose up -d` if needed — do not assume the stack is running.

## Tool-to-concept map

Each MCP tool calls one backend HTTP endpoint. See [architecture.md](../../../docs/architecture.md)
and `skills/*/SKILL.md` for what the backend does internally; this skill only covers how to drive
it from here.

| MCP tool | Backend route | Use for |
|---|---|---|
| `health` | `GET /health` | Confirm DB connection, active planner (`deterministic-demo` or `llm-structured-planner`), marketplace mode |
| `metrics` | `GET /metrics` | Run counts, pending approvals, mock publications, tool stats |
| `list_skills` | `GET /skills` | Dump the 8 domain skills' purpose/allowed tools/spec |
| `run_agent_task` | `POST /agent/run` | Submit one natural-language task — the same action as typing into the workspace and clicking Run task |
| `get_run` / `get_run_trace` / `list_runs` | `GET /agent/runs*` | Inspect a run's status/state and its full skill→tool execution trace |
| `list_approvals` | `GET /approvals` | List pending/approved/rejected approvals |
| `approve_action` / `reject_action` | `POST /approvals/{id}/approve\|reject` | Resolve a pending approval — approve publishes to the mock marketplace or changes an order's status; reject executes nothing |
| `search_inventory` / `get_inventory_item` | `GET /inventory*` | Read inventory records |
| `propose_inventory_location_change` | `PATCH /inventory/{id}` | Create a pending location-change approval (price/quantity are never accepted here) |
| `search_parts_catalog` | `GET /parts/search` | Query the synthetic OEM catalog |
| `list_orders` | `GET /orders` | Read orders |
| `list_listings` / `list_marketplace_records` | `GET /listings`, `GET /marketplace` | Read drafted/published listings |

## Running a task

Call `run_agent_task` with the same kind of sentence a warehouse employee would type — see
[demo_scenarios.md](../../../demo/demo_scenarios.md) for the canonical set (e.g. "Process BMW
alternator OEM DEMO-BMW-ALT-001. Check duplicates, verify compatibility, recommend a price and
prepare a listing."). Prefer the `oem_number`/`manufacturer`/`model`/`year`/`condition`/`order_id`
keyword arguments over stuffing everything into the text when you already know the exact values —
structured fields always win over anything the planner infers from free text, so this makes the
run reproducible instead of depending on the keyword-matching planner's quirks.

Read the returned `status` before deciding what to do next:
- `completed` — done, `final_response` has the answer.
- `needs_information` — the planner or orchestrator needs a more specific request (e.g. an
  ambiguous part with multiple catalog candidates); read `final_response.message` and retry with
  more detail rather than guessing.
- `awaiting_approval` — a protected action (listing publish or order status change) is staged but
  not executed. `final_response.approval_id` is the id to approve/reject. Never treat this as
  failure or as something you should try to force through another way — it means the guardrail is
  working. Tell the person what's staged and let them decide, unless they've already told you to
  approve straightforward demo runs on their behalf.
- `failed` — the operation rolled back safely; `final_response.error` names the exception type.

## Triaging approvals

`list_approvals(status="pending")` first, then read `get_run(agent_run_id)` or
`get_run_trace(agent_run_id)` for the approval's originating run if you need the evidence behind
it (duplicate candidates, compatibility, pricing factors) before deciding whether to recommend
approving. Approving is a real, if locally-scoped, mutation — it writes a mock marketplace record
or changes an order's status and cannot be undone by rejecting afterward (a resolved approval is
final; see 409 handling below). Don't call `approve_action` on the person's behalf without them
having asked for it or clearly wanting the demo pushed forward; do feel free to `reject_action` a
draft that duplicate/compatibility evidence shows shouldn't be published, and explain why.

`approve_action`/`reject_action` raise `ValueError` with the backend's status code and detail
string on failure — a `404` means the id doesn't exist, a `409` means it was already resolved
(including by a concurrent approval elsewhere; that's the duplicate-approval race guard working
as designed, not a bug to work around).

## Resetting synthetic data

Every `run_agent_task` intake creates a new draft inventory record, so duplicate-candidate counts
climb across a long session. To reset to the clean seed state:

```
docker compose down -v
docker compose up -d
```

**This permanently deletes everything in the project's PostgreSQL volume** — all runs, approvals,
drafts and mock marketplace records — and reseeds from scratch. Confirm with the person before
running it if they haven't already asked for a reset; it's a repo-scoped Docker volume, not their
system, but it is irreversible for this project's local data.

## What this skill will not do

- It has no delete/merge tool for inventory, because the backend has none — duplicate registration
  is a human decision, not something to automate around it.
- It will not accept "approve" as part of a task's free-text request; only a subsequent explicit
  `approve_action` call resolves an approval, exactly like the web UI requires a separate click.
- It never talks to a real marketplace; `list_marketplace_records` only ever shows local mock
  publications.
