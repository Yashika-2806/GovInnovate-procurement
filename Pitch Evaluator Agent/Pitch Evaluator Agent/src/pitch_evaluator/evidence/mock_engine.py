from __future__ import annotations

from typing import Any

from pitch_evaluator.config import EvaluationCriteriaConfig
from pitch_evaluator.evidence.engine import (
    EvidenceExtractionEngine,
    EvidenceExtractionResult,
)
from pitch_evaluator.models import NormalizedPitch, PitchSegment, SourceModality


class MockEvidenceEngine(EvidenceExtractionEngine):
    """Deterministic mock evidence extraction engine for testing.

    This engine produces consistent, predictable evidence citations
    without requiring an LLM or network calls. It extracts evidence
    based on simple keyword matching against pitch segments.
    """

    def __init__(
        self,
        evidence_map: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        """Initialize mock engine with optional custom evidence map.

        Args:
            evidence_map: Optional custom mapping of criterion names to
                evidence citation dictionaries. If not provided, uses
                built-in default evidence based on keyword matching.
        """
        self._evidence_map = evidence_map or {}

    @property
    def supported_criteria(self) -> list[str]:
        """Return all criteria this mock engine can handle."""
        # Return all possible criteria names - mock engine handles everything
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

    def extract_evidence(
        self,
        normalized_pitch: NormalizedPitch,
        criteria_config: EvaluationCriteriaConfig,
    ) -> EvidenceExtractionResult:
        """Extract evidence using deterministic keyword matching.

        This mock implementation:
        1. Uses custom evidence map if provided
        2. Otherwise performs simple keyword-based extraction
        3. Only extracts evidence for enabled criteria
        4. Returns deterministic results
        """
        enabled_criteria = criteria_config.get_enabled_criteria()
        all_citations = []

        # Use custom evidence map if provided
        if self._evidence_map:
            for criterion in enabled_criteria:
                criterion_name = criterion.name
                if criterion_name in self._evidence_map:
                    for citation_data in self._evidence_map[criterion_name]:
                        # Validate segment references exist
                        validated_segments = self._validate_segment_refs(
                            citation_data.get("source_segments", []),
                            normalized_pitch,
                        )
                        if validated_segments:
                            citation = citation_data.copy()
                            citation["criterion"] = criterion_name
                            citation["source_segments"] = validated_segments
                            if "source_segment_ids" not in citation:
                                citation["source_segment_ids"] = [
                                    seg["segment_id"] for seg in validated_segments if "segment_id" in seg
                                ]
                            all_citations.append(citation)
            return EvidenceExtractionResult(
                citations=all_citations,
                raw_response="mock_engine_custom_map",
            )

        # Default: simple keyword-based extraction
        for criterion in enabled_criteria:
            criterion_name = criterion.name
            evidence_guidance = criterion.evidence_guidance.lower()

            # Build keywords from evidence guidance and criterion name
            keywords = self._extract_keywords(criterion_name, evidence_guidance)

            # Find matching segments
            matching_segments = self._find_matching_segments(
                normalized_pitch, keywords
            )

            if matching_segments:
                # Create citation for each matching segment
                for seg in matching_segments:
                    citation = self._create_citation(
                        criterion_name=criterion_name,
                        segment=seg,
                        keywords=keywords,
                    )
                    all_citations.append(citation)

        return EvidenceExtractionResult(
            citations=all_citations,
            raw_response="mock_engine_keyword_based",
        )

    def _extract_keywords(self, criterion_name: str, evidence_guidance: str) -> list[str]:
        """Extract keywords from criterion name and evidence guidance."""
        keywords = set()

        # Add criterion name words
        for word in criterion_name.lower().split():
            if len(word) > 3:
                keywords.add(word)

        # Add evidence guidance words
        for word in evidence_guidance.split():
            word = word.strip(",.()[]{}").lower()
            if len(word) > 3:
                keywords.add(word)

        return list(keywords)

    def _find_matching_segments(
        self, normalized_pitch: NormalizedPitch, keywords: list[str]
    ) -> list[PitchSegment]:
        """Find pitch segments containing any keywords."""
        matching: list[PitchSegment] = []
        for segment in normalized_pitch.segments:
            content_lower = segment.content.lower()
            for keyword in keywords:
                if keyword in content_lower:
                    matching.append(segment)
                    break
        return matching

    def _create_citation(
        self, criterion_name: str, segment: PitchSegment, keywords: list[str]
    ) -> dict[str, Any]:
        """Create evidence citation from matching segment."""
        # Find which keywords matched
        matched_keywords = [k for k in keywords if k in segment.content.lower()]

        # Determine evidence type based on source modality
        evidence_type = self._determine_evidence_type(segment.source)

        # Default to self_reported for startup claims
        verification_level = "self_reported"

        # Confidence based on keyword match strength
        confidence = min(0.9, 0.5 + len(matched_keywords) * 0.1)

        # Create excerpt (first 200 chars)
        excerpt = segment.content[:200]

        return {
            "claim": f"Startup addresses {criterion_name.lower()} with relevant content",
            "criterion": criterion_name,
            "source_segment_ids": [segment.segment_id],
            "source_segments": [
                {
                    "segment_id": segment.segment_id,
                    "source_modality": segment.source.value,
                    "start_ref": segment.start_ref,
                    "end_ref": segment.end_ref,
                    "excerpt": excerpt,
                }
            ],
            "evidence_type": evidence_type,
            "verification_level": verification_level,
            "confidence": confidence,
            "notes": f"Mock extraction based on keyword match: {', '.join(matched_keywords)}",
        }

    def _determine_evidence_type(self, source_modality: SourceModality) -> str:
        """Determine evidence type from source modality."""
        modality_map = {
            "text": "direct_quote",
            "audio": "direct_quote",
            "video": "visual_observation",
            "document": "document_excerpt",
        }
        return modality_map.get(source_modality.value, "direct_quote")

    def _validate_segment_refs(
        self, segment_refs: list[dict[str, Any]], normalized_pitch: NormalizedPitch
    ) -> list[dict[str, Any]]:
        """Validate that segment references exist in the pitch."""
        segment_ids = {s.segment_id for s in normalized_pitch.segments}
        validated = []
        for ref in segment_refs:
            if ref.get("segment_id") in segment_ids:
                validated.append(ref)
        return validated