import pytest
from fastapi.testclient import TestClient
from orchestrator.server import app
from shared.schemas.opportunity import Opportunity, OpportunityStatus

client = TestClient(app)

def test_workflow_lifecycle_api():
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
    response = client.post(f"/api/workflows/{workflow_id}/pitch", json=pitch)
    assert response.status_code == 200

    # 3. Evaluate Pitch
    response = client.post(f"/api/workflows/{workflow_id}/pitch/evaluate")
    assert response.status_code == 200

    # Verify state
    response = client.get(f"/api/workflows/{workflow_id}")
    assert response.json()["state"] == "PITCH_EVALUATED"

def test_invalid_transition():
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

    # Try to evaluate before submitting pitch
    response = client.post(f"/api/workflows/{workflow_id}/pitch/evaluate")
    assert response.status_code == 409
