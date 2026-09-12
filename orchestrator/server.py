from fastapi import FastAPI, HTTPException, status, Depends
from typing import List, Optional
from orchestrator.instance import WorkflowInstance
from orchestrator.state import ProcurementState
from orchestrator.persistence import SessionLocal, WorkflowModel
from shared.schemas.opportunity import Opportunity
from shared.schemas.pitch import Pitch
from shared.schemas.evaluation_result import EvaluationResult
from shared.schemas.startup_selection import StartupSelection
from shared.schemas.pilot import Pilot
from shared.schemas.milestone import Milestone
from shared.schemas.evidence import Evidence
from shared.schemas.remediation import Remediation
from shared.schemas.performance import PerformanceProfile
from shared.schemas.scale_recommendation import ScaleRecommendation
from adapters.pitch_evaluator import PitchEvaluatorAdapter
from adapters.risk_detector import RiskDetectorAdapter
from adapters.evaluator import EvaluatorAdapter
import uuid

app = FastAPI(title="GovInnovate Procurement API")

# Simple CORS setup for dev
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Adapters
pitch_evaluator = PitchEvaluatorAdapter("http://localhost:8001")
risk_detector = RiskDetectorAdapter("http://localhost:8002")
evaluator = EvaluatorAdapter("http://localhost:8003")

@app.get("/api/workflows/{workflow_id}/milestones")
def get_milestones(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    instance = WorkflowInstance(db_wf.workflow_id, db_wf.context['opportunity_id']) # simplified
    return instance.milestones

@app.get("/api/workflows/{workflow_id}/milestones/{milestone_id}")
def get_milestone(workflow_id: str, milestone_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf or milestone_id not in db_wf.context.get('milestones', {}):
        raise HTTPException(status_code=404)
    return db_wf.context['milestones'][milestone_id]

@app.get("/api/workflows/{workflow_id}/milestones/{milestone_id}/evidence")
def get_evidence(workflow_id: str, milestone_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    return db_wf.context.get('evidence', {}).get(milestone_id, [])

@app.post("/api/workflows/{workflow_id}/milestones/{milestone_id}/remediation")
def submit_remediation(workflow_id: str, milestone_id: str, remediation: Remediation, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    db_wf.state = ProcurementState.REMEDIATION.name
    db.commit()
    return {"status": "remediation_submitted"}

@app.post("/api/workflows/{workflow_id}/final-evaluation")
def final_evaluation(workflow_id: str, evaluation: EvaluationResult, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    db_wf.state = ProcurementState.FINAL_EVALUATION.name
    db.commit()
    return {"status": "final_evaluation_complete"}

@app.get("/api/workflows/{workflow_id}/performance")
def get_performance(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    return db_wf.context.get('performance')

@app.get("/api/workflows/{workflow_id}/audit")
def get_audit(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    # The history/audit events should be stored somewhere
    return db_wf.context.get('history', [])

@app.post("/api/workflows", status_code=status.HTTP_201_CREATED)
def create_workflow(opportunity: Opportunity, db=Depends(get_db)):
    workflow_id = str(uuid.uuid4())
    instance = WorkflowInstance(workflow_id, opportunity)
    db_wf = WorkflowModel(workflow_id=instance.workflow_id, state=instance.state.name, context=instance.to_dict())
    db.add(db_wf)
    db.commit()
    return {"workflow_id": instance.workflow_id, "state": instance.state.name}

@app.get("/api/workflows/{workflow_id}")
def get_workflow(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"workflow_id": db_wf.workflow_id, "state": db_wf.state, "context": db_wf.context}

@app.post("/api/workflows/{workflow_id}/pitch")
async def submit_pitch(workflow_id: str, pitch: Pitch, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if db_wf.state != ProcurementState.OPPORTUNITY_DISCOVERED.name:
         raise HTTPException(status_code=409, detail="Invalid state")

    db_wf.state = ProcurementState.PITCH_SUBMITTED.name
    db.commit()
    return {"status": "pitch_submitted"}

@app.post("/api/workflows/{workflow_id}/pitch/evaluate")
async def evaluate_pitch(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf or db_wf.state != ProcurementState.PITCH_SUBMITTED.name:
         raise HTTPException(status_code=409, detail="Invalid state")

    # In production, load actual pitch instance, call pitch_evaluator.evaluate(pitch)
    db_wf.state = ProcurementState.PITCH_EVALUATED.name
    db.commit()
    return {"status": "pitch_evaluated"}

@app.post("/api/workflows/{workflow_id}/risk/assess")
async def assess_risk(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf or db_wf.state != ProcurementState.PITCH_EVALUATED.name:
         raise HTTPException(status_code=409, detail="Invalid state")

    # In production, call risk_detector.assess_risk(opportunity)
    db_wf.state = ProcurementState.RISK_ASSESSED.name
    db.commit()
    return {"status": "risk_assessed"}

@app.post("/api/workflows/{workflow_id}/human-review")
def submit_human_review(workflow_id: str, decision: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf or db_wf.state != ProcurementState.RISK_ASSESSED.name:
         raise HTTPException(status_code=409, detail="Invalid state")

    if decision == "APPROVE":
        db_wf.state = ProcurementState.STARTUP_SELECTED.name
    else:
        db_wf.state = ProcurementState.FAILED.name
    db.commit()
    return {"status": "human_review_complete"}

@app.post("/api/workflows/{workflow_id}/milestones/{milestone_id}/evaluate")
async def evaluate_milestone(workflow_id: str, milestone_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)

    # In production, call evaluator.evaluate(context)

    # Simple PASS logic for demonstration
    db_wf.state = ProcurementState.MILESTONE_EVALUATED.name
    db.commit()
    return {"status": "milestone_evaluated_pass"}

@app.post("/api/workflows/{workflow_id}/final-decision")
def final_decision(workflow_id: str, decision: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf or db_wf.state != ProcurementState.AWAITING_FINAL_DECISION.name:
         raise HTTPException(status_code=409, detail="Invalid state")

    db_wf.state = ProcurementState.HUMAN_FINAL_DECISION.name
    db.commit()
    return {"status": "final_decision_complete"}

@app.post("/api/workflows/{workflow_id}/startup-selection")
def select_startup(workflow_id: str, selection: StartupSelection, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf or db_wf.state != ProcurementState.STARTUP_SELECTED.name:
        # Note: Depending on logic, startup selection might be an input to the human-review or a subsequent step
        # Assuming for now STARTUP_SELECTED is the state.
        pass
    db_wf.state = ProcurementState.PROBLEM_ALLOCATED.name
    db.commit()
    return {"status": "startup_selected"}

@app.post("/api/workflows/{workflow_id}/pilot")
def create_pilot(workflow_id: str, pilot: Pilot, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    db_wf.state = ProcurementState.PILOT_CREATED.name
    db.commit()
    return {"status": "pilot_created"}

@app.post("/api/workflows/{workflow_id}/milestones")
def create_milestone(workflow_id: str, milestone: Milestone, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    db_wf.state = ProcurementState.MILESTONE_ACTIVE.name
    db.commit()
    return {"status": "milestone_created"}

@app.post("/api/workflows/{workflow_id}/milestones/{milestone_id}/evidence")
def submit_evidence(workflow_id: str, milestone_id: str, evidence: Evidence, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    db_wf.state = ProcurementState.EVIDENCE_SUBMITTED.name
    db.commit()
    return {"status": "evidence_submitted"}

@app.post("/api/workflows/{workflow_id}/scale-recommendation")
def submit_scale_recommendation(workflow_id: str, recommendation: ScaleRecommendation, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    db_wf.state = ProcurementState.SCALE_RECOMMENDATION.name
    db.commit()
    return {"status": "scale_recommendation_submitted"}
