import json
from datetime import date, timedelta
from sqlalchemy import select, text
from backend.app.config import ROOT
from backend.app.db import SessionLocal
from backend.app.models import Vehicle, Part, InventoryItem, HistoricalSale, Listing, Order, now


def sync_sequences(session):
    # Seed rows use explicit ids; PostgreSQL sequences must move past them.
    if session.get_bind().dialect.name != "postgresql":
        return
    for model in (Vehicle, Part, InventoryItem, Listing, Order):
        table = model.__tablename__
        session.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)"))
    session.commit()


def seed(session):
    if session.scalar(select(Vehicle.id).limit(1)):
        sync_sequences(session)
        return
    catalog = json.loads((ROOT / "knowledge/parts_catalog.json").read_text(encoding="utf-8"))
    fits = {r["oem_number"]: r for r in json.loads((ROOT / "knowledge/compatibility.json").read_text(encoding="utf-8"))}
    for index, brand in enumerate(["BMW", "Volkswagen", "Mercedes-Benz", "Audi", "Toyota"], 1):
        row = next(p for p in catalog if p["manufacturer"] == brand)
        session.add(Vehicle(id=index, vin=f"DEMO-VIN-{index:09}", manufacturer=brand, model=row["model"], generation=row["generation"], year=2019, engine="2.0 petrol demo", fuel_type="petrol"))
    session.flush()
    for row in catalog:
        session.add(Part(**{k: row[k] for k in ("id", "oem_number", "category", "name", "manufacturer", "condition", "source_vehicle_id")}, compatibility_metadata=fits[row["oem_number"]]))
    session.flush()
    for row in catalog:
        # Toyota sensor has no inventory or historical sales; other sensors have no sales.
        if row["id"] != 40:
            session.add(InventoryItem(id=row["id"], part_id=row["id"], internal_sku=f"STOCK-{row['id']:04}", quantity=1, warehouse_location=f"{chr(65+(row['id']-1)//8)}-{(row['id']-1)%8+1:02}", acquisition_date=date.today()-timedelta(days=45), status="available", asking_price=row["market_reference"]))
        if row["category"] != "sensor":
            for offset, factor in enumerate((.9, 1, 1.1)):
                session.add(HistoricalSale(part_id=row["id"], sale_price=round(row["market_reference"]*factor,2), sold_at=now()-timedelta(days=offset*10+5), days_in_inventory=25+offset*10))
    session.add(InventoryItem(id=42, part_id=1, internal_sku="STOCK-BMW-ALT-DUP", quantity=1, warehouse_location="A-09", acquisition_date=date.today()-timedelta(days=100), status="available", asking_price=190))
    session.flush()
    for index, item_id in enumerate((1, 17, 25), 1):
        session.add(Listing(id=index, inventory_item_id=item_id, title=f"Synthetic example listing {index}", description="Seeded order listing; no real marketplace activity.", price=200, marketplace="mock", status="published", facts={"synthetic":True}))
    session.flush()
    for index in range(1,4):
        session.add(Order(id=1023+index, listing_id=index, customer_reference=f"DEMO-CUSTOMER-{index}", status="awaiting_shipment", amount=200, created_at=now()))
    session.commit()
    sync_sequences(session)


if __name__ == "__main__":
    with SessionLocal() as session:
        seed(session)
    print("Synthetic seed ready (idempotent).")

