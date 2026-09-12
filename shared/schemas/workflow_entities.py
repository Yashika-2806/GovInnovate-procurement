from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from .base_entities import Evidence

class HumanReview(BaseModel):
    review_id: str
    entity_id: str
    decision: str  # e.g., "approved", "rejected"
    comments: Optional[str] = None
    reviewer: Optional[str] = None

class Allocation(BaseModel):
    allocation_id: str
    startup_id: str
    opportunity_id: str

class Pilot(BaseModel):
    pilot_id: str
    allocation_id: str
    status: str

class Milestone(BaseModel):
    milestone_id: str
    title: str
    requirements: List[str]
    pilot_id: str

class Startup(BaseModel):
    startup_id: str
    name: str
    domain: str

class PerformanceProfile(BaseModel):
    profile_id: str
    startup_id: str
    metrics: Dict[str, Any]

class ScaleRecommendation(BaseModel):
    recommendation_id: str
    recommendation: str
    supported_by: Evidence
