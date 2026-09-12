from pydantic import BaseModel, Field
from typing import List, Dict
from .base_entities import Evidence

class RiskItem(BaseModel):
    category: str
    description: str
    severity: str
    evidence: List[Evidence]
    mitigation: Optional[str] = None

class RiskAssessment(BaseModel):
    risk_assessment_id: str
    startup_id: str
    risks: List[RiskItem]
    overall_confidence: float
    uncertainties: List[str]
    unknowns: List[str]

    class Config:
        populate_by_name = True
