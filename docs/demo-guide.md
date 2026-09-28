# 3–5 minute demonstration

Start `docker compose up --build` and open http://localhost:18080.

1. **0:00–0:30 — business context.** Show the working inventory. Explain that every vehicle,
   OEM, compatibility and price record is synthetic. The dashboard reads a real local database.
2. **0:30–1:30 — one request.** Submit the BMW alternator example. Expand a tool event in the
   execution panel. Show one agent selecting skills; catalog/SQL/pricing are deterministic code.
3. **1:30–2:30 — grounded result.** Inspect duplicate records and locations, compatible catalog
   vehicles, historical pricing factors and generated SKU. No warranty promises are invented.
4. **2:30–3:30 — human review.** Open the approval card, review the immutable listing snapshot
   and duplicate warning, approve, then show the `MOCK-*` publication ID. Explain that the
   backend enforces this boundary and repeat approvals receive HTTP 409.
5. **3:30–4:30 — fail safely.** Submit `Process BMW alternator` without OEM. The two candidates
   produce a clarification, not a fabricated answer. Optionally reject an order change.

Default planning is a transparent local rule-based demo, not a live model inference. Configure
the optional provider to use an LLM for intent extraction; all downstream safeguards remain.

`uv run python scripts/demo.py` runs the HTTP flow and records actual responses in
`demo/actual_output.json` and `demo/test_output.md`. It also races two approvals on a separate
draft to verify one consumes the action. It adds two synthetic mock publications to the database.

Browser E2E tests save workspace and mobile screenshots under `docs/screenshots`.

