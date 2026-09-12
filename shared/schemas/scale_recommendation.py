from pydantic import BaseModel

class ScaleRecommendation(BaseModel):
    recommendation: str # e.g., "SCALE", "DO_NOT_SCALE"
    rationale: str
    confidence_score: float
