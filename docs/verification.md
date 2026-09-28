# Verification record

Executed 2026-09-28 on Windows 10 Pro, Python 3.12.7, Node 24.15.0, Docker 29.3.1.
All data is synthetic; all publication is to the local mock marketplace.

| Check | Command | Result |
|---|---|---|
| Backend tests (host, SQLite) | `uv run pytest -q` | 30 passed |
| Backend tests (container) | `docker compose exec -T backend pytest -q` | 30 passed |
| Evaluation runner (host) | `uv run python -m evals.run` | 18/18 passed |
| Evaluation runner (container, PostgreSQL image) | `docker compose exec -T backend python -m evals.run` | 18/18 passed |
| Frontend production build | `npm run build` | passed |
| Docker stack | `docker compose up -d --build` | db, backend, frontend healthy on 15432 / 18000 / 18080 |
| PostgreSQL migrations and seed | `uv run python -m scripts.verify_postgres` | head `fe28211ed699`; seed idempotent |
| Live HTTP demo against Docker | `uv run python scripts/demo.py` | see [test_output.md](../demo/test_output.md) |
| Browser E2E against Docker (English UI) | `npm run test:e2e` | 3 passed |

## Live demo evidence (PostgreSQL)

- BMW alternator run stops at `awaiting_approval`; marketplace count unchanged before approval.
- Approval publishes one `MOCK-` listing; run status becomes `completed`.
- Repeated approval returns HTTP 409.
- Concurrent approval race on a separate draft returns `[200, 409]`; one publication only.

## Defects found and fixed during this verification

1. **PostgreSQL sequences not advanced after seed.** The seed inserts explicit ids, so the first
   draft inventory insert failed with `UniqueViolation` on `inventory_items_pkey` and `/agent/run`
   returned 503. `seed.py` now resets `vehicles`, `parts`, `inventory_items`, `listings` and
   `orders` sequences after seeding, and also on start-up for already-seeded databases.
   SQLite tests did not cover this because SQLite assigns `MAX(id)+1`.
2. **Approval review button race in the dashboard.** The "Review approval" button rendered before the
   approvals list refreshed, so an immediate click found no approval and opened nothing. The
   run result is now shown only after the approvals refresh completes.

## Not verified

- The optional model provider was tested with a mocked HTTP client only; no live API key was used.
- No load, security penetration, or multi-user testing was performed.
