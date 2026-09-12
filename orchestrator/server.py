from fastapi import FastAPI, HTTPException, status
from orchestrator.instance import WorkflowInstance
from orchestrator.state import ProcurementState
from orchestrator.persistence import SessionLocal, WorkflowModel, AuditModel
from shared.schemas.opportunity import Opportunity
from shared.schemas.pitch import Pitch
from shared.schemas.audit_event import AuditEvent
from adapters.pitch_evaluator import PitchEvaluatorAdapter
from adapters.risk_detector import RiskDetectorAdapter
import uuid
import json

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

# Mock Ports
pitch_evaluator = PitchEvaluatorAdapter("http://localhost:8001")
risk_detector = RiskDetectorAdapter("http://localhost:8002")

@app.get("/health")
def health():
    return {"status": "healthy", "service": "orchestrator"}

@app.post("/api/workflows", status_code=status.HTTP_201_CREATED)
def create_workflow(opportunity: Opportunity):
    db = SessionLocal()
    workflow_id = str(uuid.uuid4())
    instance = WorkflowInstance(workflow_id, opportunity)
    db_wf = WorkflowModel(workflow_id=instance.workflow_id, state=instance.state.name, context=instance.to_dict())
    db.add(db_wf)
    db.commit()
    return {"workflow_id": instance.workflow_id, "state": instance.state.name}

@app.get("/api/workflows/{workflow_id}")
def get_workflow(workflow_id: str):
    db = SessionLocal()
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"workflow_id": db_wf.workflow_id, "state": db_wf.state, "context": db_wf.context}

@app.post("/api/workflows/{workflow_id}/pitch")
async def submit_pitch(workflow_id: str, pitch: Pitch):
    db = SessionLocal()
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Business validation: check state
    if db_wf.state != ProcurementState.OPPORTUNITY_DISCOVERED.name:
         raise HTTPException(status_code=409, detail="Invalid state for pitch submission")

    # In a real impl: orchestrator.transition_to(PITCH_SUBMITTED)
    db_wf.state = ProcurementState.PITCH_SUBMITTED.name
    db.commit()

    return {"status": "pitch_submitted"}

@app.post("/api/workflows/{workflow_id}/pitch/evaluate")
async def evaluate_pitch(workflow_id: str):
    db = SessionLocal()
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf or db_wf.state != ProcurementState.PITCH_SUBMITTED.name:
         raise HTTPException(status_code=409, detail="Invalid state")

    # Pitch Evaluation - adapter call
    # evaluation = await pitch_evaluator.evaluate(pitch)

    db_wf.state = ProcurementState.PITCH_EVALUATED.name
    db.commit()
    return {"status": "pitch_evaluated"}
