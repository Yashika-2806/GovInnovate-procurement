from __future__ import annotations

from pitch_evaluator.analysis.engine import (
    CriterionAnalysisEngine,
    CriterionAnalysisResult,
)
from pitch_evaluator.config import EvaluationCriteriaConfig
from pitch_evaluator.models import EvidenceCitation, NormalizedPitch


class MockCriterionAnalysisEngine(CriterionAnalysisEngine):
    """Deterministic mock criterion analysis engine for testing.

    Produces consistent, predictable scores based on evidence presence
    without requiring an LLM.
    """

    def __init__(
        self,
        score_map: dict[str, int] | None = None,
        confidence_map: dict[str, float] | None = None,
    ) -> None:
        """Initialize mock engine with optional custom scores.

        Args:
            score_map: Optional mapping of criterion name -> score
            confidence_map: Optional mapping of criterion name -> confidence
        """
        self._score_map = score_map or {}
        self._confidence_map = confidence_map or {}

    @property
    def supported_criteria(self) -> list[str]:
        """Return all criteria this mock engine can handle."""
        return [
            "Problem Validation",
            "Scalability",
            "Feasibility",
            "Cost",
            "Practicality",
            "Solution Fit",
            "Innovation",
            "Technical Feasibility",
            "Market Validation",
            "Team Capability",
            "Implementation Readiness",
            "Government Fit",
            "Business/Sustainability",
            "Competitive Differentiation",
        ]

    def analyze_criterion(
        self,
        normalized_pitch: NormalizedPitch,
        criteria_config: EvaluationCriteriaConfig,
        criterion_name: str,
        evidence_citations: list[EvidenceCitation],
    ) -> CriterionAnalysisResult:
        """Analyze a single criterion using deterministic scoring.

        This mock implementation:
        1. Uses custom score map if provided
        2. Otherwise uses simple deterministic scoring based on evidence count
        3. Returns consistent, predictable results
        """
        # Get score from custom map or compute from evidence
        if criterion_name in self._score_map:
            score = self._score_map[criterion_name]
        else:
            score = self._compute_score(criterion_name, evidence_citations)

        # Get confidence from custom map or compute
        if criterion_name in self._confidence_map:
            confidence = self._confidence_map[criterion_name]
        else:
            confidence = self._compute_confidence(criterion_name, evidence_citations)

        # Generate deterministic reasoning
        reasoning = self._generate_reasoning(criterion_name, evidence_citations, score)

        # Extract evidence citation IDs
        evidence_ids: list[str] = []
        for citation in evidence_citations:
            if hasattr(citation, "source_segments"):
                for seg in citation.source_segments:
                    evidence_ids.append(seg.segment_id)

        # Generate strengths/weaknesses based on score
        strengths, weaknesses, missing_info, uncertainties = self._generate_analysis(
            criterion_name, evidence_citations, score
        )

        return CriterionAnalysisResult(
            criterion_name=criterion_name,
            proposed_score=score,
            reasoning=reasoning,
            evidence_citation_ids=evidence_ids,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_information=missing_info,
            uncertainties=uncertainties,
            confidence=confidence,
            raw_response=f"mock_analysis_{criterion_name.lower().replace(' ', '_')}",
        )

    def _compute_score(self, criterion_name: str, evidence_citations: list[EvidenceCitation]) -> int:
        """Compute score based on evidence presence and quality."""
        base_score = 40  # Base score for no evidence
        evidence_bonus = min(len(evidence_citations) * 10, 40)
        return min(base_score + evidence_bonus, 100)

    def _compute_confidence(
        self, criterion_name: str, evidence_citations: list[EvidenceCitation]
    ) -> float:
        """Compute confidence based on evidence quantity and quality."""
        if not evidence_citations:
            return 0.3
        # More evidence = higher confidence
        return min(0.3 + len(evidence_citations) * 0.1, 0.9)

    def _generate_reasoning(
        self, criterion_name: str, evidence_citations: list[EvidenceCitation], score: int
    ) -> str:
        """Generate deterministic reasoning text."""
        evidence_count = len(evidence_citations)
        if evidence_count == 0:
            return f"No specific evidence found for {criterion_name}. Score reflects absence of supporting evidence."
        elif score >= 80:
            return f"Strong evidence found for {criterion_name} ({evidence_count} citations). Score reflects robust support."
        elif score >= 60:
            return f"Moderate evidence found for {criterion_name} ({evidence_count} citations). Score reflects adequate but not comprehensive support."
        else:
            return f"Limited evidence found for {criterion_name} ({evidence_count} citations). Score reflects weak support."

    def _generate_analysis(
        self, criterion_name: str, evidence_citations: list[EvidenceCitation], score: int
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        """Generate strengths, weaknesses, missing_info, uncertainties."""
        _ = len(evidence_citations)  # unused, but available for logic

        if score >= 80:
            strengths = [f"Strong evidence base for {criterion_name}"]
            weaknesses = []
            missing_info = []
            uncertainties = []
        elif score >= 60:
            strengths = [f"Adequate evidence for {criterion_name}"]
            weaknesses = ["Could benefit from more comprehensive evidence"]
            missing_info = ["Additional supporting documentation would strengthen the case"]
            uncertainties = ["Limited scope of available evidence"]
        else:
            strengths = []
            weaknesses = [f"Insufficient evidence for {criterion_name}"]
            missing_info = [f"Need more documentation and data points for {criterion_name}"]
            uncertainties = ["High uncertainty due to limited evidence"]

        return strengths, weaknesses, missing_info, uncertainties