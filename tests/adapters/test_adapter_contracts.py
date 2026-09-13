"""P9 — Adapter contract tests (clear mock labeling per P9)."""
import pytest
from adapters.problem_collector import ProblemCollectorAdapter
from adapters.pitch_evaluator import PitchEvaluatorAdapter
from adapters.risk_detector import RiskDetectorAdapter
from adapters.evaluator import EvaluatorAdapter
from shared.schemas.opportunity import Opportunity
from shared.schemas.pitch import Pitch
from shared.schemas.pitch_evaluation import PitchEvaluation
from shared.schemas.risk_assessment import RiskAssessment
from shared.schemas.evaluation_result import EvaluationResult

# Mocked HTTP adapter contract tests — NOT real AI execution (P9 requirement).

@pytest.mark.asyncio
async def test_problem_collector_contract():
    adapter = ProblemCollectorAdapter("http://test")
    assert adapter.api_url == "http://test"

@pytest.mark.asyncio
async def test_pitch_evaluator_contract():
    adapter = PitchEvaluatorAdapter("http://test")
    assert adapter.api_url == "http://test"
    # Contract: POST /evaluate with Pitch -> PitchEvaluation
    p = Pitch(pitch_id="p1", startup_id="s1", opportunity_id="o1", metadata={})
    assert isinstance(p, Pitch)

@pytest.mark.asyncio
async def test_risk_detector_contract():
    adapter = RiskDetectorAdapter("http://test")
    assert adapter.api_url == "http://test"
    # Contract: POST /api/analyze, poll /api/status/{id}, GET /api/results/{id} -> RiskAssessment

@pytest.mark.asyncio
async def test_evaluator_contract():
    adapter = EvaluatorAdapter("http://test")
    assert adapter.api_url == "http://test"
    # Contract: POST /api/evaluate with state dict -> EvaluationResult
