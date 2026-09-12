from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pitch_evaluator.config import EvaluationCriteriaConfig
from pitch_evaluator.models import EvidenceCitation, NormalizedPitch


@dataclass
class CriterionAnalysisResult:
    """Result from a criterion analysis engine for a single criterion."""

    criterion_name: str
    proposed_score: int
    reasoning: str
    evidence_citation_ids: list[str]
    strengths: list[str]
    weaknesses: list[str]
    missing_information: list[str]
    uncertainties: list[str]
    confidence: float
    raw_response: str


class CriterionAnalysisEngine(ABC):
    """Abstract interface for criterion analysis engines."""

    @abstractmethod
    def analyze_criterion(
        self,
        normalized_pitch: NormalizedPitch,
        criteria_config: EvaluationCriteriaConfig,
        criterion_name: str,
        evidence_citations: list[EvidenceCitation],
    ) -> CriterionAnalysisResult:
        """Analyze a single criterion using the provided evidence.

        Args:
            normalized_pitch: The normalized pitch content
            criteria_config: Evaluation criteria configuration
            criterion_name: Name of the criterion to analyze
            evidence_citations: Evidence citations relevant to this criterion

        Returns:
            CriterionAnalysisResult with score, reasoning, and metadata
        """
        ...

    @property
    @abstractmethod
    def supported_criteria(self) -> list[str]:
        """Return list of criteria this engine can analyze."""
        ...


def create_criterion_analysis_engine(engine_type: str = "mock", **kwargs: Any) -> CriterionAnalysisEngine:
    """Factory function to create criterion analysis engine.

    Args:
        engine_type: "mock" for testing, "llm" for production LLM
        **kwargs: Engine-specific configuration

    Returns:
        CriterionAnalysisEngine instance
    """
    if engine_type == "mock":
        from pitch_evaluator.analysis.mock_engine import MockCriterionAnalysisEngine

        return MockCriterionAnalysisEngine(**kwargs)
    elif engine_type == "llm":
        from pitch_evaluator.analysis.llm_engine import LLMCriterionAnalysisEngine

        return LLMCriterionAnalysisEngine(**kwargs)
    else:
        raise ValueError(f"Unknown criterion analysis engine type: {engine_type}")