# FDE case study: operationalizing recycled-parts expertise

Automotive dismantlers move between physical parts, catalogs, inventory systems, sales records
and marketplace forms. A useful assistant must coordinate this workflow, preserve uncertainty,
and leave the operator in control of publication. A fluent chat response alone is insufficient.

We capture domain procedures as eight reusable skills. The agent selects those procedures from
the employee request. Deterministic tools access existing-style business systems; SQL remains
the source of transactional truth. Pricing uses a reproducible formula. Catalog evidence grounds
compatibility. An operator sees duplicate risks and the exact listing before approving.

The minimum deployment path is a local vertical slice: BMW alternator intake through mock
publication. The next integration step would be a read-only adapter for the customer's licensed
catalog and inventory system. Real OEM fitment cannot be inferred from this synthetic dataset.
Only after shadow-mode validation and operational ownership are established should a real
marketplace adapter and production authorization be designed.

## Measurement plan

The current metrics endpoint reports synthetic run counts, completed-run duration, tool calls,
tool failure rate, approval rate, completion rate and mock publication count. Completion latency
includes time awaiting human approval; use tool durations to inspect software execution cost.

Future deployment should record intake start/end, active handling time, operator interactions,
duplicate-confirmed outcomes and listing preparation completion. Compare with a measured manual
baseline across the same part mix. A duplicate candidate is not a confirmed duplicate; a completed
request is not evidence of economic benefit. No production savings or accuracy improvement is
claimed by this demo. The included report measures only explicitly defined synthetic cases.

