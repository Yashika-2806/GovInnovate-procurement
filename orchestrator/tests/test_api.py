import pytest
from fastapi.testclient import TestClient
from orchestrator.server import app

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
    client.post(f"/api/workflows/{workflow_id}/human-review", params={"decision": "APPROVE"})

    # 6. Evaluate Milestone (as part of lifecycle placeholder)
    response = client.post(f"/api/workflows/{workflow_id}/milestones/m1/evaluate")
    assert response.status_code == 200
    assert response.json()["status"] == "milestone_evaluated_pass"
