from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# Handle imports: try absolute first (when run as module), fall back to relative (when run directly)
try:
    from backend.graph import evaluator_graph
    from backend.state import ScoringWeights
except (ImportError, ModuleNotFoundError):
    # Running from backend directory directly
    from graph import evaluator_graph
    from state import ScoringWeights

app = FastAPI(
    title="LangGraph Evaluator Agent API",
    description="Backend API executing LangGraph workflows for startup execution & milestone evaluation.",
    version="1.0.0"
)

# Enable CORS for React UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Payloads
class EvaluationRequest(BaseModel):
    state: Dict[str, Any]

class ApprovalGrantRequest(BaseModel):
    state: Dict[str, Any]
    granted_by: str

@app.get("/")
def read_root():
    return {"status": "online", "system": "LangGraph Startup Execution Evaluator Agent API"}

@app.post("/api/evaluate")
def run_evaluation(request: EvaluationRequest):
    """Executes the full LangGraph evaluation graph for a submitted state with thread checkpointing."""
    try:
        thread_id = request.state.get("startup_profile", {}).get("startup_id", "default-thread")
        config = {"configurable": {"thread_id": thread_id}}
        result_state = evaluator_graph.invoke(request.state, config=config)
        return {"success": True, "result": result_state, "thread_id": thread_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangGraph execution error: {str(e)}")

@app.post("/api/export-report")
def export_evaluation_report(request: EvaluationRequest):
    """Generates a structured Markdown evaluation report for program managers and auditors."""
    state = request.state
    profile = state.get("startup_profile", {})
    milestone = state.get("current_milestone", {})
    score = state.get("milestone_score", {})
    justification = state.get("justification_report", {})
    disbursement = state.get("escrow_disbursement", {})
    status = state.get("status", "Pending")
    action = state.get("recommended_action", "")

    report_md = f"""# Milestone Evaluation Audit Report
**Startup Name:** {profile.get('startup_name', 'N/A')}  
**Primary Domain:** {profile.get('primary_domain', 'N/A')}  
**Milestone Title:** {milestone.get('title', 'N/A')} (Sequence #{milestone.get('sequence_index', 1)})  
**Project Type:** {milestone.get('project_type', 'Software')}  
**Evaluation Status:** {status}  
**Generated At:** {state.get('execution_step', 'LangGraph Pipeline')}  

---

## Executive Summary & Next Action
- **Final Weighted Score:** {score.get('total_weighted_score', 0)} / 100
- **Pass Threshold:** {state.get('scoring_weights', {}).get('pass_threshold', 75.0)}
- **Evaluation Outcome:** {'PASSED' if score.get('passed') else 'FAILED / REMEDIATION REQUIRED'}
- **Recommended Next Action:** {action}

---

## Escrow Disbursement Authorization
- **Base Tranche Amount:** ${disbursement.get('tranche_amount_usd', 50000):,.2f} USD
- **Penalty Deductions:** -${disbursement.get('penalty_deduction_usd', 0):,.2f} USD
- **Net Release Payout:** ${disbursement.get('net_payout_usd', 0):,.2f} USD
- **Escrow Authorization Status:** {disbursement.get('escrow_status', 'Locked')}

---

## Point Justification Rationale
### Awarded Points
"""
    for award in justification.get("awards", []):
        report_md += f"- ✅ {award}\n"

    report_md += "\n### Deductions & Point Warnings\n"
    for ded in justification.get("deductions", []):
        report_md += f"- ⚠️ {ded}\n"

    report_md += f"""

---

## Dynamic Performance Vector Update
- **Initial Pitch Capability Score:** {profile.get('initial_pitch_score', 0)}
- **Demonstrated Execution Score:** {profile.get('demonstrated_execution_score', 0)}
- **Completed Milestones:** {profile.get('historical_milestones_completed', 0)} Passed | {profile.get('historical_milestones_failed', 0)} Failed
"""
    return {"success": True, "report_markdown": report_md}



@app.post("/api/grant-approval")
def grant_approval(request: ApprovalGrantRequest):
    """Grants contractual approval for a blocked milestone and re-executes LangGraph with checkpointer."""
    state = request.state
    if "current_milestone" in state:
        state["current_milestone"]["contractual_approval_granted"] = True
        state["current_milestone"]["status"] = "Submitted"
    state["human_approval_granted"] = True
    
    try:
        thread_id = state.get("startup_profile", {}).get("startup_id", "default-thread")
        config = {"configurable": {"thread_id": thread_id}}
        result_state = evaluator_graph.invoke(state, config=config)
        return {"success": True, "result": result_state, "thread_id": thread_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangGraph re-execution error: {str(e)}")
@app.get("/api/sample-startups")
def get_sample_startups():
    """Returns curated preset startup scenarios for Software, Hardware, and Hybrid projects."""
    return {
        "startups": [
            {
                "id": "startup-01",
                "name": "AeroSense Robotics",
                "primary_domain": "Industrial IoT",
                "initial_pitch_score": 88.0,
                "demonstrated_execution_score": 0.0,
                "domain_relevance_vector": {
                    "Industrial IoT": 88.0,
                    "Hardware/Sensors": 84.0,
                    "Robotics": 82.0,
                    "Healthcare AI": 50.0
                },
                "problem": {
                    "title": "Autonomous Pipeline Inspection Drones",
                    "domain": "Industrial IoT"
                },
                "milestone": {
                    "id": "m-hw-1",
                    "title": "Field Pilot & Sensor Telemetry Validation",
                    "project_type": "Hardware",
                    "sequence_index": 3,
                    "objective": "Deploy 5 sensor units in high-pressure oil pipelines and stream 100+ telemetry frames.",
                    "requirements": [
                        "5 field-deployed sensor units at GPS location",
                        "Continuous telemetry sensor log feed",
                        "Third-party independent inspection report"
                    ],
                    "kpis": [
                        {"id": "kpi-telemetry", "name": "Telemetry Packet Reliability", "target_value": 98.0, "actual_value": 99.4, "unit": "%", "weight": 1.0, "achieved": True},
                        {"id": "kpi-battery", "name": "Continuous Operation Duration", "target_value": 48.0, "actual_value": 52.0, "unit": "hours", "weight": 1.0, "achieved": True}
                    ],
                    "acceptance_criteria": ["Ground GPS location verified", "Telemetry > 98% packet delivery", "Inspection grade A"],
                    "contractual_approval_required": True,
                    "contractual_approval_granted": False,
                    "status": "Pending"
                },
                "evidence": [
                    {
                        "id": "ev-hw-gps",
                        "evidence_type": "geolocation",
                        "source": "GPS Telemetry System #8812",
                        "timestamp": "2026-09-11T12:00:00Z",
                        "verification_level": "Independently verified",
                        "relationship_to_milestone": "5 field-deployed sensor units at GPS location",
                        "relevant_claim": "GPS coordinates locked at site 31.22N 121.48E",
                        "content_payload": {
                            "geolocation_verified": True,
                            "field_deployment_count": 5,
                            "coordinates": ["31.221,121.482", "31.225,121.489"]
                        }
                    },
                    {
                        "id": "ev-hw-telem",
                        "evidence_type": "device_telemetry",
                        "source": "AWS IoT Core Telemetry Stream",
                        "timestamp": "2026-09-11T14:30:00Z",
                        "verification_level": "System-generated",
                        "relationship_to_milestone": "Continuous telemetry sensor log feed",
                        "relevant_claim": "150 telemetry packets logged with zero loss",
                        "content_payload": {
                            "telemetry_active": True,
                            "telemetry_readings_count": 150,
                            "Telemetry Packet Reliability": 99.4,
                            "Continuous Operation Duration": 52.0
                        }
                    },
                    {
                        "id": "ev-hw-audit",
                        "evidence_type": "inspection_records",
                        "source": "Bureau Veritas Ground Auditor",
                        "timestamp": "2026-09-10T16:00:00Z",
                        "verification_level": "Third-party",
                        "relationship_to_milestone": "Third-party independent inspection report",
                        "relevant_claim": "Auditor signed off with Grade A",
                        "content_payload": {
                            "third_party_inspection_grade": "A",
                            "inspector_notes": "All hardware enclosures IP67 compliant."
                        }
                    }
                ]
            },
            {
                "id": "startup-02",
                "name": "MediAI Diagnostics",
                "primary_domain": "Healthcare AI",
                "initial_pitch_score": 94.0,
                "demonstrated_execution_score": 0.0,
                "domain_relevance_vector": {
                    "Healthcare AI": 94.0,
                    "Medical Devices": 90.0,
                    "Diagnostics": 92.0,
                    "Industrial IoT": 45.0
                },
                "problem": {
                    "title": "Early Stage Mammography Screening AI",
                    "domain": "Healthcare AI"
                },
                "milestone": {
                    "id": "m-sw-1",
                    "title": "Clinical Model Prototype & API Microservice",
                    "project_type": "Software",
                    "sequence_index": 2,
                    "objective": "Deliver production-ready DICOM image inference API with automated CI/CD and unit tests.",
                    "requirements": [
                        "GitHub repo with CI/CD pipeline",
                        "Automated test suite with >75% coverage",
                        "FastAPI OpenAPI documentation & README"
                    ],
                    "kpis": [
                        {"id": "kpi-sens", "name": "Clinical Sensitivity", "target_value": 92.0, "actual_value": 94.8, "unit": "%", "weight": 1.0, "achieved": True},
                        {"id": "kpi-latency", "name": "API Response Time", "target_value": 500, "actual_value": 320, "unit": "ms", "weight": 1.0, "achieved": True}
                    ],
                    "acceptance_criteria": ["CI/CD Status PASS", "Test Coverage > 75%", "API docs complete"],
                    "contractual_approval_required": False,
                    "contractual_approval_granted": False,
                    "status": "Pending"
                },
                "evidence": [
                    {
                        "id": "ev-sw-github",
                        "evidence_type": "github_repo",
                        "source": "https://github.com/mediai-health/mammography-core",
                        "timestamp": "2026-09-11T09:00:00Z",
                        "verification_level": "System-generated",
                        "relationship_to_milestone": "GitHub repo with CI/CD pipeline, Automated test suite, API docs",
                        "relevant_claim": "65 commits, passing CI/CD, 89.2% test coverage",
                        "content_payload": {
                            "commit_count": 65,
                            "merged_prs_count": 18,
                            "ci_cd_status": "SUCCESS",
                            "test_coverage_percent": 89.2,
                            "readme_present": True,
                            "api_docs_present": True,
                            "Clinical Sensitivity": 94.8,
                            "API Response Time": 320
                        }
                    }
                ]
            },
            {
                "id": "startup-03",
                "name": "QuickApp Systems",
                "primary_domain": "Fintech",
                "initial_pitch_score": 81.0,
                "demonstrated_execution_score": 0.0,
                "domain_relevance_vector": {
                    "Fintech": 81.0,
                    "E-commerce": 78.0,
                    "Healthcare AI": 40.0
                },
                "problem": {
                    "title": "Cross-Border Settlement SDK",
                    "domain": "Fintech"
                },
                "milestone": {
                    "id": "m-sw-dummy",
                    "title": "Core Gateway Implementation",
                    "project_type": "Software",
                    "sequence_index": 1,
                    "objective": "Build secure payment microservice",
                    "requirements": [
                        "GitHub repo with CI/CD pipeline",
                        "Automated test suite",
                        "API documentation"
                    ],
                    "kpis": [],
                    "acceptance_criteria": ["Working code"],
                    "contractual_approval_required": False,
                    "contractual_approval_granted": False,
                    "status": "Pending"
                },
                "evidence": [
                    {
                        "id": "ev-sw-dummy",
                        "evidence_type": "github_repo",
                        "source": "https://github.com/quickapp/demo-stub",
                        "timestamp": "2026-09-11T11:00:00Z",
                        "verification_level": "Self-reported",
                        "relationship_to_milestone": "GitHub repo",
                        "relevant_claim": "Template uploaded",
                        "content_payload": {
                            "commit_count": 1,
                            "merged_prs_count": 0,
                            "is_template_repo_only": True,
                            "ci_cd_status": "NONE",
                            "test_coverage_percent": 0.0,
                            "readme_present": False,
                            "api_docs_present": False
                        }
                    }
                ]
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
