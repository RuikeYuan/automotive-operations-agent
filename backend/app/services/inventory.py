from uuid import uuid4
from backend.app.models import InventoryItem, AgentRun, ApprovalRequest


def propose_location_change(session,item_id,location):
    item = session.get(InventoryItem,item_id)
    if not item:
        raise LookupError("Inventory item not found")
    run = AgentRun(id=str(uuid4()),user_request=f"Move inventory {item_id} to {location}",status="awaiting_approval",state={"intent":"inventory_location","provider":"direct-structured-request","skills":["inventory-management"],"plan":[],"completed_steps":["propose_inventory_location"],"pending_steps":["human_approval"],"approval_required":True,"status":"awaiting_approval","warnings":[]},final_response={})
    session.add(run)
    session.flush()
    approval = ApprovalRequest(agent_run_id=run.id,action_type="inventory_location",payload={"inventory_item_id":item.id,"internal_sku":item.internal_sku,"previous_location":item.warehouse_location,"warehouse_location":location},status="pending")
    session.add(approval)
    session.flush()
    run.final_response = {"approval_id":approval.id,"message":"Review inventory location change before execution."}
    session.commit()
    return approval

