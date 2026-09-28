# Actual HTTP demo result

Executed: 2026-09-28T06:42:06.663903+00:00
Base URL: http://localhost:18000
Synthetic data; all publication is local mock publication.

- Identified: BMW Alternator / DEMO-BMW-ALT-001
- Matching inventory records before intake: 2
- Duplicate candidates: 3
- Fitment: compatible against synthetic catalog
- Recommended price: EUR 180.50
- Run stopped at: awaiting_approval
- Explicit approval ID: 1
- Mock publication: MOCK-000004
- Final run status: completed
- Repeated approval: HTTP 409
- Concurrent approval race on a separate draft: [200, 409]; one execution only
- Tool trace records including approved publication: 9

Full actual responses: [actual_output.json](actual_output.json).
Existing local data affects inventory counts, duplicate candidates and pricing on subsequent runs.
