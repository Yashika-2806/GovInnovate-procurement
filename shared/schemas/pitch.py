from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class Pitch(BaseModel):
    id: str = Field(..., alias="pitch_id")
    startup_id: str
    opportunity_id: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
