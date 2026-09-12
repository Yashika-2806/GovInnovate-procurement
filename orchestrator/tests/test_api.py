import pytest
from fastapi.testclient import TestClient
from orchestrator.server import app
from shared.schemas.opportunity import OpportunityStatus

client = TestClient(app)

def test_full_lifecycle_api():
    # 1. Create
    opp = {
        "opportunity_id": "opp-1",
        "title": "AI Drone Inspection",
        "description": "Inspect oil pipelines.",
        "organization": "OilCo",
        "status": "active"
    }
    response = client.post("/api/workflows", json=opp)
    assert response.status_code == 201
    workflow_id = response.json()["workflow_id"]

    # 2. Submit Pitch
    pitch = {
        "pitch_id": "pitch-1",
        "startup_id": "start-1",
        "opportunity_id": "opp-1",
        "metadata": {}
    }
    client.post(f"/api/workflows/{workflow_id}/pitch", json=pitch)

    # 3. Evaluate Pitch
    client.post(f"/api/workflows/{workflow_id}/pitch/evaluate")

    # 4. Assess Risk
    client.post(f"/api/workflows/{workflow_id}/risk/assess")

    # 5. Human Review
    response = client.post(f"/api/workflows/{workflow_id}/human-review", params={"decision": "APPROVE"})
    assert response.json()["new_state"] == "STARTUP_SELECTED"

def test_human_gate_enforcement():
    # Create
    opp = {
        "opportunity_id": "opp-2",
        "title": "Test",
        "description": "Test",
        "organization": "Test",
        "status": "active"
    }
    response = client.post("/api/workflows", json=opp)
    workflow_id = response.json()["workflow_id"]

    # Try to skip directly to final decision (should fail)
    response = client.post(f"/api/workflows/{workflow_id}/final-decision", params={"decision": "SCALE"})
    assert response.status_code == 409
