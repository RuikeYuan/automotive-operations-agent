"""Generate explicitly synthetic reference data, never real fitment claims."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
brands = [("BMW", "3 Series", "G20"), ("Volkswagen", "Golf", "MK7"), ("Mercedes-Benz", "C-Class", "W205"), ("Audi", "A4", "B9"), ("Toyota", "Corolla", "E210")]
categories = [("ALT", "alternator", 200), ("STR", "starter motor", 140), ("HL", "headlight", 280), ("ECU", "ECU", 350), ("TRN", "transmission component", 420), ("MIR", "mirror", 110), ("INF", "infotainment unit", 320), ("SNS", "sensor", 65)]
parts, compatibility = [], []
for bi, (brand, model, generation) in enumerate(brands):
    for ci, (code, category, price) in enumerate(categories):
        oem = f"DEMO-{['BMW','VW','MB','AUDI','TOYOTA'][bi]}-{code}-001"
        part = dict(id=len(parts)+1, oem_number=oem, category=category, name=f"{brand} {category.title()}", manufacturer=brand, condition="good", source_vehicle_id=bi+1, market_reference=price, acquisition_cost=round(price*.45,2), model=model, year=2019, generation=generation, evidence=f"parts_catalog.json#{oem}", synthetic=True)
        parts.append(part)
        compatibility.append(dict(oem_number=oem, vehicles=[dict(manufacturer=brand, model=model, year=y, engine="2.0 petrol demo") for y in (2018,2019,2020)] if code != "SNS" else [], evidence=f"compatibility.json#{oem}", synthetic=True, coverage="Listed combinations only; absence is uncertain."))
# A near-duplicate with a different catalog identifier and matching description.
near = {**parts[0], "id": 41, "oem_number": "DEMO-BMW-ALT-002", "evidence": "parts_catalog.json#DEMO-BMW-ALT-002"}
parts.append(near)
compatibility.append({**compatibility[0], "oem_number": near["oem_number"], "evidence": "compatibility.json#DEMO-BMW-ALT-002"})
folder = root / "knowledge"
folder.mkdir(exist_ok=True)
(folder / "parts_catalog.json").write_text(json.dumps(parts, indent=2), encoding="utf-8")
(folder / "compatibility.json").write_text(json.dumps(compatibility, indent=2), encoding="utf-8")
(folder / "example_cases.json").write_text(json.dumps([{"request":"Process BMW alternator OEM DEMO-BMW-ALT-001", "procedure":"Identify, check fitment, check stock and duplicates, calculate price, draft listing, request approval."}], indent=2), encoding="utf-8")

