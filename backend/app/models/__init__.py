from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import String, ForeignKey, JSON, Numeric, DateTime, Date, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db import Base


def now():
    return datetime.now(timezone.utc)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(primary_key=True)
    vin: Mapped[str] = mapped_column(String(30), unique=True)
    manufacturer: Mapped[str]
    model: Mapped[str]
    generation: Mapped[str]
    year: Mapped[int]
    engine: Mapped[str]
    fuel_type: Mapped[str]


class Part(Base):
    __tablename__ = "parts"
    id: Mapped[int] = mapped_column(primary_key=True)
    oem_number: Mapped[str] = mapped_column(String(80), unique=True)
    category: Mapped[str]
    name: Mapped[str]
    manufacturer: Mapped[str]
    condition: Mapped[str]
    source_vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"))
    compatibility_metadata: Mapped[dict] = mapped_column(JSON)


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    __table_args__ = (CheckConstraint("quantity >= 0"), CheckConstraint("asking_price >= 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    part_id: Mapped[int] = mapped_column(ForeignKey("parts.id"), index=True)
    internal_sku: Mapped[str] = mapped_column(String(80), unique=True)
    quantity: Mapped[int]
    warehouse_location: Mapped[str]
    acquisition_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str]
    asking_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    condition: Mapped[str] = mapped_column(default="good", server_default="good")


class HistoricalSale(Base):
    __tablename__ = "historical_sales"
    id: Mapped[int] = mapped_column(primary_key=True)
    part_id: Mapped[int] = mapped_column(ForeignKey("parts.id"))
    sale_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    sold_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    days_in_inventory: Mapped[int]


class Listing(Base):
    __tablename__ = "listings"
    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    title: Mapped[str]
    description: Mapped[str]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    marketplace: Mapped[str] = mapped_column(default="mock")
    status: Mapped[str] = mapped_column(default="draft")
    facts: Mapped[dict] = mapped_column(JSON, default=dict)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    customer_reference: Mapped[str]
    status: Mapped[str]
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_request: Mapped[str]
    status: Mapped[str]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    final_response: Mapped[dict] = mapped_column(JSON, default=dict)
    state: Mapped[dict] = mapped_column(JSON, default=dict)


class ToolExecution(Base):
    __tablename__ = "tool_executions"
    id: Mapped[int] = mapped_column(primary_key=True)
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    selected_skill: Mapped[str]
    tool_name: Mapped[str]
    input: Mapped[dict] = mapped_column(JSON)
    output: Mapped[dict] = mapped_column(JSON)
    execution_status: Mapped[str]
    duration: Mapped[float]
    summary: Mapped[str]
    error: Mapped[str | None]


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    action_type: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution: Mapped[dict] = mapped_column(JSON, default=dict)


class MarketplaceRecord(Base):
    __tablename__ = "marketplace_records"
    __table_args__ = (UniqueConstraint("listing_id"), UniqueConstraint("approval_id"))
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    approval_id: Mapped[int] = mapped_column(ForeignKey("approval_requests.id"))
    external_id: Mapped[str] = mapped_column(unique=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(default="active")

