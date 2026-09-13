"""P9 — Adapter contract tests (explicit mock labeling)."""
import pytest
from adapters.problem_collector import ProblemCollectorAdapter
from adapters.pitch_evaluator import PitchEvaluatorAdapter
from adapters.risk_detector import RiskDetectorAdapter
from adapters.evaluator import EvaluatorAdapter

def test_problem_collector_contract():
    adapter = ProblemCollectorAdapter("http://localhost:8001")
    assert adapter.api_url == "http://localhost:8001"

def test_pitch_evaluator_contract():
    adapter = PitchEvaluatorAdapter("http://localhost:8001")
    assert adapter.api_url == "http://localhost:8001"

def test_risk_detector_contract():
    adapter = RiskDetectorAdapter("http://localhost:8000")
    assert adapter.api_url == "http://localhost:8000"

def test_evaluator_contract():
    adapter = EvaluatorAdapter("http://localhost:8003")
    assert adapter.api_url == "http://localhost:8003"
