import json
import re
from typing import Protocol
from backend.app.config import ROOT


class Retriever(Protocol):
    def search(self, query: str, manufacturer: str | None = None) -> list[dict]: ...


class LocalKnowledge:
    """Metadata/keyword retrieval. Documents are never passed to the planner as instructions."""
    def __init__(self):
        self.catalog = json.loads((ROOT / "knowledge/parts_catalog.json").read_text(encoding="utf-8"))
        self.compatibility = json.loads((ROOT / "knowledge/compatibility.json").read_text(encoding="utf-8"))

    def search(self, query, manufacturer=None):
        tokens = set(re.findall(r"[\w-]+", query.lower()))
        candidates = []
        for row in self.catalog:
            if manufacturer and row["manufacturer"].lower() != manufacturer.lower():
                continue
            terms = set(re.findall(r"[\w-]+", f"{row['name']} {row['oem_number']} {row['category']} {row['model']}".lower()))
            score = len(tokens & terms)
            if score or not tokens:
                candidates.append({**row, "retrieval_score":score})
        return sorted(candidates, key=lambda r: (-r["retrieval_score"], r["id"]))[:20]

    def lookup(self, oem):
        return next((r for r in self.catalog if r["oem_number"] == oem), None)

    def fitment(self, oem):
        return next((r for r in self.compatibility if r["oem_number"] == oem), None)

    def procedures(self, query):
        sources = ["business_rules.md", "example_cases.json"]
        tokens = set(query.lower().split())
        return [{"text": (ROOT / "knowledge" / f).read_text(encoding="utf-8"), "evidence": f, "trust":"data_only"} for f in sources if tokens & set((ROOT / "knowledge" / f).read_text(encoding="utf-8").lower().split())]

