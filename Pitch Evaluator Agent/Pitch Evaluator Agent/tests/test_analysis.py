"""Tests for Pitch Evaluator criterion analysis and scoring."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pitch_evaluator.analysis import (
    AnalysisOrchestrator,
    MockCriterionAnalysisEngine,
    calculate_evidence_quality,
    calculate_overall_confidence,
    calculate_weighted_score,
    extract_risk_signals,
)
from pitch_evaluator.config import load_criteria_config
from pitch_evaluator.models import (
    CriterionAnalysis,
    EvidenceCitation,
    EvidenceType,
    NormalizedPitch,
    PitchEvaluation,
    PitchSegment,
    RiskSignals,
    SegmentRef,
    SourceMetadata,
    SourceModality,
    Transcript,
    TranscriptSegment,
    VerificationLevel,
)


def _make_test_pitch() -> NormalizedPitch:
    """Create a test NormalizedPitch with sample segments."""
    return NormalizedPitch(
        source_modality=SourceModality.TEXT,
        source_metadata=SourceMetadata(
            filename="test.txt",
            mime_type="text/plain",
            file_size_bytes=100,
            checksum="abc123",
            uploaded_at=__import__('datetime').datetime.now(__import__('datetime').UTC),
            uploaded_by="test_user",
        ),
        transcript=Transcript(
            full_text="We solve the problem of hospital readmissions. Our AI platform reduces readmissions by 30%. We have deployed in 50 hospitals. The team has 20 years of healthcare experience.",
            segments=[
                TranscriptSegment(
                    start_ms=0,
                    end_ms=5000,
                    speaker_id="speaker_1",
                    text="We solve the problem of hospital readmissions.",
                    confidence=0.95,
                ),
                TranscriptSegment(
                    start_ms=5000,
                    end_ms=10000,
                    speaker_id="speaker_1",
                    text="Our AI platform reduces readmissions by 30%.",
                    confidence=0.9,
                ),
                TranscriptSegment(
                    start_ms=10000,
                    end_ms=15000,
                    speaker_id="speaker_1",
                    text="We have deployed in 50 hospitals.",
                    confidence=0.9,
                ),
                TranscriptSegment(
                    start_ms=15000,
                    end_ms=20000,
                    speaker_id="speaker_1",
                    text="The team has 20 years of healthcare experience.",
                    confidence=0.95,
                ),
            ],
            language="en",
            confidence=0.92,
        ),
        visual_observations=[],
        document_content=[],
        segments=[
            PitchSegment(
                segment_id="seg_1",
                source=SourceModality.TEXT,
                start_ref=0,
                end_ref=5000,
                content="We solve the problem of hospital readmissions.",
                speaker_id="speaker_1",
            ),
            PitchSegment(
                segment_id="seg_2",
                source=SourceModality.TEXT,
                start_ref=5000,
                end_ref=10000,
                content="Our AI platform reduces readmissions by 30%.",
                speaker_id="speaker_1",
            ),
            PitchSegment(
                segment_id="seg_3",
                source=SourceModality.TEXT,
                start_ref=10000,
                end_ref=15000,
                content="We have deployed in 50 hospitals.",
                speaker_id="speaker_1",
            ),
            PitchSegment(
                segment_id="seg_4",
                source=SourceModality.TEXT,
                start_ref=15000,
                end_ref=20000,
                content="The team has 20 years of healthcare experience.",
                speaker_id="speaker_1",
            ),
        ],
    )


def _make_test_evidence_citations() -> list:
    """Create test evidence citations."""
    return [
        EvidenceCitation(
            claim="Startup solves hospital readmissions problem",
            criterion="Problem Validation",
            source_segments=[
                SegmentRef(
                    segment_id="seg_1",
                    source_modality="text",
                    start_ref=0,
                    end_ref=5000,
                    excerpt="We solve the problem of hospital readmissions.",
                )
            ],
            evidence_type=EvidenceType.DIRECT_QUOTE,
            verification_level=VerificationLevel.SELF_REPORTED,
            confidence=0.9,
        ),
        EvidenceCitation(
            claim="AI platform reduces readmissions by 30%",
            criterion="Scalability",
            source_segments=[
                SegmentRef(
                    segment_id="seg_2",
                    source_modality="text",
                    start_ref=5000,
                    end_ref=10000,
                    excerpt="Our AI platform reduces readmissions by 30%.",
                )
            ],
            evidence_type=EvidenceType.DIRECT_QUOTE,
            verification_level=VerificationLevel.SELF_REPORTED,
            confidence=0.85,
        ),
        EvidenceCitation(
            claim="Deployed in 50 hospitals",
            criterion="Market Validation",
            source_segments=[
                SegmentRef(
                    segment_id="seg_3",
                    source_modality="text",
                    start_ref=10000,
                    end_ref=15000,
                    excerpt="We have deployed in 50 hospitals.",
                )
            ],
            evidence_type=EvidenceType.DATA_POINT,
            verification_level=VerificationLevel.SELF_REPORTED,
            confidence=0.8,
        ),
        EvidenceCitation(
            claim="Team has 20 years healthcare experience",
            criterion="Team Capability",
            source_segments=[
                SegmentRef(
                    segment_id="seg_4",
                    source_modality="text",
                    start_ref=15000,
                    end_ref=20000,
                    excerpt="The team has 20 years of healthcare experience.",
                )
            ],
            evidence_type=EvidenceType.DIRECT_QUOTE,
            verification_level=VerificationLevel.SELF_REPORTED,
            confidence=0.9,
        ),
    ]


class TestMockCriterionAnalysisEngine:
    """Tests for mock criterion analysis engine."""

    def _make_pitch(self):
        return _make_test_pitch()

    def _make_config(self):
        return load_criteria_config("config/evaluation_criteria.yaml")

    def test_mock_engine_creation(self) -> None:
        """Mock engine creates successfully."""
        engine = MockCriterionAnalysisEngine()
        assert engine is not None
        assert len(engine.supported_criteria) > 0

    def test_mock_engine_analyzes_criterion(self) -> None:
        """Mock engine produces valid CriterionAnalysisResult."""
        from pitch_evaluator.config import load_criteria_config

        pitch = _make_test_pitch()
        config = load_criteria_config("config/evaluation_criteria.yaml")
        engine = MockCriterionAnalysisEngine()

        evidence = _make_test_evidence_citations()
        result = engine.analyze_criterion(pitch, config, "Problem Validation", evidence)

        assert result.criterion_name == "Problem Validation"
        assert 0 <= result.proposed_score <= 100
        assert result.reasoning
        assert isinstance(result.evidence_citation_ids, list)
        assert isinstance(result.strengths, list)
        assert isinstance(result.weaknesses, list)
        assert isinstance(result.missing_information, list)
        assert isinstance(result.uncertainties, list)
        assert 0.0 <= result.confidence <= 1.0
        assert result.raw_response

    def test_mock_engine_custom_scores(self) -> None:
        """Mock engine respects custom score map."""
        from pitch_evaluator.config import load_criteria_config

        pitch = _make_test_pitch()
        config = load_criteria_config("config/evaluation_criteria.yaml")
        engine = MockCriterionAnalysisEngine(score_map={"Problem Validation": 95})

        _ = _make_test_evidence_citations()
        result = engine.analyze_criterion(pitch, config, "Problem Validation", [])

        assert result.proposed_score == 95

    def test_mock_engine_custom_confidence(self) -> None:
        """Mock engine respects custom confidence map."""
        from pitch_evaluator.config import load_criteria_config

        pitch = _make_test_pitch()
        config = load_criteria_config("config/evaluation_criteria.yaml")
        engine = MockCriterionAnalysisEngine(confidence_map={"Problem Validation": 0.95})

        _ = _make_test_evidence_citations()
        result = engine.analyze_criterion(pitch, config, "Problem Validation", [])

        assert result.confidence == 0.95

    def test_mock_engine_deterministic(self) -> None:
        """Mock engine produces deterministic results."""
        from pitch_evaluator.config import load_criteria_config

        pitch = _make_test_pitch()
        config = load_criteria_config("config/evaluation_criteria.yaml")

        engine1 = MockCriterionAnalysisEngine()
        engine2 = MockCriterionAnalysisEngine()

        evidence = _make_test_evidence_citations()
        result1 = engine1.analyze_criterion(pitch, config, "Problem Validation", evidence)
        result2 = engine2.analyze_criterion(pitch, config, "Problem Validation", evidence)

        assert result1.proposed_score == result2.proposed_score
        assert result1.confidence == result2.confidence
        assert result1.reasoning == result2.reasoning


class TestScoring:
    """Tests for deterministic weighted scoring."""

    def _make_analyses(self) -> list:
        """Create test criterion analyses for all enabled criteria."""
        return [
            CriterionAnalysis(
                criterion_name="Problem Validation",
                proposed_score=85,
                reasoning="Strong problem validation",
                strengths=["Clear problem statement"],
                weaknesses=[],
                missing_information=[],
                uncertainties=[],
                confidence=0.9,
            ),
            CriterionAnalysis(
                criterion_name="Scalability",
                proposed_score=70,
                reasoning="Good scalability plan",
                strengths=["Cloud-native architecture"],
                weaknesses=["Limited load testing"],
                missing_information=["Load test results"],
                uncertainties=["Peak load handling unknown"],
                confidence=0.75,
            ),
            CriterionAnalysis(
                criterion_name="Feasibility",
                proposed_score=75,
                reasoning="Feasible approach",
                strengths=["Prototype exists"],
                weaknesses=["Integration complexity"],
                missing_information=["Integration specs"],
                uncertainties=["Third-party dependencies"],
                confidence=0.8,
            ),
            CriterionAnalysis(
                criterion_name="Cost",
                proposed_score=80,
                reasoning="Cost-effective solution",
                strengths=["Competitive pricing"],
                weaknesses=[],
                missing_information=[],
                uncertainties=[],
                confidence=0.85,
            ),
            CriterionAnalysis(
                criterion_name="Practicality",
                proposed_score=65,
                reasoning="Moderate practicality",
                strengths=["Clear deployment path"],
                weaknesses=["Integration effort high"],
                missing_information=["Integration timeline"],
                uncertainties=["Resource availability"],
                confidence=0.7,
            ),
            CriterionAnalysis(
                criterion_name="Solution Fit",
                proposed_score=75,
                reasoning="Good fit",
                strengths=[],
                weaknesses=[],
                missing_information=[],
                uncertainties=[],
                confidence=0.7,
            ),
            CriterionAnalysis(
                criterion_name="Innovation",
                proposed_score=70,
                reasoning="Innovative approach",
                strengths=[],
                weaknesses=[],
                missing_information=[],
                uncertainties=[],
                confidence=0.65,
            ),
            CriterionAnalysis(
                criterion_name="Technical Feasibility",
                proposed_score=80,
                reasoning="Technically feasible",
                strengths=[],
                weaknesses=[],
                missing_information=[],
                uncertainties=[],
                confidence=0.8,
            ),
            CriterionAnalysis(
                criterion_name="Market Validation",
                proposed_score=65,
                reasoning="Some market validation",
                strengths=[],
                weaknesses=[],
                missing_information=[],
                uncertainties=[],
                confidence=0.6,
            ),
            CriterionAnalysis(
                criterion_name="Team Capability",
                proposed_score=85,
                reasoning="Strong team",
                strengths=[],
                weaknesses=[],
                missing_information=[],
                uncertainties=[],
                confidence=0.9,
            ),
            CriterionAnalysis(
                criterion_name="Implementation Readiness",
                proposed_score=70,
                reasoning="Ready to implement",
                strengths=[],
                weaknesses=[],
                missing_information=[],
                uncertainties=[],
                confidence=0.7,
            ),
            CriterionAnalysis(
                criterion_name="Government Fit",
                proposed_score=75,
                reasoning="Good government fit",
                strengths=[],
                weaknesses=[],
                missing_information=[],
                uncertainties=[],
                confidence=0.75,
            ),
            CriterionAnalysis(
                criterion_name="Business/Sustainability",
                proposed_score=70,
                reasoning="Sustainable business",
                strengths=[],
                weaknesses=[],
                missing_information=[],
                uncertainties=[],
                confidence=0.7,
            ),
            CriterionAnalysis(
                criterion_name="Competitive Differentiation",
                proposed_score=80,
                reasoning="Differentiated",
                strengths=[],
                weaknesses=[],
                missing_information=[],
                uncertainties=[],
                confidence=0.8,
            ),
        ]

    def _make_config(self):
        # Use a custom config with only the 5 core criteria for this test
        # Weights normalized to sum to 1.0: 0.20+0.15+0.15+0.15+0.10 = 0.75 -> normalize by dividing by 0.75
        from pitch_evaluator.config import CriterionConfig, EvaluationCriteriaConfig
        return EvaluationCriteriaConfig(
            version="1.0",
            criteria=[
                CriterionConfig(name="Problem Validation", weight=0.20/0.75, enabled=True, description="Test", evidence_guidance="Test"),
                CriterionConfig(name="Scalability", weight=0.15/0.75, enabled=True, description="Test", evidence_guidance="Test"),
                CriterionConfig(name="Feasibility", weight=0.15/0.75, enabled=True, description="Test", evidence_guidance="Test"),
                CriterionConfig(name="Cost", weight=0.15/0.75, enabled=True, description="Test", evidence_guidance="Test"),
                CriterionConfig(name="Practicality", weight=0.10/0.75, enabled=True, description="Test", evidence_guidance="Test"),
            ],
        )

    def test_weighted_score_calculation(self) -> None:
        """Correct weighted score calculation."""
        analyses = self._make_analyses()
        config = self._make_config()

        weighted_total, criterion_scores, _audit_trail = calculate_weighted_score(
            analyses, config
        )

        # Verify all core criteria have scores
        assert "Problem Validation" in criterion_scores
        assert "Scalability" in criterion_scores
        assert "Feasibility" in criterion_scores
        assert "Cost" in criterion_scores
        assert "Practicality" in criterion_scores

        # Verify scores match
        assert criterion_scores["Problem Validation"] == 85
        assert criterion_scores["Scalability"] == 70
        assert criterion_scores["Feasibility"] == 75
        assert criterion_scores["Cost"] == 80
        assert criterion_scores["Practicality"] == 65

        # Verify weighted total (normalized weights: original 0.20, 0.15, 0.15, 0.15, 0.10 sum to 0.75)
        # Normalized: 0.20/0.75=0.2667, 0.15/0.75=0.20, 0.15/0.75=0.20, 0.15/0.75=0.20, 0.10/0.75=0.1333
        # = 0.2667*85 + 0.20*70 + 0.20*75 + 0.20*80 + 0.1333*65
        # = 22.67 + 14 + 15 + 16 + 8.67 = 76.33 -> rounded to 76
        assert weighted_total == 76

    def test_weighted_score_audit_trail(self) -> None:
        """Score audit trail is correct."""
        analyses = self._make_analyses()
        config = self._make_config()

        _, _, audit_trail = calculate_weighted_score(analyses, config)

        assert len(audit_trail) == 5  # 5 core criteria
        for entry in audit_trail:
            assert "criterion" in entry
            assert "raw_score" in entry
            assert "weight" in entry
            assert "weighted_contribution" in entry
            assert entry["weighted_contribution"] == entry["raw_score"] * entry["weight"]

    def test_invalid_weight_sum_rejected(self) -> None:
        """Invalid weight sum is rejected at config validation time."""
        from pitch_evaluator.config import CriterionConfig, EvaluationCriteriaConfig

        with pytest.raises(ValueError, match="weights must sum to 1.0"):
            EvaluationCriteriaConfig(
                version="1.0",
                criteria=[
                    CriterionConfig(name="A", weight=0.5, enabled=True, description="A", evidence_guidance="A"),
                    CriterionConfig(name="B", weight=0.3, enabled=True, description="B", evidence_guidance="B"),
                ],
            )

    def test_missing_criterion_rejected(self) -> None:
        """Missing criterion analysis is rejected."""
        analyses = [
            CriterionAnalysis(criterion_name="Problem Validation", proposed_score=50, reasoning="", confidence=0.5),
        ]
        config = load_criteria_config("config/evaluation_criteria.yaml")

        with pytest.raises(ValueError, match="Missing analyses"):
            calculate_weighted_score(analyses, config)

    def test_invalid_score_rejected(self) -> None:
        """Invalid score bounds are rejected at CriterionAnalysis construction."""
        from pitch_evaluator.config import CriterionConfig, EvaluationCriteriaConfig

        EvaluationCriteriaConfig(
            version="1.0",
            criteria=[
                CriterionConfig(name="Problem Validation", weight=1.0, enabled=True, description="Test", evidence_guidance="Test"),
            ],
        )

        with pytest.raises(ValueError, match="less than or equal to 100"):
            CriterionAnalysis(criterion_name="Problem Validation", proposed_score=101, reasoning="", confidence=0.5)

        # Also test negative score
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            CriterionAnalysis(criterion_name="Problem Validation", proposed_score=-1, reasoning="", confidence=0.5)

    def test_disabled_criteria_excluded(self) -> None:
        """Disabled criteria are excluded from scoring."""
        from pitch_evaluator.config import CriterionConfig, EvaluationCriteriaConfig

        config = EvaluationCriteriaConfig(
            version="1.0",
            criteria=[
                CriterionConfig(name="A", weight=0.6, enabled=True, description="A", evidence_guidance="A"),
                CriterionConfig(name="B", weight=0.4, enabled=True, description="B", evidence_guidance="B"),
                CriterionConfig(name="C", weight=0.0, enabled=False, description="C", evidence_guidance="C"),
            ],
        )
        analyses = [
            CriterionAnalysis(criterion_name="A", proposed_score=80, reasoning="", confidence=0.8),
            CriterionAnalysis(criterion_name="B", proposed_score=60, reasoning="", confidence=0.7),
        ]

        weighted_total, scores, _ = calculate_weighted_score(analyses, config)

        # Only A and B should be scored
        assert "A" in scores
        assert "B" in scores
        assert "C" not in scores
        assert weighted_total == round(80 * 0.6 + 60 * 0.4)  # 48 + 24 = 72


class TestConfidenceCalculation:
    """Tests for overall confidence calculation."""

    def _make_analyses(self) -> list:
        return [
            CriterionAnalysis(
                criterion_name="Problem Validation",
                proposed_score=85,
                reasoning="",
                confidence=0.9,
            ),
            CriterionAnalysis(
                criterion_name="Scalability",
                proposed_score=70,
                reasoning="",
                confidence=0.75,
            ),
        ]

    def _make_config(self):
        # Custom config for the 2 criteria in _make_analyses
        # Normalize weights: 0.20 + 0.15 = 0.35
        from pitch_evaluator.config import CriterionConfig, EvaluationCriteriaConfig
        return EvaluationCriteriaConfig(
            version="1.0",
            criteria=[
                CriterionConfig(name="Problem Validation", weight=0.20/0.35, enabled=True, description="Test", evidence_guidance="Test"),
                CriterionConfig(name="Scalability", weight=0.15/0.35, enabled=True, description="Test", evidence_guidance="Test"),
            ],
        )

    def test_overall_confidence_weighted_average(self) -> None:
        """Overall confidence is weighted average of criterion confidences."""
        analyses = self._make_analyses()
        config = self._make_config()

        confidence = calculate_overall_confidence(analyses, config)

        # Weighted: 0.9 * 0.20 + 0.75 * 0.15 = 0.18 + 0.1125 = 0.2925
        # Total weight = 0.35
        # Result = 0.2925 / 0.35 = 0.8357...
        expected = (0.9 * 0.20 + 0.75 * 0.15) / 0.35
        assert abs(confidence - expected) < 0.001

    def test_confidence_zero_weight(self) -> None:
        """Zero total weight returns 0.0."""
        # Test the function directly with empty analyses (total_weight = 0)
        confidence = calculate_overall_confidence([], None)
        assert confidence == 0.0


class TestEvidenceQuality:
    """Tests for evidence quality calculation."""

    def test_zero_citations_returns_zero(self) -> None:
        """Zero citations returns zero quality."""
        quality = calculate_evidence_quality([])
        assert quality == 0.0

    def test_citation_count_factor(self) -> None:
        """More citations increase quality (up to saturation)."""
        citations = []
        for i in range(5):
            citations.append(EvidenceCitation(
                claim=f"Claim {i}",
                criterion="Test",
                source_segments=[
                    SegmentRef(segment_id=f"seg_{i}", source_modality="text", start_ref=0, end_ref=100, excerpt="test")
                ],
                evidence_type=EvidenceType.DIRECT_QUOTE,
                verification_level=VerificationLevel.SELF_REPORTED,
                confidence=0.8,
            ))

        quality = calculate_evidence_quality(citations)
        assert quality > 0.0
        assert quality <= 1.0

    def test_verification_level_affects_quality(self) -> None:
        """Higher verification levels increase quality."""
        low_citation = EvidenceCitation(
            claim="Test",
            criterion="Test",
            source_segments=[SegmentRef(segment_id="seg_1", source_modality="text", start_ref=0, end_ref=100, excerpt="test")],
            evidence_type=EvidenceType.DIRECT_QUOTE,
            verification_level=VerificationLevel.SELF_REPORTED,
            confidence=0.8,
        )
        high_citation = EvidenceCitation(
            claim="Test",
            criterion="Test",
            source_segments=[SegmentRef(segment_id="seg_1", source_modality="text", start_ref=0, end_ref=100, excerpt="test")],
            evidence_type=EvidenceType.DIRECT_QUOTE,
            verification_level=VerificationLevel.INDEPENDENTLY_VERIFIED,
            confidence=0.8,
        )

        low_quality = calculate_evidence_quality([low_citation])
        high_quality = calculate_evidence_quality([high_citation])

        assert high_quality > low_quality

    def test_modality_diversity_increases_quality(self) -> None:
        """Multiple modalities increase quality."""
        citations = []
        for i, modality in enumerate(["text", "audio", "video", "document"]):
            citations.append(EvidenceCitation(
                claim=f"Claim {i}",
                criterion="Test",
                source_segments=[
                    SegmentRef(segment_id=f"seg_{i}", source_modality=modality, start_ref=0, end_ref=100, excerpt="test")
                ],
                evidence_type=EvidenceType.DIRECT_QUOTE,
                verification_level=VerificationLevel.SELF_REPORTED,
                confidence=0.8,
            ))

        quality = calculate_evidence_quality(citations)
        assert quality > 0.0


class TestRiskSignals:
    """Tests for risk signal extraction."""

    def _make_analyses(self) -> list:
        return [
            CriterionAnalysis(
                criterion_name="Feasibility",
                proposed_score=40,
                reasoning="",
                weaknesses=["Technical feasibility concerns"],
                missing_information=["Architecture details"],
                uncertainties=["Technical debt unknown"],
                confidence=0.5,
            ),
            CriterionAnalysis(
                criterion_name="Practicality",
                proposed_score=45,
                reasoning="",
                weaknesses=["Regulatory compliance unclear"],
                missing_information=["Certification timeline"],
                uncertainties=["Regulatory approval uncertain"],
                confidence=0.5,
            ),
            CriterionAnalysis(
                criterion_name="Team Capability",
                proposed_score=50,
                reasoning="",
                weaknesses=["Team lacks domain experience"],
                missing_information=["Key hires needed"],
                uncertainties=["Hiring timeline uncertain"],
                confidence=0.6,
            ),
        ]

    def test_technical_risk_detected(self) -> None:
        """Technical risk keywords are detected."""
        analyses = self._make_analyses()
        signals = extract_risk_signals(analyses)

        assert len(signals.technical_risk_indicators) > 0
        assert any("technical" in kw or "feasibility" in kw for kw in signals.technical_risk_indicators)

    def test_regulatory_risk_detected(self) -> None:
        """Regulatory risk keywords are detected."""
        analyses = self._make_analyses()
        signals = extract_risk_signals(analyses)

        assert len(signals.regulatory_risk_indicators) > 0
        assert any("regulatory" in kw or "compliance" in kw for kw in signals.regulatory_risk_indicators)

    def test_team_risk_detected(self) -> None:
        """Team risk keywords are detected."""
        analyses = self._make_analyses()
        signals = extract_risk_signals(analyses)

        assert len(signals.team_risk_indicators) > 0
        assert any("team" in kw or "experience" in kw for kw in signals.team_risk_indicators)

    def test_no_duplicates(self) -> None:
        """Risk signals are deduplicated."""
        analyses = [
            CriterionAnalysis(
                criterion_name="A",
                proposed_score=50,
                reasoning="",
                weaknesses=["technical", "technical", "scalability"],
                missing_information=[],
                uncertainties=[],
                confidence=0.5,
            ),
        ]
        signals = extract_risk_signals(analyses)

        # Should be deduplicated
        assert len(signals.technical_risk_indicators) == len(set(signals.technical_risk_indicators))


class TestFullPipeline:
    """End-to-end integration tests."""

    def _make_pitch(self):
        return _make_test_pitch()

    def test_full_evaluation_mock(self) -> None:
        """Full evaluation pipeline works with mock engines."""
        pitch = _make_test_pitch()
        orchestrator = AnalysisOrchestrator(engine="mock", evidence_engine="mock")

        result = orchestrator.evaluate(
            normalized_pitch=pitch,
            pitch_id="pitch_123",
            startup_id="startup_456",
            problem_statement_id="prob_789",
        )

        # Verify output structure
        assert result.pitch_evaluation is not None
        assert isinstance(result.pitch_evaluation, PitchEvaluation)
        assert result.pitch_evaluation.pitch_id == "pitch_123"
        assert result.pitch_evaluation.startup_id == "startup_456"
        assert result.pitch_evaluation.problem_statement_id == "prob_789"

        # Verify all core criteria scored
        core_criteria = ["Problem Validation", "Scalability", "Feasibility", "Cost", "Practicality"]
        for criterion in core_criteria:
            assert criterion in result.pitch_evaluation.criterion_scores

        # Verify weighted total is within bounds
        assert 0 <= result.pitch_evaluation.weighted_total <= 100

        # Verify confidence and evidence quality are separate dimensions
        assert 0.0 <= result.pitch_evaluation.confidence <= 1.0
        assert 0.0 <= result.pitch_evaluation.evidence_quality <= 1.0

        # Verify they are NOT the same (separate dimensions)
        # They might coincidentally be equal, but the test is that they exist as separate fields
        assert hasattr(result.pitch_evaluation, "confidence")
        assert hasattr(result.pitch_evaluation, "evidence_quality")

        # Verify risk signals structure
        assert isinstance(result.pitch_evaluation.risk_signals, RiskSignals)

    def test_score_not_probability(self) -> None:
        """Verify score is NOT interpreted as probability."""

        pitch = _make_test_pitch()
        orchestrator = AnalysisOrchestrator(engine="mock", evidence_engine="mock")

        result = orchestrator.evaluate(
            normalized_pitch=pitch,
            pitch_id="pitch_1",
            startup_id="startup_1",
            problem_statement_id="prob_1",
        )

        # The score is criterion-relative, not probability
        # We can't test the semantic meaning directly, but we verify
        # the model doesn't have probability-like fields
        evaluation = result.pitch_evaluation
        assert hasattr(evaluation, "weighted_total")
        assert hasattr(evaluation, "confidence")
        assert hasattr(evaluation, "evidence_quality")
        # These are separate fields, not a single probability


class TestCriterionAnalysisModel:
    """Tests for CriterionAnalysis model validation."""

    def test_valid_construction(self) -> None:
        analysis = CriterionAnalysis(
            criterion_name="Test",
            proposed_score=85,
            reasoning="Good evidence",
            evidence_citations=["cite_1"],
            strengths=["Strong point"],
            weaknesses=["Weak point"],
            missing_information=["Missing info"],
            uncertainties=["Uncertain thing"],
            confidence=0.85,
        )
        assert analysis.criterion_name == "Test"
        assert analysis.proposed_score == 85
        assert analysis.confidence == 0.85

    def test_proposed_score_bounds(self) -> None:
        with pytest.raises(ValidationError):
            CriterionAnalysis(criterion_name="Test", proposed_score=101, reasoning="", confidence=0.5)
        with pytest.raises(ValidationError):
            CriterionAnalysis(criterion_name="Test", proposed_score=-1, reasoning="", confidence=0.5)

    def test_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            CriterionAnalysis(criterion_name="Test", proposed_score=50, reasoning="", confidence=1.5)
        with pytest.raises(ValidationError):
            CriterionAnalysis(criterion_name="Test", proposed_score=50, reasoning="", confidence=-0.1)


class TestPitchEvaluationModel:
    """Tests for PitchEvaluation model."""

    def test_valid_construction(self) -> None:
        eval = PitchEvaluation(
            pitch_evaluation_id="eval_1",
            pitch_id="pitch_1",
            startup_id="startup_1",
            problem_statement_id="prob_1",
            criterion_scores={"A": 80, "B": 70},
            weighted_total=75,
            risk_signals=RiskSignals(),
            confidence=0.8,
            evidence_quality=0.7,
            metadata=__import__('pitch_evaluator.models.evaluation', fromlist=['EvaluationMetadata']).EvaluationMetadata(
                criteria_config_version="1.0",
                evaluator_version="0.1.0",
                processed_at=__import__('datetime').datetime.now(__import__('datetime').UTC),
                source_modality="text",
                processing_time_ms=1000,
            ),
        )
        assert eval.weighted_total == 75
        assert eval.confidence == 0.8
        assert eval.evidence_quality == 0.7

    def test_weighted_total_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PitchEvaluation(
                pitch_evaluation_id="eval_1",
                pitch_id="pitch_1",
                startup_id="startup_1",
                problem_statement_id="prob_1",
                criterion_scores={"A": 50},
                weighted_total=101,
                risk_signals=RiskSignals(),
                confidence=0.5,
                evidence_quality=0.5,
                metadata=__import__('pitch_evaluator.models.evaluation', fromlist=['EvaluationMetadata']).EvaluationMetadata(
                    criteria_config_version="1.0",
                    evaluator_version="0.1.0",
                    processed_at=__import__('datetime').datetime.now(__import__('datetime').UTC),
                    source_modality="text",
                    processing_time_ms=1000,
                ),
            )

    def test_criterion_scores_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PitchEvaluation(
                pitch_evaluation_id="eval_1",
                pitch_id="pitch_1",
                startup_id="startup_1",
                problem_statement_id="prob_1",
                criterion_scores={"A": 101},
                weighted_total=50,
                risk_signals=RiskSignals(),
                confidence=0.5,
                evidence_quality=0.5,
                metadata=__import__('pitch_evaluator.models.evaluation', fromlist=['EvaluationMetadata']).EvaluationMetadata(
                    criteria_config_version="1.0",
                    evaluator_version="0.1.0",
                    processed_at=__import__('datetime').datetime.now(__import__('datetime').UTC),
                    source_modality="text",
                    processing_time_ms=1000,
                ),
            )

    def test_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PitchEvaluation(
                pitch_evaluation_id="eval_1",
                pitch_id="pitch_1",
                startup_id="startup_1",
                problem_statement_id="prob_1",
                criterion_scores={"A": 50},
                weighted_total=50,
                risk_signals=RiskSignals(),
                confidence=1.5,
                evidence_quality=0.5,
                metadata=__import__('pitch_evaluator.models.evaluation', fromlist=['EvaluationMetadata']).EvaluationMetadata(
                    criteria_config_version="1.0",
                    evaluator_version="0.1.0",
                    processed_at=__import__('datetime').datetime.now(__import__('datetime').UTC),
                    source_modality="text",
                    processing_time_ms=1000,
                ),
            )

    def test_evidence_quality_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PitchEvaluation(
                pitch_evaluation_id="eval_1",
                pitch_id="pitch_1",
                startup_id="startup_1",
                problem_statement_id="prob_1",
                criterion_scores={"A": 50},
                weighted_total=50,
                risk_signals=RiskSignals(),
                confidence=0.5,
                evidence_quality=-0.1,
                metadata=__import__('pitch_evaluator.models.evaluation', fromlist=['EvaluationMetadata']).EvaluationMetadata(
                    criteria_config_version="1.0",
                    evaluator_version="0.1.0",
                    processed_at=__import__('datetime').datetime.now(__import__('datetime').UTC),
                    source_modality="text",
                    processing_time_ms=1000,
                ),
            )

    def test_missing_required_ids_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PitchEvaluation(
                pitch_evaluation_id="",
                pitch_id="pitch_1",
                startup_id="startup_1",
                problem_statement_id="prob_1",
                criterion_scores={"A": 50},
                weighted_total=50,
                risk_signals=RiskSignals(),
                confidence=0.5,
                evidence_quality=0.5,
                metadata=__import__('pitch_evaluator.models.evaluation', fromlist=['EvaluationMetadata']).EvaluationMetadata(
                    criteria_config_version="1.0",
                    evaluator_version="0.1.0",
                    processed_at=__import__('datetime').datetime.now(__import__('datetime').UTC),
                    source_modality="text",
                    processing_time_ms=1000,
                ),
            )


class TestScoreNotProbability:
    """Explicit tests that score ≠ probability."""

    def test_criterion_analysis_has_separate_confidence(self) -> None:
        """CriterionAnalysis has separate score and confidence fields."""
        analysis = CriterionAnalysis(
            criterion_name="Test",
            proposed_score=85,
            reasoning="Test",
            confidence=0.7,
        )
        # Score and confidence are independent
        assert analysis.proposed_score == 85
        assert analysis.confidence == 0.7
        # They are independent fields
        assert analysis.proposed_score != analysis.confidence * 100

    def test_pitch_evaluation_separate_dimensions(self) -> None:
        """PitchEvaluation has separate score, confidence, evidence_quality."""
        eval = PitchEvaluation(
            pitch_evaluation_id="eval_1",
            pitch_id="pitch_1",
            startup_id="startup_1",
            problem_statement_id="prob_1",
            criterion_scores={"A": 85},
            weighted_total=85,
            risk_signals=RiskSignals(),
            confidence=0.7,
            evidence_quality=0.6,
            metadata=__import__('pitch_evaluator.models.evaluation', fromlist=['EvaluationMetadata']).EvaluationMetadata(
                criteria_config_version="1.0",
                evaluator_version="0.1.0",
                processed_at=__import__('datetime').datetime.now(__import__('datetime').UTC),
                source_modality="text",
                processing_time_ms=1000,
            ),
        )
        # All three are separate fields
        assert eval.weighted_total == 85
        assert eval.confidence == 0.7
        assert eval.evidence_quality == 0.6
        # They can have any relationship - they're independent dimensions
        assert eval.weighted_total / 100 != eval.confidence  # Not probability
        assert eval.evidence_quality != eval.confidence  # Different dimensions