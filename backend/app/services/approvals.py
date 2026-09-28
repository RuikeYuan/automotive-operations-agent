from time import perf_counter
from sqlalchemy import update, select
from backend.app.models import ApprovalRequest, Listing, InventoryItem, Order, AgentRun, ToolExecution, now
from integrations.marketplace import MockMarketplaceClient, PolicyError


def listing_snapshot(listing):
    return {"listing_id":listing.id, "inventory_item_id":listing.inventory_item_id, "title":listing.title, "description":listing.description, "price":float(listing.price), "facts":listing.facts, "marketplace":listing.marketplace}


def request_publish(session, run_id, listing):
    request = ApprovalRequest(agent_run_id=run_id, action_type="publish_listing", payload=listing_snapshot(listing), status="pending")
    session.add(request)
    session.flush()
    return request


def publish_approved(session, listing_id, approval_id):
    approval = session.get(ApprovalRequest, approval_id) if approval_id else None
    listing = session.get(Listing, listing_id)
    if not approval or approval.status != "executing" or approval.action_type != "publish_listing":
        raise PolicyError("Publishing requires explicit human approval")
    if not listing or listing.status != "draft" or approval.payload != listing_snapshot(listing):
        raise PolicyError("Draft changed since approval was requested")
    item = session.get(InventoryItem, listing.inventory_item_id)
    if not item or item.quantity < 1 or item.status != "draft":
        raise PolicyError("Draft stock is no longer publishable")
    record = MockMarketplaceClient().create_listing(session, listing, approval_id)
    listing.status = "published"
    item.status = "available"
    return {"external_id":record.external_id, "listing_id":listing.id, "status":"published", "marketplace":"mock"}


def resolve_approval(session, approval_id, approve):
    started = perf_counter()
    # Atomic compare-and-set: at most one transaction can consume the approval.
    claimed = session.execute(update(ApprovalRequest).where(ApprovalRequest.id == approval_id, ApprovalRequest.status == "pending").values(status="executing"))
    if claimed.rowcount != 1:
        session.rollback()
        if not session.get(ApprovalRequest, approval_id):
            raise LookupError("Approval not found")
        raise PolicyError("Approval has already been resolved")
    approval = session.get(ApprovalRequest, approval_id, populate_existing=True)
    run_id, action, payload = approval.agent_run_id, approval.action_type, approval.payload
    tool_name = {"publish_listing":"publish_marketplace_listing", "prepare_order":"prepare_order"}.get(action, action)
    selected_skill = {"publish_listing":"marketplace-publishing", "prepare_order":"order-processing", "inventory_location":"inventory-management"}.get(action,"unknown")
    try:
        if not approve:
            result = {"status":"rejected", "action":action}
        elif action == "publish_listing":
            result = publish_approved(session, payload["listing_id"], approval_id)
        elif action == "prepare_order":
            order = session.get(Order, payload["order_id"])
            if not order or order.status != payload["previous_status"]:
                raise PolicyError("Order changed since approval was requested")
            order.status = "processing"
            result = {"order_id":order.id, "status":order.status}
        elif action == "inventory_location":
            item = session.get(InventoryItem,payload["inventory_item_id"])
            if not item or item.warehouse_location != payload["previous_location"]:
                raise PolicyError("Inventory location changed since approval was requested")
            item.warehouse_location = payload["warehouse_location"]
            result = {"inventory_item_id":item.id,"warehouse_location":item.warehouse_location,"status":"updated"}
        else:
            raise PolicyError("Unsupported protected action")
        approval.status = "approved" if approve else "rejected"
        approval.resolved_at, approval.resolution = now(), result
        run = session.get(AgentRun, run_id)
        run.status, run.completed_at = ("completed" if approve else "rejected"), now()
        run.final_response = {**run.final_response, "approval":approval.status, "action_result":result}
        run.state = {**run.state, "approval_required":False, "status":run.status, "pending_steps":[], "completed_steps":[*run.state.get("completed_steps", []), "human_approval"]}
        session.add(ToolExecution(agent_run_id=run_id, selected_skill=selected_skill, tool_name=tool_name if approve else "reject_action", input={"approval_id":approval_id}, output=result, execution_status="success", duration=(perf_counter()-started)*1000, summary="Employee reviewed the stored action snapshot.", error=None))
        session.commit()
        return approval
    except Exception as error:
        session.rollback()
        # A failed mock operation is rolled back entirely; approval remains retryable.
        session.add(ToolExecution(agent_run_id=run_id, selected_skill=selected_skill, tool_name=tool_name, input={"approval_id":approval_id}, output={}, execution_status="error", duration=(perf_counter()-started)*1000, summary="Approved action failed; transaction rolled back and no publication occurred.", error=type(error).__name__))
        session.commit()
        raise

