from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field


class LLMEvidenceCitation(BaseModel):
    """Structured evidence citation from LLM output."""

    claim: Annotated[str, Field(min_length=1, max_length=500)]
    criterion: Annotated[str, Field(min_length=1, max_length=100)]
    source_segment_ids: Annotated[list[str], Field(min_length=1, max_length=10)]
    evidence_type: Annotated[str, Field(pattern=r"^(direct_quote|paraphrase|visual_observation|document_excerpt|data_point)$")]
    verification_level: Annotated[str, Field(pattern=r"^(self_reported|system_generated|third_party|independently_verified|unknown)$")]
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    notes: str | None = None


class LLMEvidenceExtractionOutput(BaseModel):
    """Complete structured output from LLM evidence extraction."""

    citations: Annotated[list[LLMEvidenceCitation], Field(min_length=0, max_length=50)]
    extraction_notes: str | None = None


class EvidenceExtractionRequest(BaseModel):
    """Request for evidence extraction."""

    normalized_pitch: dict[str, Any]  # Serialized NormalizedPitch
    criteria_config: dict[str, Any]   # Serialized EvaluationCriteriaConfig
    system_prompt: str
    user_prompt: str