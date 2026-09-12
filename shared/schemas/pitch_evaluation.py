from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from .base_entities import Evidence

class PitchEvaluation(BaseModel):
    pitch_evaluation_id: str
    pitch_id: str
    startup_id: str
    criterion_scores: Dict[str, int]
    weighted_total: int
    confidence: float
    evidence_quality: float
    evidence_citations: List[Evidence]
    strengths: List[str]
    weaknesses: List[str]
    missing_information: List[str]
    uncertainties: List[str]
    explanation: str

    class Config:
        populate_by_name = True
