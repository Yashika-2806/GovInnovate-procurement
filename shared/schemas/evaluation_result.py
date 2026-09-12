from pydantic import BaseModel, Field
from typing import List, Optional
from .base_entities import Evidence

class KpiMeasurement(BaseModel):
    name: str
    target: float
    actual: float
    achieved: bool

class EvaluationResult(BaseModel):
    evaluation_id: str
    milestone_id: str
    status: str # PASS/FAIL
    kpi_measurements: List[KpiMeasurement]
    evidence_submitted: List[Evidence]
    explanation: str
    confidence: float
    remediation_required: Optional[str] = None
    recommendation: str

    class Config:
        populate_by_name = True
