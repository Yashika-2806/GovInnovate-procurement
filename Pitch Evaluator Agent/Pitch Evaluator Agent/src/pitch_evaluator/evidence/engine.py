from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pitch_evaluator.config import EvaluationCriteriaConfig
from pitch_evaluator.models import NormalizedPitch


@dataclass
class EvidenceExtractionResult:
    """Result from an evidence extraction engine."""

    citations: list[dict[str, Any]]  # Raw evidence citation data for validation
    raw_response: str  # Full LLM response for debugging


class EvidenceExtractionEngine(ABC):
    """Abstract interface for evidence extraction engines."""

    @abstractmethod
    def extract_evidence(
        self,
        normalized_pitch: NormalizedPitch,
        criteria_config: EvaluationCriteriaConfig,
    ) -> EvidenceExtractionResult:
        """Extract evidence citations from normalized pitch content.

        Args:
            normalized_pitch: Normalized pitch with segments and metadata
            criteria_config: Enabled evaluation criteria with descriptions and guidance

        Returns:
            EvidenceExtractionResult with structured citations
        """
        ...

    @property
    @abstractmethod
    def supported_criteria(self) -> list[str]:
        """Return list of criteria this engine can extract evidence for."""
        ...


def create_evidence_engine(engine_type: str = "mock", **kwargs: Any) -> EvidenceExtractionEngine:
    """Factory function to create evidence extraction engine.

    Args:
        engine_type: "mock" for testing, "llm" for production LLM
        **kwargs: Engine-specific configuration

    Returns:
        EvidenceExtractionEngine instance
    """
    if engine_type == "mock":
        from pitch_evaluator.evidence.mock_engine import MockEvidenceEngine

        return MockEvidenceEngine(**kwargs)
    elif engine_type == "llm":
        # Lazy import - only if actually used
        try:
            from pitch_evaluator.evidence.llm_engine import LLMEvidenceEngine

            return LLMEvidenceEngine(**kwargs)
        except ImportError as e:
            raise RuntimeError(
                "LLM evidence engine not available. Ensure dependencies are installed."
            ) from e
    else:
        raise ValueError(f"Unknown evidence engine type: {engine_type}")