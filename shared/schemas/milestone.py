from pydantic import BaseModel
from typing import Optional

class Milestone(BaseModel):
    milestone_id: str
    description: str
    due_date: str
    status: str = "pending" # pending, active, completed, failed
