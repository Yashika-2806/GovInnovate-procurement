from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from .base_entities import Evidence

class AuditEvent(BaseModel):
    audit_event_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    workflow_id: str
    entity_id: str
    event_type: str
    reason: str
    relevant_agent: Optional[str] = None
    success: bool
    evidence_references: List[Evidence] = Field(default_factory=list)
