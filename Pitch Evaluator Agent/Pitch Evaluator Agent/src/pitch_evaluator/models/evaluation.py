from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator

from pitch_evaluator.models.evidence import EvidenceCitation


class RiskSignals(BaseModel):
    """Structured risk-relevant signals for downstream Risk Detector consumption.

    These are deterministic pattern tags extracted from the evaluation,
    NOT an AI risk assessment.
    """

    technical_risk_indicators: Annotated[list[str], Field(default_factory=list)]
    regulatory_risk_indicators: Annotated[list[str], Field(default_factory=list)]
    team_risk_indicators: Annotated[list[str], Field(default_factory=list)]
    market_risk_indicators: Annotated[list[str], Field(default_factory=list)]
    financial_risk_indicators: Annotated[list[str], Field(default_factory=list)]


class EvaluationMetadata(BaseModel):
    """Metadata about the evaluation process."""

    criteria_config_version: str
    evaluator_version: str
    processed_at: datetime
    source_modality: str
    processing_time_ms: Annotated[int, Field(ge=0)]
    llm_model: str | None = None
    criteria_used: Annotated[list[str], Field(default_factory=list)]


class CriterionAnalysis(BaseModel):
    """LLM-proposed analysis for a single criterion."""

    criterion_name: Annotated[str, Field(min_length=1)]
    proposed_score: Annotated[int, Field(ge=0, le=100)]
    reasoning: str
    evidence_citations: Annotated[list[str], Field(default_factory=list)]
    strengths: Annotated[list[str], Field(default_factory=list)]
    weaknesses: Annotated[list[str], Field(default_factory=list)]
    missing_information: Annotated[list[str], Field(default_factory=list)]
    uncertainties: Annotated[list[str], Field(default_factory=list)]
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]


class PitchEvaluation(BaseModel):
    """Complete pitch evaluation output.

    IMPORTANT SEMANTIC DISTINCTIONS:
    - score (criterion_scores, weighted_total): Criterion-relative performance, NOT probability of success
    - confidence: Evaluator's certainty in the analysis
    - evidence_quality: Richness/reliability of supplied evidence
    - These are SEPARATE dimensions, not interchangeable
    """

    pitch_evaluation_id: Annotated[str, Field(min_length=1)]
    pitch_id: Annotated[str, Field(min_length=1)]
    startup_id: Annotated[str, Field(min_length=1)]
    problem_statement_id: Annotated[str, Field(min_length=1)]
    criterion_scores: Annotated[dict[str, int], Field(min_length=1)]
    weighted_total: Annotated[int, Field(ge=0, le=100)]
    evidence_citations: Annotated[list[EvidenceCitation], Field(default_factory=list)] = Field(default_factory=list)
    strengths: Annotated[list[str], Field(default_factory=list)]
    weaknesses: Annotated[list[str], Field(default_factory=list)]
    missing_information: Annotated[list[str], Field(default_factory=list)]
    uncertainties: Annotated[list[str], Field(default_factory=list)]
    risk_signals: RiskSignals
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    evidence_quality: Annotated[float, Field(ge=0.0, le=1.0)]
    metadata: EvaluationMetadata
    calculation_audit: Annotated[list[dict[str, Any]], Field(default_factory=list)] = Field(default_factory=list)

    @field_validator("weighted_total", mode="after")
    @classmethod
    def _validate_weighted_total_bounds(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("weighted_total must be between 0 and 100")
        return v

    @field_validator("criterion_scores", mode="after")
    @classmethod
    def _validate_criterion_scores_bounds(cls, v: dict[str, int]) -> dict[str, int]:
        for name, score in v.items():
            if not 0 <= score <= 100:
                raise ValueError(f"Criterion '{name}' score must be between 0 and 100, got {score}")
        return v