from datetime import date, datetime, time, timezone, timedelta
from difflib import SequenceMatcher
from uuid import uuid4
from sqlalchemy import select
from backend.app.models import Part, InventoryItem, HistoricalSale, Listing, Order, Vehicle
from backend.app.schemas import ToolInput, ToolResult
from backend.app.retrieval import LocalKnowledge
from backend.app.services.pricing import calculate_price
from integrations.marketplace import PolicyError


def inventory_row(item, part):
    return {"id":item.id, "part_id":part.id, "oem_number":part.oem_number, "name":part.name, "manufacturer":part.manufacturer, "category":part.category, "condition":item.condition, "internal_sku":item.internal_sku, "quantity":item.quantity, "warehouse_location":item.warehouse_location, "status":item.status, "asking_price":float(item.asking_price), "acquisition_date":item.acquisition_date.isoformat()}


class Tools:
    def __init__(self, session, knowledge=None):
        self.session = session
        self.knowledge = knowledge or LocalKnowledge()

    def call(self, name, raw):
        args = ToolInput.model_validate(raw)
        allowed = {"search_parts_catalog", "lookup_oem", "check_vehicle_compatibility", "search_inventory", "get_inventory_item", "create_inventory_draft", "find_duplicates", "get_historical_sales", "calculate_suggested_price", "generate_listing_draft", "get_orders", "prepare_order", "publish_marketplace_listing"}
        if name not in allowed:
            raise ValueError("Unknown tool")
        result = getattr(self, name)(args)
        return ToolResult.model_validate(result).model_dump()

    def _part(self, args):
        part = self.session.get(Part, args.part_id) if args.part_id else self.session.scalar(select(Part).where(Part.oem_number == args.oem_number))
        if not part:
            raise ValueError("Part not found")
        return part

    def search_parts_catalog(self, a):
        rows = self.knowledge.search(a.category or a.query, a.manufacturer)
        if a.category:
            rows = [r for r in rows if r["category"].lower() == a.category.lower()]
        if a.model:
            rows = [r for r in rows if r["model"].lower() == a.model.lower()]
        if a.year:
            rows = [r for r in rows if r["year"] == a.year]
        if a.vin:
            vehicle = self.session.scalar(select(Vehicle).where(Vehicle.vin == a.vin))
            rows = [r for r in rows if vehicle and r["source_vehicle_id"] == vehicle.id]
        return {"data":{"candidate_parts":rows, "confidence":.8 if len(rows)==1 else .4 if rows else 0, "missing_information":[] if len(rows)==1 else ["oem_number"], "recommended_next_action":"verify_candidate" if len(rows)==1 else "ask_for_oem"}, "evidence":[r["evidence"] for r in rows]}

    def lookup_oem(self, a):
        row = self.knowledge.lookup(a.oem_number)
        return {"data":{"candidate_parts":[row] if row else [], "confidence":1 if row else 0, "missing_information":[] if row else ["valid_oem_number"], "recommended_next_action":"verify_attributes" if row else "ask_for_oem"}, "evidence":[row["evidence"]] if row else []}

    def check_vehicle_compatibility(self, a):
        part = self._part(a)
        record = self.knowledge.fitment(part.oem_number)
        vehicles = record["vehicles"] if record else []
        target_given = any((a.manufacturer, a.model, a.year))
        complete = all((a.manufacturer, a.model, a.year))
        matches = [v for v in vehicles if (not a.manufacturer or v["manufacturer"].lower()==a.manufacturer.lower()) and (not a.model or v["model"].lower()==a.model.lower()) and (not a.year or v["year"]==a.year)]
        # Positive fitment requires all target fields, or returns a catalog list without a target claim.
        status = "compatible" if (complete and matches) or (not target_given and vehicles) else "uncertain"
        exclusions = record.get("incompatible_vehicles", []) if record else []
        if complete and any(v["manufacturer"].lower()==a.manufacturer.lower() and v["model"].lower()==a.model.lower() and v["year"]==a.year for v in exclusions):
            status = "incompatible"
        return {"data":{"status":status, "vehicles":matches if target_given else vehicles, "scope":"synthetic catalog only", "missing_information":[] if not target_given or complete else ["complete_target_vehicle"]}, "evidence":[record["evidence"]] if record else []}

    def search_inventory(self, a):
        statement = select(InventoryItem, Part).join(Part)
        if a.part_id:
            statement = statement.where(Part.id==a.part_id)
        if a.oem_number:
            statement = statement.where(Part.oem_number==a.oem_number)
        if a.manufacturer:
            statement = statement.where(Part.manufacturer==a.manufacturer)
        if a.category:
            statement = statement.where(Part.category==a.category)
        if a.query:
            statement = statement.where((Part.name.ilike(f"%{a.query}%")) | (Part.oem_number.ilike(f"%{a.query}%")) | (InventoryItem.internal_sku.ilike(f"%{a.query}%")))
        rows = [inventory_row(i,p) for i,p in self.session.execute(statement.order_by(InventoryItem.id).limit(500))]
        return {"data":{"items":rows, "record_count":len(rows), "available_quantity":sum(i["quantity"] for i in rows if i["status"]=="available")}, "evidence":["sql:inventory_items"]}

    def get_inventory_item(self, a):
        item = self.session.get(InventoryItem, a.inventory_item_id)
        if not item:
            raise LookupError("Inventory item not found")
        return {"data":inventory_row(item, self.session.get(Part,item.part_id)), "evidence":[f"sql:inventory_items/{item.id}"]}

    def find_duplicates(self, a):
        part = self._part(a)
        rows = self.session.execute(select(InventoryItem,Part).join(Part).where(InventoryItem.status != "rejected")).all()
        candidates = []
        for item, other in rows:
            exact = part.oem_number == other.oem_number
            similarity = SequenceMatcher(None, part.name.lower(), other.name.lower()).ratio()
            same_vehicle = part.source_vehicle_id == other.source_vehicle_id
            if exact or (part.manufacturer == other.manufacturer and part.category==other.category and similarity>=.8):
                candidates.append({**inventory_row(item,other), "probability":1 if exact else round(similarity*.8,2), "reasons":(["exact OEM"] if exact else ["similar description and category"])+(["same source vehicle"] if same_vehicle else [])})
        return {"data":{"duplicate_probability":max((r["probability"] for r in candidates),default=0), "candidate_records":candidates, "recommended_action":"review_physical_items_before_publishing" if candidates else "continue"}, "evidence":["sql:inventory_items", "sql:parts"]}

    def get_historical_sales(self, a):
        part = self._part(a)
        rows = self.session.scalars(select(HistoricalSale).where(HistoricalSale.part_id==part.id)).all()
        return {"data":{"sales":[{"id":s.id,"sale_price":float(s.sale_price),"days_in_inventory":s.days_in_inventory,"sold_at":s.sold_at.isoformat()} for s in rows]}, "evidence":[f"sql:historical_sales?part_id={part.id}"]}

    def calculate_suggested_price(self, a):
        part = self._part(a)
        reference = self.knowledge.lookup(part.oem_number)
        history = self.get_historical_sales(a)["data"]["sales"]
        inventory = self.search_inventory(ToolInput(part_id=part.id))["data"]["items"]
        available = [i for i in inventory if i["status"]=="available"]
        age = max(((date.today()-date.fromisoformat(i["acquisition_date"])).days for i in available),default=0)
        result = calculate_price([s["sale_price"] for s in history],a.condition,sum(i["quantity"] for i in available),age,reference["market_reference"],reference["acquisition_cost"])
        return {"data":result, "evidence":[reference["evidence"], f"sql:historical_sales?part_id={part.id}", "sql:inventory_items"]}

    def create_inventory_draft(self, a):
        part = self._part(a)
        if a.price is None:
            raise ValueError("Draft price is required")
        item = InventoryItem(part_id=part.id, internal_sku=f"DRAFT-{uuid4().hex[:12].upper()}", quantity=1, warehouse_location="INTAKE-REVIEW", acquisition_date=date.today(), status="draft", asking_price=a.price, condition=a.condition)
        self.session.add(item)
        self.session.flush()
        return {"data":inventory_row(item,part), "evidence":[f"sql:inventory_items/{item.id}"]}

    def generate_listing_draft(self, a):
        item = self.session.get(InventoryItem,a.inventory_item_id)
        if not item or item.status != "draft":
            raise PolicyError("Only isolated draft stock can receive a new listing")
        part = self.session.get(Part,item.part_id)
        fitment = self.check_vehicle_compatibility(ToolInput(part_id=part.id))
        facts = {"oem_number":part.oem_number,"condition":item.condition,"sku":item.internal_sku,"compatibility":fitment["data"],"synthetic":True,"evidence":fitment["evidence"]}
        description = f"Recycled {part.name}. OEM: {part.oem_number}. Condition: {item.condition}. SKU: {item.internal_sku}. Synthetic demo fitment only; verify physical identification before use. Warranty: not specified."
        listing = Listing(inventory_item_id=item.id,title=f"{part.name} | {part.oem_number}",description=description,price=item.asking_price,marketplace="mock",status="draft",facts=facts)
        self.session.add(listing)
        self.session.flush()
        return {"data":{"listing_id":listing.id,"title":listing.title,"description":description,"price":float(listing.price),"currency":"EUR","status":"draft","facts":facts,"marketing_copy":"Reusable OEM-style component from our synthetic recycling inventory."},"evidence":[f"sql:listings/{listing.id}",*fitment["evidence"]]}

    def get_orders(self, a):
        statement = select(Order,Part).join(Listing,Order.listing_id==Listing.id).join(InventoryItem,Listing.inventory_item_id==InventoryItem.id).join(Part,InventoryItem.part_id==Part.id)
        if a.order_id:
            statement = statement.where(Order.id==a.order_id)
        if a.status:
            statement = statement.where(Order.status==a.status)
        if a.manufacturer:
            statement = statement.where(Part.manufacturer==a.manufacturer)
        if a.today:
            start = datetime.combine(datetime.now(timezone.utc).date(),time.min,tzinfo=timezone.utc)
            statement = statement.where(Order.created_at>=start,Order.created_at<start+timedelta(days=1))
        rows = [{"id":o.id,"listing_id":o.listing_id,"manufacturer":p.manufacturer,"customer_reference":o.customer_reference,"status":o.status,"amount":float(o.amount),"created_at":o.created_at.isoformat()} for o,p in self.session.execute(statement.order_by(Order.id).limit(500))]
        return {"data":{"orders":rows},"evidence":["sql:orders"]}

    def prepare_order(self, a):
        raise PolicyError("Order state changes execute only inside the approval service")

    def publish_marketplace_listing(self, a):
        raise PolicyError("The agent tool boundary cannot publish; use the human approval endpoint")

