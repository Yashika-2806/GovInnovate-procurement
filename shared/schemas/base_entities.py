from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    UNKNOWN = "unknown"
    REQUIRES_VERIFICATION = "requires_verification"

class Provenance(BaseModel):
    source_type: str
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence: float = 0.0

class Evidence(BaseModel):
    id: str = Field(..., alias="evidence_id")
    claim: str
    provenance: Provenance
    content_payload: Dict[str, Any] = Field(default_factory=dict)
