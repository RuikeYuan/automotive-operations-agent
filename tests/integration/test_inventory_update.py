from backend.app.models import InventoryItem


def test_location_update_is_reviewed(client,session):
    before = session.get(InventoryItem,1).warehouse_location
    proposed = client.patch("/inventory/1",json={"warehouse_location":"B-99"})
    assert proposed.status_code==202
    assert session.get(InventoryItem,1).warehouse_location==before
    aid = proposed.json()["id"]
    assert client.post(f"/approvals/{aid}/approve",json={}).status_code==200
    assert session.get(InventoryItem,1).warehouse_location=="B-99"


def test_price_and_arbitrary_inventory_mutations_rejected(client):
    assert client.patch("/inventory/1",json={"asking_price":1}).status_code==422
    assert client.patch("/inventory/1",json={"warehouse_location":"B-99","quantity":999}).status_code==422
    assert client.patch("/inventory/9999",json={"warehouse_location":"B-99"}).status_code==404

