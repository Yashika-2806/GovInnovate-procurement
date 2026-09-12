from pydantic import BaseModel
from typing import Optional

class Remediation(BaseModel):
    remediation_id: str
    milestone_id: str
    description: str
    action_plan: str
    status: str = "proposed"
