from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pitch_evaluator.config import EvaluationCriteriaConfig
from pitch_evaluator.evidence.engine import (
    EvidenceExtractionEngine,
    EvidenceExtractionResult,
    create_evidence_engine,
)
from pitch_evaluator.models import (
    EvidenceCitation,
    EvidenceType,
    NormalizedPitch,
    SegmentRef,
    VerificationLevel,
)


@dataclass
class EvidenceExtractionOutput:
    """Complete evidence extraction output with validated citations."""

    citations: list[EvidenceCitation]
    raw_engine_result: EvidenceExtractionResult
    extraction_metadata: dict[str, Any]


class EvidenceExtractor:
    """High-level evidence extractor that orchestrates the extraction process."""

    def __init__(
        self,
        engine: EvidenceExtractionEngine | str = "mock",
        **engine_kwargs: Any,
    ) -> None:
        """Initialize evidence extractor.

        Args:
            engine: EvidenceExtractionEngine instance or engine type string ("mock", "llm")
            **engine_kwargs: Additional engine configuration
        """
        if isinstance(engine, str):
            self._engine = create_evidence_engine(engine, **engine_kwargs)
        else:
            self._engine = engine

    def extract(
        self,
        normalized_pitch: NormalizedPitch,
        criteria_config: EvaluationCriteriaConfig,
    ) -> EvidenceExtractionOutput:
        """Extract evidence citations from normalized pitch.

        Args:
            normalized_pitch: Normalized pitch with segments and metadata
            criteria_config: Evaluation criteria configuration

        Returns:
            EvidenceExtractionOutput with validated EvidenceCitation objects

        Raises:
            ValueError: If evidence validation fails
        """
        # Build segment lookup for validation
        segment_map = {seg.segment_id: seg for seg in normalized_pitch.segments}

        # Get raw extraction result from engine
        engine_result = self._engine.extract_evidence(normalized_pitch, criteria_config)

        # Validate and convert citations
        validated_citations = []
        for citation_data in engine_result.citations:
            validated = self._validate_and_convert_citation(
                citation_data, segment_map, criteria_config
            )
            if validated:
                validated_citations.append(validated)

        return EvidenceExtractionOutput(
            citations=validated_citations,
            raw_engine_result=engine_result,
            extraction_metadata={
                "engine_type": type(self._engine).__name__,
                "total_citations": len(validated_citations),
                "criteria_covered": list({c.criterion for c in validated_citations}),
                "segments_referenced": list({
                    ref.segment_id
                    for c in validated_citations
                    for ref in c.source_segments
                }),
            },
        )

    def _validate_and_convert_citation(
        self,
        citation_data: dict[str, Any],
        segment_map: dict[str, Any],
        criteria_config: EvaluationCriteriaConfig,
    ) -> EvidenceCitation | None:
        """Validate and convert raw citation data to EvidenceCitation model."""
        # Fallback to source_segments if source_segment_ids not explicitly provided
        if "source_segment_ids" not in citation_data and "source_segments" in citation_data:
            citation_data["source_segment_ids"] = [
                s.get("segment_id") if isinstance(s, dict) else getattr(s, "segment_id", str(s))
                for s in citation_data["source_segments"]
                if (isinstance(s, dict) and "segment_id" in s) or hasattr(s, "segment_id")
            ]

        # Validate required fields
        required_fields = ["claim", "criterion", "source_segment_ids"]
        for field in required_fields:
            if field not in citation_data:
                return None

        criterion_name = citation_data["criterion"]
        source_segment_ids = citation_data.get("source_segment_ids", [])

        # Validate criterion exists and is enabled
        try:
            next(
                c for c in criteria_config.criteria
                if c.name == criterion_name and c.enabled
            )
        except StopIteration:
            return None

        # Validate and convert segment references
        source_segments = []
        for seg_id in source_segment_ids:
            if seg_id not in segment_map:
                continue
            seg = segment_map[seg_id]
            source_segments.append(SegmentRef(
                segment_id=seg.segment_id,
                source_modality=seg.source.value,
                start_ref=seg.start_ref,
                end_ref=seg.end_ref,
                excerpt=seg.content[:200],
            ))

        if not source_segments:
            return None

        # Parse evidence type
        try:
            evidence_type = EvidenceType(citation_data.get("evidence_type", "direct_quote"))
        except ValueError:
            evidence_type = EvidenceType.DIRECT_QUOTE

        # Parse verification level - default to self_reported
        try:
            verification_level = VerificationLevel(
                citation_data.get("verification_level", "self_reported")
            )
        except ValueError:
            verification_level = VerificationLevel.UNKNOWN

        # Validate confidence
        confidence = citation_data.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            confidence = 0.5

        # Build EvidenceCitation
        return EvidenceCitation(
            claim=citation_data["claim"],
            criterion=criterion_name,
            source_segments=source_segments,
            evidence_type=evidence_type,
            verification_level=verification_level,
            confidence=confidence,
            notes=citation_data.get("notes"),
        )