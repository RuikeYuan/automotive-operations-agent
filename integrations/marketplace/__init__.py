import os
from sqlalchemy import select
from backend.app.models import ApprovalRequest, Listing, MarketplaceRecord


class PolicyError(ValueError):
    pass


def authorized(session, approval_id, action, listing_id):
    approval = session.get(ApprovalRequest, approval_id) if approval_id else None
    if not approval or approval.status != "executing" or approval.action_type != action or approval.payload.get("listing_id") != listing_id:
        raise PolicyError("An executing human approval for this exact action is required")
    if os.getenv("MARKETPLACE_FAIL", "false").lower() == "true":
        raise ConnectionError("Mock marketplace is unavailable")
    return approval


class MockMarketplaceClient:
    """Local transactional fake. No HTTP, credentials or real publishing capabilities."""
    def create_listing(self, session, listing, approval_id):
        authorized(session, approval_id, "publish_listing", listing.id)
        existing = session.scalar(select(MarketplaceRecord).where(MarketplaceRecord.listing_id == listing.id))
        if existing:
            return existing
        record = MarketplaceRecord(listing_id=listing.id, approval_id=approval_id, external_id=f"MOCK-{listing.id:06}", payload={"title":listing.title, "price":float(listing.price), "facts":listing.facts}, status="active")
        session.add(record)
        session.flush()
        return record

    def update_listing(self, session, listing_id, price, approval_id):
        approval = authorized(session, approval_id, "update_listing", listing_id)
        if approval.payload.get("price") != price:
            raise PolicyError("Price does not match the approved snapshot")
        listing = session.get(Listing, listing_id)
        record = session.scalar(select(MarketplaceRecord).where(MarketplaceRecord.listing_id == listing_id))
        if not listing or not record:
            raise ValueError("Published mock listing not found")
        listing.price = price
        record.payload = {**record.payload, "price":price}
        return record

    def deactivate_listing(self, session, listing_id, approval_id):
        authorized(session, approval_id, "deactivate_listing", listing_id)
        record = session.scalar(select(MarketplaceRecord).where(MarketplaceRecord.listing_id == listing_id))
        if not record:
            raise ValueError("Published mock listing not found")
        record.status = "inactive"
        session.get(Listing, listing_id).status = "inactive"
        return record

