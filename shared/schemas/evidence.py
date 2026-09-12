from pydantic import BaseModel
from typing import Optional

class Evidence(BaseModel):
    evidence_id: str
    milestone_id: str
    description: str
    link: str
    status: str = "submitted" # submitted, verified, rejected
