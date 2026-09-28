from sqlalchemy import select,func
from backend.app.models import MarketplaceRecord, Listing, ApprovalRequest, InventoryItem, Order
from backend.app.db.seed import seed

REQUEST = {"request":"Process BMW alternator OEM DEMO-BMW-ALT-001. Check duplicates and prepare a marketplace listing."}


def test_bmw_end_to_end(client,session):
    response = client.post("/agent/run",json=REQUEST)
    assert response.status_code==201
    run = response.json()
    assert run["status"]=="awaiting_approval"
    result = run["final_response"]
    assert result["inventory"]["record_count"]==2
    assert result["pricing"]["suggested_price"]==180.5
    assert session.scalar(select(func.count()).select_from(MarketplaceRecord))==0
    trace = client.get(f"/agent/runs/{run['id']}/trace").json()
    assert [t["tool_name"] for t in trace]==["lookup_oem","check_vehicle_compatibility","search_inventory","find_duplicates","get_historical_sales","calculate_suggested_price","create_inventory_draft","generate_listing_draft"]
    assert all(t["execution_status"]=="success" for t in trace)
    approval_id = result["approval_id"]
    approved = client.post(f"/approvals/{approval_id}/approve",json={})
    assert approved.status_code==200
    assert approved.json()["resolution"]["external_id"].startswith("MOCK-")
    assert session.scalar(select(func.count()).select_from(MarketplaceRecord))==1
    assert client.post(f"/approvals/{approval_id}/approve",json={}).status_code==409
    assert client.get(f"/agent/runs/{run['id']}").json()["status"]=="completed"


def test_major_endpoints(client):
    for path in ["/health","/inventory","/inventory/1","/parts/search?q=alternator","/orders","/approvals","/agent/runs","/skills","/listings","/marketplace","/metrics","/openapi.json"]:
        assert client.get(path).status_code==200,path
    for path in ["/inventory/99999","/agent/runs/missing","/agent/runs/missing/trace"]:
        assert client.get(path).status_code==404
    assert client.post("/approvals/99999/approve",json={}).status_code==404
    assert client.post("/agent/run",json={"request":""}).status_code==422
    assert client.post("/agent/run",json={"request":"identify","entities":{"oem_number":"BAD;DROP"}}).status_code==422


def test_ambiguity_unknown_and_malformed(client):
    for text in ["Process BMW alternator","Identify OEM DEMO-BMW-ALT-999","Identify OEM DEMO-BAD"]:
        run = client.post("/agent/run",json={"request":text}).json()
        assert run["status"]=="needs_information"
        assert "listing" not in run["final_response"]


def test_rejection(client,session):
    run = client.post("/agent/run",json=REQUEST).json()
    aid = run["final_response"]["approval_id"]
    assert client.post(f"/approvals/{aid}/reject",json={}).json()["status"]=="rejected"
    assert session.scalar(select(func.count()).select_from(MarketplaceRecord))==0
    assert client.post(f"/approvals/{aid}/approve",json={}).status_code==409


def test_changed_snapshot_is_rejected(client,session):
    run = client.post("/agent/run",json=REQUEST).json()
    result = run["final_response"]
    listing = session.get(Listing,result["listing"]["listing_id"])
    listing.price = 1
    session.commit()
    assert client.post(f"/approvals/{result['approval_id']}/approve",json={}).status_code==409
    assert session.scalar(select(func.count()).select_from(MarketplaceRecord))==0


def test_marketplace_failure_rollback_retry(client,session,monkeypatch):
    run = client.post("/agent/run",json=REQUEST).json()
    aid = run["final_response"]["approval_id"]
    monkeypatch.setenv("MARKETPLACE_FAIL","true")
    assert client.post(f"/approvals/{aid}/approve",json={}).status_code==503
    assert session.get(ApprovalRequest,aid).status=="pending"
    assert session.scalar(select(func.count()).select_from(MarketplaceRecord))==0
    monkeypatch.setenv("MARKETPLACE_FAIL","false")
    assert client.post(f"/approvals/{aid}/approve",json={}).status_code==200


def test_order_requires_review(client,session):
    run = client.post("/agent/run",json={"request":"Prepare order 1024 for processing"}).json()
    assert session.get(Order,1024).status=="awaiting_shipment"
    assert client.post(f"/approvals/{run['final_response']['approval_id']}/approve",json={}).status_code==200
    assert session.get(Order,1024).status=="processing"


def test_seed_idempotency(session):
    before = session.scalar(select(func.count()).select_from(InventoryItem))
    seed(session)
    assert session.scalar(select(func.count()).select_from(InventoryItem))==before

