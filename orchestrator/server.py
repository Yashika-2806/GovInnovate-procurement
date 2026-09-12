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

pitch_evaluator = PitchEvaluatorAdapter("http://localhost:8001")
risk_detector = RiskDetectorAdapter("http://localhost:8002")
evaluator = EvaluatorAdapter("http://localhost:8003")

@app.get("/api/workflows/{workflow_id}/milestones", response_model=list)
def get_milestones(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or db_wf.context.get('opportunity_id'))
    instance = WorkflowInstance.from_db(db_wf, opp)
    return [m.model_dump() for m in instance.milestones.values()]

@app.get("/api/workflows/{workflow_id}/milestones/{milestone_id}", response_model=dict)
def get_milestone(workflow_id: str, milestone_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    if milestone_id not in instance.milestones:
        raise HTTPException(status_code=404)
    return instance.milestones[milestone_id].model_dump()

@app.get("/api/workflows/{workflow_id}/milestones/{milestone_id}/evidence", response_model=list)
def get_evidence(workflow_id: str, milestone_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    return [e.model_dump() for e in instance.evidence.get(milestone_id, [])]

@app.post("/api/workflows/{workflow_id}/milestones/{milestone_id}/remediation", response_model=dict)
def submit_remediation(workflow_id: str, milestone_id: str, remediation: Remediation, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    remediation.milestone_id = milestone_id
    try:
        instance.submit_remediation(remediation)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    # Audit to persistence if needed
    return {"status": "remediation_submitted", "milestone_id": milestone_id, "remediation_id": remediation.remediation_id}

@app.post("/api/workflows/{workflow_id}/final-evaluation", response_model=dict)
def final_evaluation(workflow_id: str, evaluation: EvaluationResult, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    try:
        instance.final_evaluation(evaluation)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "final_evaluation_complete"}

@app.get("/api/workflows/{workflow_id}/performance", response_model=dict)
def get_performance(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    return db_wf.context.get('performance') or {}

@app.post("/api/workflows/{workflow_id}/performance", response_model=dict)
def post_performance(workflow_id: str, performance: PerformanceProfile, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    try:
        instance.update_performance(performance)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "performance_updated"}

@app.get("/api/workflows/{workflow_id}/audit", response_model=list)
def get_audit(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    return db_wf.context.get('history', [])

@app.post("/api/workflows", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_workflow(opportunity: Opportunity, db=Depends(get_db)):
    workflow_id = str(uuid.uuid4())
    instance = WorkflowInstance(workflow_id, opportunity)
    db_wf = WorkflowModel(workflow_id=instance.workflow_id, state=instance.state.name, context=instance.to_dict())
    db.add(db_wf)
    db.commit()
    return {"workflow_id": instance.workflow_id, "state": instance.state.name}

@app.get("/api/workflows/{workflow_id}", response_model=dict)
def get_workflow(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"workflow_id": db_wf.workflow_id, "state": db_wf.state, "context": db_wf.context}

@app.post("/api/workflows/{workflow_id}/pitch", response_model=dict)
async def submit_pitch(workflow_id: str, pitch: Pitch, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    instance.pitch_id = pitch.id
    try:
        instance.transition_to(ProcurementState.PITCH_SUBMITTED, "PITCH_SUBMITTED", "Pitch submitted via API")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "pitch_submitted"}

@app.post("/api/workflows/{workflow_id}/pitch/evaluate", response_model=dict)
async def evaluate_pitch(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    try:
        instance.transition_to(ProcurementState.PITCH_EVALUATED, "PITCH_EVALUATED", "Pitch evaluated")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "pitch_evaluated"}

@app.post("/api/workflows/{workflow_id}/risk/assess", response_model=dict)
async def assess_risk(workflow_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    try:
        instance.transition_to(ProcurementState.RISK_ASSESSED, "RISK_ASSESSED", "Risk assessment completed")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "risk_assessed"}

@app.post("/api/workflows/{workflow_id}/human-review", response_model=dict)
def submit_human_review(workflow_id: str, decision: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    # Human gate: must be from RISK_ASSESSED; decision APPROVE -> STARTUP_SELECTED or AWAITING_HUMAN_REVIEW then selection; REJECT -> FAILED
    if decision == "APPROVE":
        # After approval, go to AWAITING_HUMAN_REVIEW if not yet selected; but per lifecycle, after risk assessed, human review approves startup selection path
        new_state = ProcurementState.AWAITING_HUMAN_REVIEW
    elif decision == "REJECT":
        new_state = ProcurementState.FAILED
    else:
        raise HTTPException(status_code=400, detail="Decision must be APPROVE or REJECT")
    try:
        instance.transition_to(new_state, "HUMAN_REVIEW", f"Human review decision: {decision}")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "human_review_complete", "decision": decision, "state": instance.state.name}

@app.post("/api/workflows/{workflow_id}/milestones/{milestone_id}/evaluate", response_model=dict)
async def evaluate_milestone(workflow_id: str, milestone_id: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    try:
        result = instance.evaluate_milestone(milestone_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": f"milestone_evaluated_{result.lower()}", "result": result, "milestone_id": milestone_id}

@app.post("/api/workflows/{workflow_id}/final-decision", response_model=dict)
def final_decision(workflow_id: str, decision: str, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    try:
        instance.final_decision(decision)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "final_decision_complete", "decision": decision}

@app.post("/api/workflows/{workflow_id}/startup-selection", response_model=dict)
def select_startup(workflow_id: str, selection: StartupSelection, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    try:
        instance.select_startup(selection)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "startup_selected", "startup_id": selection.startup_id}

@app.post("/api/workflows/{workflow_id}/pilot", response_model=dict)
def create_pilot(workflow_id: str, pilot: Pilot, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    try:
        instance.create_pilot(pilot)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "pilot_created"}

@app.post("/api/workflows/{workflow_id}/milestones", response_model=dict)
def create_milestone(workflow_id: str, milestone: Milestone, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    try:
        instance.add_milestone(milestone)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "milestone_created", "milestone_id": milestone.milestone_id}

@app.post("/api/workflows/{workflow_id}/milestones/{milestone_id}/evidence", response_model=dict)
def submit_evidence(workflow_id: str, milestone_id: str, evidence: Evidence, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    evidence.milestone_id = milestone_id
    try:
        instance.add_evidence(evidence)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "evidence_submitted", "evidence_id": evidence.evidence_id}

@app.post("/api/workflows/{workflow_id}/scale-recommendation", response_model=dict)
def submit_scale_recommendation(workflow_id: str, recommendation: ScaleRecommendation, db=Depends(get_db)):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)
    opp = Opportunity(**db_wf.context.get('opportunity') or {})
    instance = WorkflowInstance.from_db(db_wf, opp)
    try:
        instance.submit_scale_recommendation(recommendation)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    db_wf.state = instance.state.name
    db_wf.context = instance.to_dict()
    db.commit()
    return {"status": "scale_recommendation_submitted"}
