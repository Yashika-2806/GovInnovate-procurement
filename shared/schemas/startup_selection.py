from pydantic import BaseModel
from typing import Optional

class StartupSelection(BaseModel):
    startup_id: str
    selection_reason: str
    selection_date: Optional[str] = None
