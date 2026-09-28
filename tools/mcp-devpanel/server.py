"""Dev-only MCP server wrapping the automotive-operations-agent FastAPI backend.

Not part of the product. Never packaged into the submission archive (the
packaging allowlist in scripts/package_submission.py has no "tools" entry).
Gives Claude Code, running as a developer's terminal assistant, a typed tool
surface over the same HTTP API the React dashboard uses. It performs no
direct database or filesystem access and enforces no policy of its own; every
call is a plain HTTP request to the backend, so all approval gating, tool
whitelisting and validation still happen there, exactly as for the web UI.

Run with: uv run --with "mcp<2" python tools/mcp-devpanel/server.py
(pinned below 2.0: v2's stdio transport needs pywin32 on Windows, which the
ephemeral --with environment does not register correctly; v1's FastMCP API
used here has no such dependency.)
Requires the backend reachable at AUTOMOTIVE_API_BASE_URL
(default http://localhost:18000, e.g. via `docker compose up -d`).
"""
import os
import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("AUTOMOTIVE_API_BASE_URL", "http://localhost:18000")
client = httpx.Client(base_url=BASE_URL, timeout=30)

mcp = FastMCP("automotive-devpanel")


def _check(response):
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise ValueError(f"{response.status_code}: {detail}")
    return response.json()


def _get(path, **params):
    return _check(client.get(path, params={k: v for k, v in params.items() if v is not None}))


def _post(path, payload=None):
    return _check(client.post(path, json=payload or {}))


@mcp.tool()
def health() -> dict:
    """Check backend health: database connectivity, active intent planner and marketplace mode."""
    return _get("/health")


@mcp.tool()
def metrics() -> dict:
    """Fetch dashboard metrics: run counts, pending approvals, mock publications, tool-call stats."""
    return _get("/metrics")


@mcp.tool()
def list_skills() -> list:
    """List the 8 domain skills with purpose, allowed tools and SKILL.md path."""
    return _get("/skills")


@mcp.tool()
def run_agent_task(request: str, oem_number: str | None = None, manufacturer: str | None = None,
                    model: str | None = None, year: int | None = None, condition: str = "good",
                    order_id: int | None = None) -> dict:
    """Run one agent task: the same action a person takes by typing into the web workspace and
    clicking "Run task". Returns the full AgentRun record (id, status, state incl. selected
    skills, final_response). Structured fields always override anything inferred from the text.
    A run that reaches a protected action stops at status "awaiting_approval" and never
    publishes or mutates state on its own; use approve_action/reject_action to resolve it."""
    entities = {k: v for k, v in dict(oem_number=oem_number, manufacturer=manufacturer, model=model,
                                       year=year, condition=condition, order_id=order_id).items() if v is not None}
    return _post("/agent/run", {"request": request, "entities": entities})


@mcp.tool()
def get_run(run_id: str) -> dict:
    """Fetch one agent run by id."""
    return _get(f"/agent/runs/{run_id}")


@mcp.tool()
def get_run_trace(run_id: str) -> list:
    """Fetch the tool-call trace for one run: selected skill, tool name, input, output, duration
    and error per step, in execution order."""
    return _get(f"/agent/runs/{run_id}/trace")


@mcp.tool()
def list_runs(limit: int = 30) -> list:
    """List recent agent runs, newest first."""
    return _get("/agent/runs", limit=limit)


@mcp.tool()
def list_approvals(status: str | None = None) -> list:
    """List approval requests. status: pending | approved | rejected, or omit for all."""
    return _get("/approvals", status=status)


@mcp.tool()
def approve_action(approval_id: int) -> dict:
    """Approve a pending approval and execute exactly the stored action (publish a listing to the
    local mock marketplace, or change an order's status). Fails with 404 if the approval does not
    exist and 409 if it was already resolved or a concurrent approval already consumed it — the
    action then executes at most once. Never publishes to a real marketplace."""
    return _post(f"/approvals/{approval_id}/approve")


@mcp.tool()
def reject_action(approval_id: int) -> dict:
    """Reject a pending approval. No mutation is executed."""
    return _post(f"/approvals/{approval_id}/reject")


@mcp.tool()
def search_inventory(q: str = "", manufacturer: str | None = None) -> list:
    """Search inventory records by free text over name, OEM number, internal SKU and warehouse
    location, with an optional exact manufacturer filter."""
    return _get("/inventory", q=q, manufacturer=manufacturer)


@mcp.tool()
def get_inventory_item(item_id: int) -> dict:
    """Fetch one inventory record by its internal id."""
    return _get(f"/inventory/{item_id}")


@mcp.tool()
def propose_inventory_location_change(item_id: int, warehouse_location: str) -> dict:
    """Propose moving one inventory item to a new warehouse location. Only the location field is
    ever accepted here; price and quantity are not adjustable through this endpoint. Creates a
    pending approval — use approve_action to apply it."""
    return _check(client.patch(f"/inventory/{item_id}", json={"warehouse_location": warehouse_location}))


@mcp.tool()
def search_parts_catalog(q: str = "") -> dict:
    """Search the synthetic OEM parts catalog by free text (name, OEM number, manufacturer)."""
    return _get("/parts/search", q=q)


@mcp.tool()
def list_orders(status: str | None = None, manufacturer: str | None = None, today: bool = False) -> list:
    """List orders, optionally filtered by status, manufacturer, or restricted to today's orders."""
    return _get("/orders", status=status, manufacturer=manufacturer, today=today)


@mcp.tool()
def list_listings() -> list:
    """List generated listing drafts, published or not."""
    return _get("/listings")


@mcp.tool()
def list_marketplace_records() -> list:
    """List records published to the local mock marketplace. This is the only marketplace this
    system ever writes to; there is no real marketplace integration."""
    return _get("/marketplace")


if __name__ == "__main__":
    mcp.run()
