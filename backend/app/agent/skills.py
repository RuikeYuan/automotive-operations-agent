from dataclasses import dataclass
from backend.app.config import ROOT


@dataclass(frozen=True)
class Skill:
    name: str
    purpose: str
    tools: tuple[str, ...]
    required: str
    optional: str
    rules: str
    output: str
    example: str

    @property
    def specification(self):
        return (ROOT / "skills" / self.name / "SKILL.md").read_text(encoding="utf-8")


SKILLS = {s.name:s for s in [
    Skill("part-identification", "Resolve incomplete part descriptions into evidenced catalog candidates", ("search_parts_catalog","lookup_oem"), "Employee description or OEM", "manufacturer, model, year, VIN, category", "Normalize names. Rank catalog matches. Never invent OEM identifiers. Stop and ask for an OEM when multiple candidates remain.", "candidate_parts, confidence, evidence, missing_information, recommended_next_action", "Identify DEMO-BMW-ALT-001"),
    Skill("compatibility-check", "Check fitment using synthetic catalog evidence", ("check_vehicle_compatibility",), "Resolved part ID", "target manufacturer, model, year", "Use catalog records only. Absence is uncertain. Explicit exclusions alone establish incompatibility. A partial target cannot establish fitment.", "status, vehicles, evidence, missing_information", "Check DEMO-BMW-ALT-001 for BMW 3 Series 2019"),
    Skill("inventory-management", "Search current SQL stock and create isolated intake drafts", ("search_inventory","get_inventory_item","create_inventory_draft"), "Part ID for drafting; search text for reads", "OEM, manufacturer, category, price", "Read from SQL. Drafts do not count as available stock. No public price changes or destructive mutations. Draft publication requires review.", "items, stock counts, locations, draft SKU", "Find BMW alternators in stock"),
    Skill("duplicate-detection", "Find exact and similar inventory records", ("find_duplicates",), "Resolved part ID", "source vehicle", "Match OEM first, then same manufacturer/category and name similarity. Explain same-source-vehicle evidence. Never automatically merge or delete.", "duplicate_probability, candidate_records, reasons, recommended_action", "Check duplicates of DEMO-BMW-ALT-001"),
    Skill("pricing", "Calculate an evidence based selling-price recommendation", ("get_historical_sales","calculate_suggested_price"), "Resolved part ID and condition", "Configured minimum margin", "Use historical median or marked synthetic reference. Apply condition, available-stock and age factors, then margin floor. Low history lowers confidence. Never update public prices.", "suggested_price, price_range, factors, evidence, confidence", "Recommend price for DEMO-TOYOTA-SNS-001"),
    Skill("listing-generation", "Prepare a fact-grounded local marketplace draft", ("generate_listing_draft",), "Draft inventory ID", "condition", "Only use verified catalog facts. Separate marketing copy. Do not invent warranty or fitment. The draft must not publish itself.", "listing_id, title, description, price, facts, marketing_copy", "Prepare a listing for the identified alternator"),
    Skill("order-processing", "Read SQL orders and propose reviewed processing changes", ("get_orders","prepare_order"), "Order ID for processing or query for reads", "manufacturer, status, today", "Read directly. Processing requires approval tied to order ID and previous status. Never infer customer data.", "orders or approval request", "Prepare order 1024 for processing"),
    Skill("marketplace-publishing", "Publish reviewed drafts to the local mock marketplace", ("publish_marketplace_listing",), "Stored listing snapshot and employee approval", "none", "The agent must stop at a pending approval. Only the approval service can consume it. Reject changed snapshots and repeats. No real network integrations.", "pending approval or mock external ID after review", "Review and publish the BMW alternator draft"),
]}


INTENT_SKILLS = {
    "process_part":["part-identification","compatibility-check","inventory-management","duplicate-detection","pricing","listing-generation","marketplace-publishing"],
    "identify":["part-identification"],
    "inventory":["inventory-management"],
    "compatibility":["part-identification","compatibility-check"],
    "pricing":["part-identification","pricing"],
    "orders":["order-processing"], "prepare_order":["order-processing"], "unsupported":[],
}

