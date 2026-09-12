from pydantic import BaseModel
from typing import Dict

class PerformanceProfile(BaseModel):
    startup_id: str
    metrics: Dict[str, float]
    summary: str
