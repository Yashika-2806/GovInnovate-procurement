from fastapi import FastAPI, HTTPException, status, Depends
from typing import List, Optional
from orchestrator.instance import WorkflowInstance
from orchestrator.state import ProcurementState
from orchestrator.persistence import SessionLocal, WorkflowModel
from shared.schemas.opportunity import Opportunity
from shared.schemas.pitch import Pitch
from shared.schemas.evaluation_result import EvaluationResult
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

@app.get("/health")
def health():
    return {"status": "healthy", "service": "orchestrator"}

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
