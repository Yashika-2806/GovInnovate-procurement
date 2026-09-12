from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Type of evidence supporting a claim."""

    DIRECT_QUOTE = "direct_quote"
    PARAPHRASE = "paraphrase"
    VISUAL_OBSERVATION = "visual_observation"
    DOCUMENT_EXCERPT = "document_excerpt"
    DATA_POINT = "data_point"


class VerificationLevel(str, Enum):
    """Verification level of evidence."""

    SELF_REPORTED = "self_reported"
    SYSTEM_GENERATED = "system_generated"
    THIRD_PARTY = "third_party"
    INDEPENDENTLY_VERIFIED = "independently_verified"
    UNKNOWN = "unknown"


class SegmentRef(BaseModel):
    """Reference to a pitch segment as evidence."""

    segment_id: str
    source_modality: str
    start_ref: Annotated[int, Field(ge=0)]
    end_ref: Annotated[int, Field(ge=0)]
    excerpt: str


class EvidenceCitation(BaseModel):
    """Evidence citation linking a claim to source segments."""

    claim: Annotated[str, Field(min_length=1)]
    criterion: Annotated[str, Field(min_length=1)]
    source_segments: Annotated[list[SegmentRef], Field(min_length=1)]
    evidence_type: EvidenceType
    verification_level: VerificationLevel
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    notes: str | None = None