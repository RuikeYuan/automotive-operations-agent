# HTTP API

Swagger/OpenAPI: `http://localhost:18000/docs` and `/openapi.json`.
Frontend proxies `/api/*` to FastAPI using nginx or the Vite development proxy.

| Method | Path | Result |
|---|---|---|
| GET | /health | Database connectivity, actual planner mode and mock marker |
| POST | /agent/run | 201 with persisted run; validated natural-language request and optional entities |
| GET | /agent/runs | Recent runs, limit 1–100 |
| GET | /agent/runs/{id} | Run, explicit plan/state and result |
| GET | /agent/runs/{id}/trace | Ordered tool input/output, skill and timing |
| GET | /inventory?q=&manufacturer= | SQL stock, count and available quantity |
| GET | /inventory/{id} | One stock item |
| PATCH | /inventory/{id} | Propose an approved location change; body has only warehouse_location |
| GET | /parts/search?q= | Catalog candidates with evidence |
| GET | /orders?status=&manufacturer=&today= | Current SQL orders |
| GET | /approvals?status= | Latest approval snapshots |
| POST | /approvals/{id}/approve | Atomically consume a pending approval and execute |
| POST | /approvals/{id}/reject | Reject without executing the action |
| GET | /skills | Skill specifications and allowed tools |
| GET | /listings | Draft/published internal listings |
| GET | /marketplace | Local mock publication records |
| GET | /metrics | Measured synthetic run/tool/approval counts and rates |

Review requests must send `Content-Type: application/json`, for example `{}`. Chat is never
approval. There is no direct publish, delete, arbitrary SQL or bulk-update endpoint.

Errors: 404 missing resource; 409 consumed approval/stale snapshot/policy conflict; 415 wrong
review content type; 422 malformed request; 503 unavailable SQL or mock marketplace.
An operational tool failure produces a persisted run with status `failed` and a sanitized
error class. A 201 response means the run was created, not that its business task succeeded.

All API routes are unauthenticated for local demo use. Do not expose this prototype outside
loopback without adding employee identity, authorization and deployment protections.

