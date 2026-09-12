from fastapi import FastAPI, HTTPException
from orchestrator.instance import WorkflowInstance
from orchestrator.state import ProcurementState
from orchestrator.persistence import SessionLocal, WorkflowModel
from shared.schemas.opportunity import Opportunity
from shared.schemas.pitch import Pitch
from adapters.pitch_evaluator import PitchEvaluatorAdapter
from adapters.risk_detector import RiskDetectorAdapter
import uuid

app = FastAPI()
db = SessionLocal()
pitch_evaluator = PitchEvaluatorAdapter("http://localhost:8001") # Assuming ports: PS:8000, Pitch:8001, Risk:8002, Eval:8003
risk_detector = RiskDetectorAdapter("http://localhost:8002")

@app.post("/api/workflow/start")
def start_workflow(opportunity: Opportunity):
    workflow_id = str(uuid.uuid4())
    instance = WorkflowInstance(workflow_id, opportunity)
    db_wf = WorkflowModel(workflow_id=instance.workflow_id, state=instance.state.name, context=instance.to_dict())
    db.add(db_wf)
    db.commit()
    return {"workflow_id": instance.workflow_id}

@app.post("/api/workflow/submit_pitch")
async def submit_pitch(workflow_id: str, pitch: Pitch):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)

    # Pitch Evaluation
    evaluation = await pitch_evaluator.evaluate(pitch)

    # Risk Assessment
    # Assuming opportunity lookup from context or another DB call
    # risk = await risk_detector.assess_risk(opportunity)

    return {"status": "pitch_evaluated", "evaluation": evaluation}
