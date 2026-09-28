from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Entities(StrictModel):
    oem_number: str | None = Field(default=None, pattern=r"^DEMO-[A-Z0-9]+-[A-Z0-9]+-[0-9]{3}$", max_length=80)
    manufacturer: str | None = Field(default=None, max_length=60)
    model: str | None = Field(default=None, max_length=80)
    year: int | None = Field(default=None, ge=1950, le=2100)
    vin: str | None = Field(default=None, max_length=40)
    category: str | None = Field(default=None, max_length=80)
    condition: Literal["good", "fair", "excellent", "untested"] = "good"
    order_id: int | None = Field(default=None, gt=0)
    target_manufacturer: str | None = Field(default=None, max_length=60)
    target_model: str | None = Field(default=None, max_length=80)
    target_year: int | None = Field(default=None, ge=1950, le=2100)


class RunRequest(StrictModel):
    request: str = Field(min_length=3, max_length=4000)
    entities: Entities = Field(default_factory=Entities)


class Plan(StrictModel):
    intent: Literal["process_part", "identify", "inventory", "compatibility", "pricing", "orders", "prepare_order", "unsupported"]
    entities: Entities = Field(default_factory=Entities)


class ToolInput(StrictModel):
    query: str = Field(default="", max_length=4000)
    oem_number: str | None = Field(default=None, pattern=r"^DEMO-[A-Z0-9]+-[A-Z0-9]+-[0-9]{3}$")
    manufacturer: str | None = None
    model: str | None = None
    year: int | None = Field(default=None, ge=1950, le=2100)
    category: str | None = None
    vin: str | None = None
    part_id: int | None = Field(default=None, gt=0)
    inventory_item_id: int | None = Field(default=None, gt=0)
    listing_id: int | None = Field(default=None, gt=0)
    order_id: int | None = Field(default=None, gt=0)
    approval_id: int | None = Field(default=None, gt=0)
    condition: Literal["good", "fair", "excellent", "untested"] = "good"
    price: float | None = Field(default=None, ge=0, le=1000000)
    status: str | None = None
    today: bool = False


class ToolResult(StrictModel):
    data: dict
    evidence: list[str] = Field(default_factory=list)
    synthetic: bool = True


class InventoryLocationChange(StrictModel):
    warehouse_location: str = Field(min_length=1,max_length=80,pattern=r"^[A-Za-z0-9][A-Za-z0-9 _-]*$")

