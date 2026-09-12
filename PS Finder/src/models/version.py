from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FieldDiff(BaseModel):
    field_name: str
    old_value: Any
    new_value: Any


class OpportunityVersion(BaseModel):
    """Historical version snapshot when an opportunity's content/status changes."""
    version_number: int
    opportunity_id: str
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    change_reason: str = Field("source_update", description="Reason for version creation (e.g. deadline_extended, status_changed)")
    diffs: List[FieldDiff] = Field(default_factory=list)
    snapshot: Dict[str, Any] = Field(default_factory=dict, description="Full state snapshot at this version")
