# Agent design

`providers.py` defines the provider interface and implementations. `orchestrator.py` owns
explicit state, plans and business sequencing. `skills.py` defines reusable procedures and
tool permissions. The agent does not implement private SQL inside prompts.

Supported intents: identify, compatibility, inventory, pricing, process_part, orders,
prepare_order and unsupported. The process_part plan identifies a candidate, verifies
fitment, reads stock, finds duplicates, reads sales, calculates price, creates isolated
inventory and listing drafts, then requests approval. Other intents execute only needed
procedures. An ambiguous candidate list stops before all downstream tools.

Structured input fields override extracted fields. The LLM provider uses JSON Schema and
Pydantic validation. Transport/configuration failure uses the deterministic fallback and
records a visible warning; malformed structured entities request clarification. No live
provider calls were needed for the demo.

The optional provider format follows [OpenAI structured output documentation](https://developers.openai.com/api/docs/guides/structured-outputs).
Configure an accessible model explicitly; this repository does not assume any account's
model availability. The adapter is tested with a mocked HTTP provider, not a paid API.

No model output can supply a selling price or fitment list: those output fields do not exist
in the planner schema. Unknown tool names are rejected. Catalog retrieval text never reaches
the planner as system instructions. Approval cannot be granted through a natural-language
request, including "bypass approval".

Missing information appears in the run response and UI. A follow-up is a new run with corrected
fields or a selected OEM; cross-run conversational memory and automatic resume are not implemented.

