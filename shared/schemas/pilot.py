from pydantic import BaseModel
from typing import Optional

class Pilot(BaseModel):
    pilot_id: str
    description: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "active"
