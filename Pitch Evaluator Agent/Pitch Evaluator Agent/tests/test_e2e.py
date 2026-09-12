"""End-to-end integration tests demonstrating meaningful deterministic evaluation."""

from __future__ import annotations

import pytest

from pitch_evaluator.fixtures import SYNTHETIC_PITCH_TEXT, create_synthetic_pitch_fixture
from pitch_evaluator.models import (
    EvidenceCitation,
    EvidenceType,
    PitchEvaluation,
    RiskSignals,
    SegmentRef,
    VerificationLevel,
)
from pitch_evaluator.service import EvaluatePitchRequest, PitchEvaluator


def test_end_to_end_deterministic_pipeline_meaningful_evaluation() -> None:
    """Demonstrate complete 8-stage deterministic evaluation with meaningful outputs.

    Synthetic Pitch -> NormalizedPitch -> EvidenceCitation[] -> CriterionAnalysis[]
    -> Weighted Score -> PitchEvaluation
    """
    evaluator = PitchEvaluator(engine="mock", evidence_engine="mock")
    pitch = create_synthetic_pitch_fixture()

    evaluation = evaluator.evaluate_normalized_pitch(
        normalized_pitch=pitch,
        pitch_id="pitch_e2e_synth_001",
        startup_id="startup_e2e_govprocure",
        problem_statement_id="ps_e2e_procurement_2026",
    )

    # 1. Verification of identity and schema
    assert isinstance(evaluation, PitchEvaluation)
    assert evaluation.pitch_id == "pitch_e2e_synth_001"
    assert evaluation.startup_id == "startup_e2e_govprocure"
    assert evaluation.problem_statement_id == "ps_e2e_procurement_2026"

    # 2. Evidence citations extracted and structured fields preserved
    assert len(evaluation.evidence_citations) > 0, "Expected evidence citations to be extracted from pitch"
    first_citation = evaluation.evidence_citations[0]
    assert isinstance(first_citation, EvidenceCitation)
    assert first_citation.claim
    assert first_citation.criterion
    assert len(first_citation.source_segments) > 0
    assert isinstance(first_citation.source_segments[0], SegmentRef)
    assert first_citation.source_segments[0].segment_id
    assert first_citation.source_segments[0].source_modality
    assert first_citation.source_segments[0].excerpt
    assert isinstance(first_citation.evidence_type, EvidenceType)
    assert isinstance(first_citation.verification_level, VerificationLevel)
    assert 0.0 <= first_citation.confidence <= 1.0
    assert first_citation.notes is not None

    # 3. Differentiated criterion scores (must NOT all be identical)
    scores = evaluation.criterion_scores
    unique_scores = set(scores.values())
    assert len(unique_scores) > 1, f"Expected non-identical criterion scores, got {unique_scores}"

    # Criteria with strong evidence score higher than criteria with zero evidence
    assert scores["Government Fit"] > scores["Competitive Differentiation"]
    assert scores["Scalability"] > scores["Competitive Differentiation"]

    # 4. Deterministic weighted score is mathematically correct
    assert 0 <= evaluation.weighted_total <= 100
    assert len(evaluation.calculation_audit) == len(scores)

    computed_weighted_sum = sum(entry["weighted_contribution"] for entry in evaluation.calculation_audit)
    assert round(computed_weighted_sum) == evaluation.weighted_total
    total_weights = sum(entry["weight"] for entry in evaluation.calculation_audit)
    assert pytest.approx(total_weights, abs=1e-6) == 1.0

    # 5. Semantic independence: Confidence != Evidence Quality != Score
    assert 0.0 <= evaluation.confidence <= 1.0
    assert 0.0 <= evaluation.evidence_quality <= 1.0
    assert evaluation.evidence_quality > 0.0

    # 6. Preserved strengths, weaknesses, missing info, uncertainties
    assert len(evaluation.strengths) > 0, "Criteria with sufficient evidence should yield strengths"
    assert len(evaluation.weaknesses) > 0, "Criteria with evidence gaps should yield weaknesses"
    assert len(evaluation.missing_information) > 0, "Missing info must be preserved"
    assert len(evaluation.uncertainties) > 0, "Uncertainties must be preserved"

    # 7. Risk signals generated and categorized
    assert isinstance(evaluation.risk_signals, RiskSignals)
    assert len(evaluation.risk_signals.team_risk_indicators) > 0
    assert len(evaluation.risk_signals.financial_risk_indicators) > 0

    # 8. Metadata present and valid
    assert evaluation.metadata.criteria_config_version == "1.0"
    assert evaluation.metadata.evaluator_version == "0.1.0"
    assert evaluation.metadata.processing_time_ms >= 0


def test_end_to_end_request_contract_flow() -> None:
    """Verify integration via EvaluatePitchRequest contract."""
    evaluator = PitchEvaluator(engine="mock", evidence_engine="mock")

    request = EvaluatePitchRequest(
        pitch_id="pitch_contract_01",
        startup_id="startup_contract_01",
        problem_statement_id="ps_contract_01",
        pitch_content=SYNTHETIC_PITCH_TEXT,
        context={"procurement_tier": "municipal", "budget_ceiling": 500000},
    )

    evaluation = evaluator.evaluate_pitch(request)

    assert evaluation.pitch_id == "pitch_contract_01"
    assert evaluation.startup_id == "startup_contract_01"
    assert len(evaluation.evidence_citations) > 0
    assert isinstance(evaluation.evidence_citations[0], EvidenceCitation)
    assert len(evaluation.evidence_citations[0].source_segments) > 0
    assert len(set(evaluation.criterion_scores.values())) > 1
    assert evaluation.weighted_total >= 40
    assert len(evaluation.calculation_audit) > 0
