import pytest
from fastapi.testclient import TestClient
from orchestrator.server import app

client = TestClient(app)

def test_extended_lifecycle_api():
    # 1. Create
    opp = {
        "opportunity_id": "opp-1",
        "title": "AI Drone Inspection",
        "description": "Inspect oil pipelines.",
        "organization": "OilCo",
        "status": "active"
    }
    response = client.post("/api/workflows", json=opp)
    workflow_id = response.json()["workflow_id"]

    # 2. Startup Selection
    startup_data = {
        "startup_id": "s1",
        "selection_reason": "High capability",
    }
    response = client.post(f"/api/workflows/{workflow_id}/startup-selection", json=startup_data)
    assert response.status_code == 200

    # 3. Pilot
    pilot_data = {
        "pilot_id": "p1",
        "description": "Test pilot",
    }
    response = client.post(f"/api/workflows/{workflow_id}/pilot", json=pilot_data)
    assert response.status_code == 200

    # 4. Milestone
    milestone_data = {
        "milestone_id": "m1",
        "description": "Initial milestone",
        "due_date": "2026-10-01"
    }
    response = client.post(f"/api/workflows/{workflow_id}/milestones", json=milestone_data)
    assert response.status_code == 200

    # 5. Evidence
    evidence_data = {
        "evidence_id": "e1",
        "milestone_id": "m1",
        "description": "Report",
        "link": "http://doc.url"
    }
    response = client.post(f"/api/workflows/{workflow_id}/milestones/m1/evidence", json=evidence_data)
    assert response.status_code == 200

    # 6. Scale Recommendation
    recommendation_data = {
        "recommendation": "SCALE",
        "rationale": "Good results",
        "confidence_score": 0.9
    }
    response = client.post(f"/api/workflows/{workflow_id}/scale-recommendation", json=recommendation_data)
    assert response.status_code == 200
