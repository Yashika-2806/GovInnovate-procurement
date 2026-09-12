"""Tests for the Pitch Evaluator FastAPI boundary."""

from __future__ import annotations

from fastapi.testclient import TestClient

from pitch_evaluator.api import create_app
from pitch_evaluator.fixtures import SYNTHETIC_PITCH_TEXT
from pitch_evaluator.service import PitchEvaluator


def test_api_health() -> None:
    """Health check endpoint returns 200 with service info."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "pitch-evaluator-agent"
    assert data["version"] == "0.1.0"
    assert data["active_criteria"] > 0


def test_api_evaluate_synthetic_pitch() -> None:
    """POST /evaluate successfully evaluates a synthetic pitch text."""
    evaluator = PitchEvaluator(engine="mock", evidence_engine="mock")
    app = create_app(evaluator=evaluator)
    client = TestClient(app)

    payload = {
        "pitch_id": "test_pitch_api_01",
        "startup_id": "test_startup_api_01",
        "problem_statement_id": "test_ps_api_01",
        "pitch_content": SYNTHETIC_PITCH_TEXT,
    }

    response = client.post("/evaluate", json=payload)
    assert response.status_code == 200

    data = response.json()
    # Required core fields
    assert data["pitch_id"] == "test_pitch_api_01"
    assert data["startup_id"] == "test_startup_api_01"
    assert data["problem_statement_id"] == "test_ps_api_01"
    assert "pitch_evaluation_id" in data
    assert "criterion_scores" in data
    assert "weighted_total" in data
    assert "evidence_citations" in data
    assert "strengths" in data
    assert "weaknesses" in data
    assert "missing_information" in data
    assert "uncertainties" in data
    assert "risk_signals" in data
    assert "confidence" in data
    assert "evidence_quality" in data
    assert "calculation_audit" in data
    assert "metadata" in data

    # Differentiated scores
    scores = list(data["criterion_scores"].values())
    assert len(set(scores)) > 1, f"Expected non-identical scores, got {scores}"

    # Meaningful outputs and structured evidence objects
    assert len(data["evidence_citations"]) > 0
    first_cite = data["evidence_citations"][0]
    assert isinstance(first_cite, dict), f"Expected dict, got {type(first_cite)}"
    assert "claim" in first_cite
    assert "criterion" in first_cite
    assert "source_segments" in first_cite
    assert isinstance(first_cite["source_segments"], list)
    assert len(first_cite["source_segments"]) > 0
    assert "segment_id" in first_cite["source_segments"][0]
    assert "source_modality" in first_cite["source_segments"][0]
    assert "excerpt" in first_cite["source_segments"][0]
    assert "evidence_type" in first_cite
    assert "verification_level" in first_cite
    assert "confidence" in first_cite
    assert "notes" in first_cite

    assert 0 <= data["weighted_total"] <= 100
    assert 0.0 <= data["confidence"] <= 1.0
    assert 0.0 <= data["evidence_quality"] <= 1.0
    assert len(data["calculation_audit"]) == len(data["criterion_scores"])


def test_api_evaluate_missing_content_and_file() -> None:
    """POST /evaluate returns 400 when neither content nor file_path is provided."""
    app = create_app()
    client = TestClient(app)

    payload = {
        "pitch_id": "pitch_bad",
        "startup_id": "startup_bad",
    }
    response = client.post("/evaluate", json=payload)
    assert response.status_code == 400
    assert "pitch_content" in response.json()["detail"] or "file_path" in response.json()["detail"]


def test_api_evaluate_nonexistent_file() -> None:
    """POST /evaluate returns 404 when file_path does not exist."""
    app = create_app()
    client = TestClient(app)

    payload = {
        "pitch_id": "pitch_missing",
        "startup_id": "startup_missing",
        "file_path": "/tmp/nonexistent_pitch_file_12345.pdf",
    }
    response = client.post("/evaluate", json=payload)
    assert response.status_code == 404


def test_downstream_orchestrator_integration_contract() -> None:
    """Simulates a downstream consumer (e.g. Workflow Orchestrator).

    - Loads examples/evaluate_request.json
    - Sends to POST /evaluate
    - Asserts all required contract fields exist
    - Asserts evidence_citations contains full structured objects (not plain strings)
    - Asserts criterion_scores contains all enabled criteria
    - Asserts weighted_total matches calculation_audit
    - Asserts confidence is a float in [0.0, 1.0]
    - Asserts evidence_quality is a float in [0.0, 1.0]
    - Asserts response matches examples/pitch_evaluation_response.json schema
    """
    import json
    from pathlib import Path

    request_path = Path(__file__).parent.parent / "examples" / "evaluate_request.json"
    assert request_path.exists(), f"Missing example request at {request_path}"
    with open(request_path, encoding="utf-8") as f:
        req_payload = json.load(f)

    response_example_path = Path(__file__).parent.parent / "examples" / "pitch_evaluation_response.json"
    assert response_example_path.exists(), f"Missing example response at {response_example_path}"
    with open(response_example_path, encoding="utf-8") as f:
        expected_schema_example = json.load(f)

    app = create_app()
    client = TestClient(app)

    response = client.post("/evaluate", json=req_payload)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()

    # 1. Expected top-level keys match example schema
    expected_top_keys = {k for k in expected_schema_example if not k.startswith("_")}
    actual_top_keys = {k for k in data if not k.startswith("_")}
    assert expected_top_keys.issubset(actual_top_keys), f"Missing keys: {expected_top_keys - actual_top_keys}"

    # 2. Correlated IDs
    assert data["pitch_id"] == req_payload["pitch_id"]
    assert data["startup_id"] == req_payload["startup_id"]
    assert data["problem_statement_id"] == req_payload["problem_statement_id"]

    # 3. Structured evidence citations (NOT plain strings)
    assert len(data["evidence_citations"]) > 0
    for citation in data["evidence_citations"]:
        assert isinstance(citation, dict), f"Expected dict, got {type(citation)}"
        assert "claim" in citation and isinstance(citation["claim"], str)
        assert "criterion" in citation and isinstance(citation["criterion"], str)
        assert "source_segments" in citation and isinstance(citation["source_segments"], list)
        assert len(citation["source_segments"]) > 0
        for seg in citation["source_segments"]:
            assert "segment_id" in seg
            assert "source_modality" in seg
            assert "excerpt" in seg
        assert "evidence_type" in citation
        assert "verification_level" in citation
        assert "confidence" in citation and isinstance(citation["confidence"], (int, float))
        assert "notes" in citation

    # 4. Criterion scores contain all enabled criteria
    assert len(data["criterion_scores"]) > 0
    assert len(data["calculation_audit"]) == len(data["criterion_scores"])

    # 5. Weighted total matches calculation audit
    audit_weighted_total = round(sum(item["weighted_contribution"] for item in data["calculation_audit"]))
    assert data["weighted_total"] == audit_weighted_total

    # 6. Confidence and evidence quality
    assert isinstance(data["confidence"], (int, float))
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["evidence_quality"], (int, float))
    assert 0.0 <= data["evidence_quality"] <= 1.0

    # 7. Risk signals are structured
    assert isinstance(data["risk_signals"], dict)
    for risk_field in [
        "technical_risk_indicators",
        "regulatory_risk_indicators",
        "team_risk_indicators",
        "market_risk_indicators",
        "financial_risk_indicators",
    ]:
        assert risk_field in data["risk_signals"]
        assert isinstance(data["risk_signals"][risk_field], list)

