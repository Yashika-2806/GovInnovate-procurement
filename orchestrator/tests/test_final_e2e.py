import pytest
from fastapi.testclient import TestClient
from orchestrator.server import app

client = TestClient(app)

def test_complete_final_lifecycle_e2e():
    # 1. Create workflow
    opp = {
        "opportunity_id": "opp-final",
        "title": "Green Energy Pilot",
        "description": "Renewable energy procurement.",
        "organization": "EnergyCo",
        "status": "active"
    }
    resp = client.post("/api/workflows", json=opp)
    assert resp.status_code == 201, resp.json()
    wf_id = resp.json()["workflow_id"]

    # 2. Pitch
    client.post(f"/api/workflows/{wf_id}/pitch", json={
        "pitch_id": "p-final", "startup_id": "s-final", "opportunity_id": "opp-final", "metadata": {}
    })

    # 3. Pitch evaluation
    client.post(f"/api/workflows/{wf_id}/pitch/evaluate")

    # 4. Risk
    client.post(f"/api/workflows/{wf_id}/risk/assess")

    # 5. Human review (gate) — APPROVE
    resp = client.post(f"/api/workflows/{wf_id}/human-review", params={"decision": "APPROVE"})
    assert resp.status_code == 200, resp.json()

    # 6. Startup selection
    resp = client.post(f"/api/workflows/{wf_id}/startup-selection", json={
        "startup_id": "s-final", "selection_reason": "Best technical score"
    })
    assert resp.status_code == 200, resp.json()

    # 7. Pilot (allocation step implicitly via transition from STARTUP_SELECTED -> PILOT_CREATED allowed)
    resp = client.post(f"/api/workflows/{wf_id}/pilot", json={
        "pilot_id": "pilot-final", "description": "6-month pilot"
    })
    assert resp.status_code == 200, resp.json()

    # 8. Milestone
    resp = client.post(f"/api/workflows/{wf_id}/milestones", json={
        "milestone_id": "m-final", "description": "Deployment milestone", "due_date": "2026-12-01"
    })
    assert resp.status_code == 200, resp.json()

    # 9. Evidence (verified)
    resp = client.post(f"/api/workflows/{wf_id}/milestones/m-final/evidence", json={
        "evidence_id": "e-final", "milestone_id": "m-final",
        "description": "Verified deployment report", "link": "http://doc.url", "status": "verified"
    })
    assert resp.status_code == 200, resp.json()

    # 10. Milestone evaluation (PASS expected)
    resp = client.post(f"/api/workflows/{wf_id}/milestones/m-final/evaluate")
    assert resp.status_code == 200, resp.json()
    assert resp.json()["result"] == "PASS", resp.json()

    # 11. Final evaluation (uses actual evidence / pilot / milestones)
    resp = client.post(f"/api/workflows/{wf_id}/final-evaluation", json={
        "evaluation_id": "eval-final", "milestone_id": "m-final", "status": "PASS",
        "kpi_measurements": [{"name":"deployment_rate","target":100,"actual":95,"achieved":True}],
        "evidence_submitted": [], "explanation": "Pilot successful", "confidence": 0.92,
        "remediation_required": None, "recommendation": "Proceed to scale"
    })
    assert resp.status_code == 200, resp.json()

    # 12. Performance (actual pilot info)
    resp = client.post(f"/api/workflows/{wf_id}/performance", json={
        "startup_id": "s-final", "summary": "Pilot performance summary",
        "metrics": {"uptime": 0.99, "cost_savings": 0.15}
    })
    assert resp.status_code == 200, resp.json()

    # Need transition through scale-recommendation to AWAITING_FINAL_DECISION before final-decision
    # But scale recommendation requires FINAL_EVALUATION -> PERFORMANCE_UPDATED -> SCALE_RECOMMENDATION -> AWAITING_FINAL_DECISION
    # Current state after final-evaluation = FINAL_EVALUATION; after performance = PERFORMANCE_UPDATED
    resp_scale = client.post(f"/api/workflows/{wf_id}/scale-recommendation", json={
        "recommendation": "SCALE", "rationale": "Verified evidence and positive performance", "confidence_score": 0.91
    })
    assert resp_scale.status_code == 200, resp_scale.json()

    # Verify transition to AWAITING_FINAL_DECISION
    wf_check = client.get(f"/api/workflows/{wf_id}").json()
    assert wf_check["context"]["state"] == "AWAITING_FINAL_DECISION", f"Expected AWAITING_FINAL_DECISION, got {wf_check['context']['state']}"

    # 13. Final human decision (from AWAITING_FINAL_DECISION)
    resp = client.post(f"/api/workflows/{wf_id}/final-decision", params={"decision": "APPROVE"})
    assert resp.status_code == 200, resp.json()
    # Must reach COMPLETED
    assert resp.json()["status"] == "final_decision_complete", resp.json()

    # 15. Verify final state and persistence
    wf_resp = client.get(f"/api/workflows/{wf_id}")
    assert wf_resp.status_code == 200, wf_resp.json()
    ctx = wf_resp.json()["context"]
    assert ctx.get("state") == "COMPLETED", f"Expected COMPLETED, got {ctx.get('state')}"
    assert ctx.get("evaluation_result") is not None
    assert ctx.get("performance") is not None
    assert ctx.get("scale_recommendation") is not None
    assert ctx.get("milestones") is not None
    assert ctx.get("evidence") is not None
    # Audit exists
    audit_resp = client.get(f"/api/workflows/{wf_id}/audit")
    assert audit_resp.status_code == 200
    audit = audit_resp.json()
    assert len(audit) > 0
    # Verify milestone PASS stored
    assert "m-final" in ctx.get("milestones", {})

    # 16. Verify human gate protects invalid final decision
    # Create second workflow, try final-decision too early
    resp2 = client.post("/api/workflows", json={
        "opportunity_id":"o-early","title":"E","description":"D","organization":"O","status":"active"
    })
    wf2 = resp2.json()["workflow_id"]
    resp_bad = client.post(f"/api/workflows/{wf2}/final-decision", params={"decision":"APPROVE"})
    assert resp_bad.status_code == 409, f"Expected 409 for invalid final-decision, got {resp_bad.status_code}"
