# BMW alternator intake — synthetic data

Source: BMW 3 Series, 2019, good condition.
OEM: `DEMO-BMW-ALT-001`.

Process this part. Check if we already have the same item, verify compatibility,
recommend a selling price, and prepare a marketplace listing.

API request:
```json
{"request":"Process BMW alternator OEM DEMO-BMW-ALT-001. Check duplicates, compatibility and recommend a price. Prepare a marketplace listing.","entities":{"manufacturer":"BMW","model":"3 Series","year":2019,"condition":"good"}}
```

Expected boundary: stop at pending human approval. Actual output is recorded by scripts/demo.py.

