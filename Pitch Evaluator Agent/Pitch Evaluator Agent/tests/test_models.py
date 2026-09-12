"""Tests for Pitch Evaluator data models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pitch_evaluator.models import (
    BoundingBox,
    CriterionAnalysis,
    DocumentContent,
    DocumentSource,
    EvaluationMetadata,
    EvidenceCitation,
    EvidenceType,
    NormalizedPitch,
    ObservationType,
    PitchEvaluation,
    PitchSegment,
    RiskSignals,
    SegmentRef,
    SourceMetadata,
    SourceModality,
    Transcript,
    TranscriptSegment,
    VerificationLevel,
    VisualObservation,
)


class TestPitchModels:
    """Tests for pitch-related models."""

    def test_source_modality_enum(self) -> None:
        assert SourceModality.TEXT == "text"
        assert SourceModality.AUDIO == "audio"
        assert SourceModality.VIDEO == "video"
        assert SourceModality.DOCUMENT == "document"

    def test_observation_type_enum(self) -> None:
        assert ObservationType.PROTOTYPE_DEMO == "prototype_demo"
        assert ObservationType.UI_SCREEN == "ui_screen"
        assert ObservationType.PHYSICAL_HARDWARE == "physical_hardware"
        assert ObservationType.SLIDE_CONTENT == "slide_content"
        assert ObservationType.DEPLOYMENT_EVIDENCE == "deployment_evidence"
        assert ObservationType.OTHER == "other"

    def test_document_source_enum(self) -> None:
        assert DocumentSource.PDF == "pdf"
        assert DocumentSource.PPT == "ppt"
        assert DocumentSource.PPTX == "pptx"

    def test_source_metadata_valid(self) -> None:
        meta = SourceMetadata(
            filename="pitch.pdf",
            mime_type="application/pdf",
            file_size_bytes=1024,
            checksum="abc123",
            uploaded_at=datetime.now(UTC),
            uploaded_by="user123",
            duration_seconds=30.5,
            page_count=10,
        )
        assert meta.filename == "pitch.pdf"
        assert meta.duration_seconds == 30.5
        assert meta.page_count == 10

    def test_source_metadata_optional_fields_none(self) -> None:
        meta = SourceMetadata(
            filename="pitch.txt",
            mime_type="text/plain",
            file_size_bytes=512,
            checksum="def456",
            uploaded_at=datetime.now(UTC),
            uploaded_by="user123",
        )
        assert meta.duration_seconds is None
        assert meta.page_count is None

    def test_source_metadata_negative_size_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SourceMetadata(
                filename="pitch.pdf",
                mime_type="application/pdf",
                file_size_bytes=-1,
                checksum="abc123",
                uploaded_at=datetime.now(UTC),
                uploaded_by="user123",
            )

    def test_transcript_segment_valid(self) -> None:
        seg = TranscriptSegment(
            start_ms=0,
            end_ms=5000,
            speaker_id="speaker_1",
            text="Hello world",
            confidence=0.95,
        )
        assert seg.start_ms == 0
        assert seg.end_ms == 5000
        assert seg.confidence == 0.95

    def test_transcript_segment_negative_timestamp_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TranscriptSegment(
                start_ms=-100,
                end_ms=5000,
                speaker_id="speaker_1",
                text="test",
                confidence=0.9,
            )

    def test_transcript_segment_end_before_start_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TranscriptSegment(
                start_ms=5000,
                end_ms=1000,
                speaker_id="speaker_1",
                text="test",
                confidence=0.9,
            )

    def test_transcript_segment_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            TranscriptSegment(
                start_ms=0,
                end_ms=1000,
                speaker_id="speaker_1",
                text="test",
                confidence=1.5,
            )
        with pytest.raises(ValidationError):
            TranscriptSegment(
                start_ms=0,
                end_ms=1000,
                speaker_id="speaker_1",
                text="test",
                confidence=-0.1,
            )

    def test_transcript_valid(self) -> None:
        transcript = Transcript(
            full_text="Hello world. This is a test.",
            segments=[
                TranscriptSegment(
                    start_ms=0,
                    end_ms=2000,
                    speaker_id="speaker_1",
                    text="Hello world.",
                    confidence=0.95,
                ),
                TranscriptSegment(
                    start_ms=2000,
                    end_ms=5000,
                    speaker_id="speaker_1",
                    text="This is a test.",
                    confidence=0.9,
                ),
            ],
            language="en",
            confidence=0.92,
        )
        assert len(transcript.segments) == 2
        assert transcript.language == "en"

    def test_visual_observation_valid(self) -> None:
        obs = VisualObservation(
            timestamp_ms=15000,
            frame_index=450,
            observation_type=ObservationType.PROTOTYPE_DEMO,
            description="Founder demonstrating mobile app prototype",
            confidence=0.85,
            extracted_text="App v1.0",
            bounding_boxes=[BoundingBox(x=100, y=100, width=200, height=300)],
            trigger_keyword="prototype",
        )
        assert obs.observation_type == ObservationType.PROTOTYPE_DEMO
        assert obs.confidence == 0.85
        assert len(obs.bounding_boxes) == 1

    def test_visual_observation_invalid_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VisualObservation(
                timestamp_ms=1000,
                frame_index=30,
                observation_type="invalid_type",  # type: ignore
                description="test",
                confidence=0.5,
                trigger_keyword="test",
            )

    def test_visual_observation_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            VisualObservation(
                timestamp_ms=1000,
                frame_index=30,
                observation_type=ObservationType.OTHER,
                description="test",
                confidence=1.5,
                trigger_keyword="test",
            )

    def test_document_content_valid(self) -> None:
        doc = DocumentContent(
            source=DocumentSource.PDF,
            page_number=1,
            slide_number=None,
            text_content="Page 1 content",
            images=[],
            tables=[],
        )
        assert doc.source == DocumentSource.PDF
        assert doc.page_number == 1

    def test_pitch_segment_valid(self) -> None:
        seg = PitchSegment(
            segment_id="seg_1",
            source=SourceModality.TEXT,
            start_ref=0,
            end_ref=100,
            content="First segment content",
            speaker_id="speaker_1",
        )
        assert seg.segment_id == "seg_1"
        assert seg.source == SourceModality.TEXT

    def test_normalized_pitch_valid_text(self) -> None:
        pitch = NormalizedPitch(
            source_modality=SourceModality.TEXT,
            source_metadata=SourceMetadata(
                filename="pitch.txt",
                mime_type="text/plain",
                file_size_bytes=100,
                checksum="abc",
                uploaded_at=datetime.now(UTC),
                uploaded_by="user",
            ),
            transcript=Transcript(
                full_text="Test pitch",
                segments=[
                    TranscriptSegment(
                        start_ms=0,
                        end_ms=5000,
                        speaker_id="speaker_1",
                        text="Test pitch",
                        confidence=0.9,
                    )
                ],
                language="en",
                confidence=0.9,
            ),
            visual_observations=[],
            document_content=[],
            segments=[
                PitchSegment(
                    segment_id="seg_1",
                    source=SourceModality.TEXT,
                    start_ref=0,
                    end_ref=5000,
                    content="Test pitch",
                    speaker_id="speaker_1",
                )
            ],
        )
        assert pitch.source_modality == SourceModality.TEXT
        assert len(pitch.segments) == 1

    def test_normalized_pitch_empty_segments_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NormalizedPitch(
                source_modality=SourceModality.TEXT,
                source_metadata=SourceMetadata(
                    filename="pitch.txt",
                    mime_type="text/plain",
                    file_size_bytes=100,
                    checksum="abc",
                    uploaded_at=datetime.now(UTC),
                    uploaded_by="user",
                ),
                transcript=None,
                visual_observations=[],
                document_content=[],
                segments=[],
            )


class TestEvidenceModels:
    """Tests for evidence-related models."""

    def test_evidence_type_enum(self) -> None:
        assert EvidenceType.DIRECT_QUOTE == "direct_quote"
        assert EvidenceType.PARAPHRASE == "paraphrase"
        assert EvidenceType.VISUAL_OBSERVATION == "visual_observation"
        assert EvidenceType.DOCUMENT_EXCERPT == "document_excerpt"
        assert EvidenceType.DATA_POINT == "data_point"

    def test_verification_level_enum(self) -> None:
        assert VerificationLevel.SELF_REPORTED == "self_reported"
        assert VerificationLevel.SYSTEM_GENERATED == "system_generated"
        assert VerificationLevel.THIRD_PARTY == "third_party"
        assert VerificationLevel.INDEPENDENTLY_VERIFIED == "independently_verified"
        assert VerificationLevel.UNKNOWN == "unknown"

    def test_segment_ref_valid(self) -> None:
        ref = SegmentRef(
            segment_id="seg_1",
            source_modality="text",
            start_ref=0,
            end_ref=100,
            excerpt="Excerpt text",
        )
        assert ref.segment_id == "seg_1"
        assert ref.excerpt == "Excerpt text"

    def test_evidence_citation_valid(self) -> None:
        citation = EvidenceCitation(
            claim="Startup has 50 hospital deployments",
            criterion="Market Validation",
            source_segments=[
                SegmentRef(
                    segment_id="seg_5",
                    source_modality="text",
                    start_ref=12000,
                    end_ref=15000,
                    excerpt="We have deployed in 50 hospitals",
                )
            ],
            evidence_type=EvidenceType.DIRECT_QUOTE,
            verification_level=VerificationLevel.SELF_REPORTED,
            confidence=0.8,
            notes="No independent verification in pitch",
        )
        assert citation.claim == "Startup has 50 hospital deployments"
        assert citation.verification_level == VerificationLevel.SELF_REPORTED
        assert citation.confidence == 0.8

    def test_evidence_citation_invalid_verification_level_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EvidenceCitation(
                claim="test",
                criterion="test",
                source_segments=[
                    SegmentRef(
                        segment_id="seg_1",
                        source_modality="text",
                        start_ref=0,
                        end_ref=100,
                        excerpt="test",
                    )
                ],
                evidence_type=EvidenceType.DIRECT_QUOTE,
                verification_level="invalid_level",  # type: ignore
                confidence=0.5,
            )

    def test_evidence_citation_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            EvidenceCitation(
                claim="test",
                criterion="test",
                source_segments=[
                    SegmentRef(
                        segment_id="seg_1",
                        source_modality="text",
                        start_ref=0,
                        end_ref=100,
                        excerpt="test",
                    )
                ],
                evidence_type=EvidenceType.DIRECT_QUOTE,
                verification_level=VerificationLevel.SELF_REPORTED,
                confidence=1.5,
            )


class TestEvaluationModels:
    """Tests for evaluation-related models."""

    def test_risk_signals_valid(self) -> None:
        signals = RiskSignals(
            technical_risk_indicators=["prototype_only", "no_scale_testing"],
            regulatory_risk_indicators=["health_data_no_compliance_evidence"],
            team_risk_indicators=["no_gov_experience"],
            market_risk_indicators=["single_pilot"],
            financial_risk_indicators=["pre_revenue"],
        )
        assert len(signals.technical_risk_indicators) == 2
        assert "prototype_only" in signals.technical_risk_indicators

    def test_risk_signals_empty_defaults(self) -> None:
        signals = RiskSignals()
        assert signals.technical_risk_indicators == []
        assert signals.regulatory_risk_indicators == []

    def test_evaluation_metadata_valid(self) -> None:
        meta = EvaluationMetadata(
            criteria_config_version="1.0",
            evaluator_version="0.1.0",
            processed_at=datetime.now(UTC),
            source_modality="video",
            processing_time_ms=45000,
            llm_model="llama-3.1-70b",
            criteria_used=["Problem Validation", "Scalability"],
        )
        assert meta.criteria_config_version == "1.0"
        assert meta.processing_time_ms == 45000

    def test_criterion_analysis_valid(self) -> None:
        analysis = CriterionAnalysis(
            criterion_name="Problem Validation",
            proposed_score=85,
            reasoning="Strong problem validation with user research data",
            evidence_citations=["cite_1", "cite_2"],
            strengths=["Quantified problem size", "User interviews"],
            weaknesses=["Limited geographic scope"],
            missing_information=["Competitor problem validation"],
            uncertainties=["Long-term problem persistence"],
            confidence=0.85,
        )
        assert analysis.criterion_name == "Problem Validation"
        assert analysis.proposed_score == 85
        assert analysis.confidence == 0.85

    def test_criterion_analysis_proposed_score_bounds(self) -> None:
        with pytest.raises(ValidationError):
            CriterionAnalysis(
                criterion_name="Test",
                proposed_score=101,
                reasoning="test",
                confidence=0.5,
            )
        with pytest.raises(ValidationError):
            CriterionAnalysis(
                criterion_name="Test",
                proposed_score=-1,
                reasoning="test",
                confidence=0.5,
            )

    def test_criterion_analysis_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            CriterionAnalysis(
                criterion_name="Test",
                proposed_score=50,
                reasoning="test",
                confidence=1.5,
            )

    def test_pitch_evaluation_valid(self) -> None:
        eval = PitchEvaluation(
            pitch_evaluation_id="eval_123",
            pitch_id="pitch_456",
            startup_id="startup_789",
            problem_statement_id="prob_001",
            criterion_scores={
                "Problem Validation": 85,
                "Scalability": 70,
                "Feasibility": 75,
                "Cost": 80,
                "Practicality": 65,
            },
            weighted_total=76,
            evidence_citations=[
                EvidenceCitation(
                    claim="Test problem claim",
                    criterion="Problem Validation",
                    source_segments=[
                        SegmentRef(
                            segment_id="seg_1",
                            source_modality="text",
                            start_ref=0,
                            end_ref=50,
                            excerpt="Test excerpt",
                        )
                    ],
                    evidence_type=EvidenceType.DIRECT_QUOTE,
                    verification_level=VerificationLevel.SELF_REPORTED,
                    confidence=0.85,
                    notes="Test notes",
                )
            ],
            strengths=["Strong team", "Clear problem"],
            weaknesses=["Limited traction"],
            missing_information=["Financial projections"],
            uncertainties=["Regulatory timeline"],
            risk_signals=RiskSignals(
                technical_risk_indicators=[],
                regulatory_risk_indicators=["health_data_no_compliance_evidence"],
                team_risk_indicators=[],
                market_risk_indicators=[],
                financial_risk_indicators=[],
            ),
            confidence=0.78,
            evidence_quality=0.65,
            metadata=EvaluationMetadata(
                criteria_config_version="1.0",
                evaluator_version="0.1.0",
                processed_at=datetime.now(UTC),
                source_modality="video",
                processing_time_ms=30000,
            ),
        )
        assert eval.pitch_evaluation_id == "eval_123"
        assert eval.weighted_total == 76
        assert eval.confidence == 0.78
        assert eval.evidence_quality == 0.65
        assert len(eval.criterion_scores) == 5
        assert len(eval.evidence_citations) == 1
        assert isinstance(eval.evidence_citations[0], EvidenceCitation)
        assert eval.evidence_citations[0].claim == "Test problem claim"
        assert eval.evidence_citations[0].criterion == "Problem Validation"
        assert len(eval.evidence_citations[0].source_segments) == 1
        assert eval.evidence_citations[0].source_segments[0].segment_id == "seg_1"
        assert eval.evidence_citations[0].evidence_type == EvidenceType.DIRECT_QUOTE
        assert eval.evidence_citations[0].verification_level == VerificationLevel.SELF_REPORTED
        assert eval.evidence_citations[0].confidence == 0.85
        assert eval.evidence_citations[0].notes == "Test notes"

    def test_pitch_evaluation_weighted_total_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PitchEvaluation(
                pitch_evaluation_id="eval_1",
                pitch_id="pitch_1",
                startup_id="startup_1",
                problem_statement_id="prob_1",
                criterion_scores={"Test": 50},
                weighted_total=101,
                risk_signals=RiskSignals(),
                confidence=0.5,
                evidence_quality=0.5,
                metadata=EvaluationMetadata(
                    criteria_config_version="1.0",
                    evaluator_version="0.1.0",
                    processed_at=datetime.now(UTC),
                    source_modality="text",
                    processing_time_ms=1000,
                ),
            )

    def test_pitch_evaluation_criterion_score_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PitchEvaluation(
                pitch_evaluation_id="eval_1",
                pitch_id="pitch_1",
                startup_id="startup_1",
                problem_statement_id="prob_1",
                criterion_scores={"Test": 101},
                weighted_total=50,
                risk_signals=RiskSignals(),
                confidence=0.5,
                evidence_quality=0.5,
                metadata=EvaluationMetadata(
                    criteria_config_version="1.0",
                    evaluator_version="0.1.0",
                    processed_at=datetime.now(UTC),
                    source_modality="text",
                    processing_time_ms=1000,
                ),
            )

    def test_pitch_evaluation_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PitchEvaluation(
                pitch_evaluation_id="eval_1",
                pitch_id="pitch_1",
                startup_id="startup_1",
                problem_statement_id="prob_1",
                criterion_scores={"Test": 50},
                weighted_total=50,
                risk_signals=RiskSignals(),
                confidence=1.5,
                evidence_quality=0.5,
                metadata=EvaluationMetadata(
                    criteria_config_version="1.0",
                    evaluator_version="0.1.0",
                    processed_at=datetime.now(UTC),
                    source_modality="text",
                    processing_time_ms=1000,
                ),
            )

    def test_pitch_evaluation_evidence_quality_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PitchEvaluation(
                pitch_evaluation_id="eval_1",
                pitch_id="pitch_1",
                startup_id="startup_1",
                problem_statement_id="prob_1",
                criterion_scores={"Test": 50},
                weighted_total=50,
                risk_signals=RiskSignals(),
                confidence=0.5,
                evidence_quality=-0.1,
                metadata=EvaluationMetadata(
                    criteria_config_version="1.0",
                    evaluator_version="0.1.0",
                    processed_at=datetime.now(UTC),
                    source_modality="text",
                    processing_time_ms=1000,
                ),
            )

    def test_pitch_evaluation_missing_required_ids_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PitchEvaluation(
                pitch_evaluation_id="",
                pitch_id="pitch_1",
                startup_id="startup_1",
                problem_statement_id="prob_1",
                criterion_scores={"Test": 50},
                weighted_total=50,
                risk_signals=RiskSignals(),
                confidence=0.5,
                evidence_quality=0.5,
                metadata=EvaluationMetadata(
                    criteria_config_version="1.0",
                    evaluator_version="0.1.0",
                    processed_at=datetime.now(UTC),
                    source_modality="text",
                    processing_time_ms=1000,
                ),
            )

    def test_risk_signals_representable_without_risk_detector(self) -> None:
        """Verify risk_signals can be constructed without invoking Risk Detector logic."""
        signals = RiskSignals(
            technical_risk_indicators=["prototype_only"],
            regulatory_risk_indicators=[],
            team_risk_indicators=[],
            market_risk_indicators=[],
            financial_risk_indicators=[],
        )
        # This is just data - no AI logic involved
        assert isinstance(signals.technical_risk_indicators, list)
        assert "prototype_only" in signals.technical_risk_indicators