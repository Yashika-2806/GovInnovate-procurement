from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class OpportunityStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"

class Opportunity(BaseModel):
    id: str = Field(..., alias="opportunity_id")
    title: str
    description: str
    organization: str
    status: OpportunityStatus
    deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
