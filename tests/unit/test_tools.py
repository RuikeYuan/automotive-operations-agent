import pytest
from backend.app.tools import Tools
from backend.app.schemas import ToolInput
from backend.app.services.pricing import calculate_price
from backend.app.retrieval import LocalKnowledge
from backend.app.models import InventoryItem


def test_pricing_formula():
    result = calculate_price([180,200,220],"good",2,100,200,90)
    assert result["suggested_price"] == 180.5
    assert result["price_range"] == {"min":162.45,"max":198.55}
    assert result["confidence"] == .85


def test_pricing_floor_and_no_history():
    result = calculate_price([],"untested",5,200,100,90)
    assert result["suggested_price"] == 112.5
    assert result["confidence"] == .3
    assert result["factors"][0]["source"]=="synthetic_market_reference"


@pytest.mark.parametrize("condition,stock,age",[("invalid",1,0),("good",-1,0),("good",1,-1)])
def test_bad_pricing_inputs(condition,stock,age):
    with pytest.raises(ValueError):
        calculate_price([100],condition,stock,age,100,50)


def test_catalog_and_unknown_oem(session):
    tools = Tools(session)
    exact = tools.call("lookup_oem",{"oem_number":"DEMO-BMW-ALT-001"})
    assert exact["data"]["candidate_parts"][0]["name"]=="BMW Alternator"
    assert exact["evidence"] == ["parts_catalog.json#DEMO-BMW-ALT-001"]
    assert tools.call("lookup_oem",{"oem_number":"DEMO-BMW-ALT-999"})["data"]["candidate_parts"] == []
    assert len(tools.call("search_parts_catalog",{"manufacturer":"BMW","category":"alternator"})["data"]["candidate_parts"])==2


def test_compatibility_evidence_and_uncertainty(session):
    tools = Tools(session)
    known = tools.call("check_vehicle_compatibility",{"part_id":1,"manufacturer":"BMW","model":"3 Series","year":2019})
    assert known["data"]["status"]=="compatible"
    assert known["evidence"]
    assert tools.call("check_vehicle_compatibility",{"part_id":1,"manufacturer":"BMW","model":"3 Series","year":2030})["data"]["status"]=="uncertain"
    assert tools.call("check_vehicle_compatibility",{"part_id":1,"manufacturer":"BMW"})["data"]["status"]=="uncertain"
    assert tools.call("check_vehicle_compatibility",{"part_id":40})["data"]["status"]=="uncertain"


def test_explicit_incompatible_record(session):
    knowledge = LocalKnowledge()
    knowledge.compatibility[0]["incompatible_vehicles"]=[{"manufacturer":"Toyota","model":"Corolla","year":2019}]
    result = Tools(session,knowledge).call("check_vehicle_compatibility",{"part_id":1,"manufacturer":"Toyota","model":"Corolla","year":2019})
    assert result["data"]["status"]=="incompatible"


def test_duplicate_exact_near_and_none(session):
    tools = Tools(session)
    result = tools.call("find_duplicates",{"part_id":1})["data"]
    assert len(result["candidate_records"])==3
    assert sum(r["probability"]==1 for r in result["candidate_records"])==2
    assert any("similar description and category" in r["reasons"] for r in result["candidate_records"])
    assert tools.call("find_duplicates",{"part_id":40})["data"]["duplicate_probability"]==0


def test_draft_tools_and_grounded_listing(session):
    tools = Tools(session)
    draft = tools.call("create_inventory_draft",{"part_id":40,"price":65,"condition":"fair"})["data"]
    listing = tools.call("generate_listing_draft",{"inventory_item_id":draft["id"],"condition":"fair"})["data"]
    assert listing["status"]=="draft"
    assert listing["facts"]["compatibility"]["status"]=="uncertain"
    assert listing["facts"]["compatibility"]["vehicles"]==[]
    assert listing["facts"]["condition"]=="fair"
    assert draft["condition"]=="fair"
    assert tools.call("get_inventory_item",{"inventory_item_id":draft["id"]})["data"]["status"]=="draft"
    assert tools.call("search_inventory",{"part_id":40})["data"]["available_quantity"]==0


def test_orders_filter_and_history(session):
    tools = Tools(session)
    assert [o["id"] for o in tools.call("get_orders",{"manufacturer":"Mercedes-Benz","today":True})["data"]["orders"]]==[1025]
    assert len(tools.call("get_historical_sales",{"part_id":1})["data"]["sales"])==3
    assert tools.call("calculate_suggested_price",{"part_id":1})["data"]["suggested_price"]==180.5

