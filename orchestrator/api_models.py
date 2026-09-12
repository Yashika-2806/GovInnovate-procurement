from pydantic import BaseModel
from typing import Dict, Any, Optional

class StateUpdateRequest(BaseModel):
    workflow_id: str
    new_state: str
    event: str
    reason: str

class HumanDecisionRequest(BaseModel):
    workflow_id: str
    decision: str
    comments: Optional[str] = None
