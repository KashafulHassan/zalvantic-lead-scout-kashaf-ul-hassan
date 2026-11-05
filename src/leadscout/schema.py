from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class BudgetBand(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    unknown = "unknown"


class Lead(BaseModel):
    lead_id: str
    name: str
    company: str
    need: str = Field(..., description="Free-text description of what the lead wants")
    budget_band: BudgetBand
    timeline_weeks: Optional[int] = Field(None, ge=1, le=52)
    country: str