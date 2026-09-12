from fastapi import FastAPI, HTTPException
from orchestrator.instance import WorkflowInstance
from orchestrator.state import ProcurementState
from orchestrator.persistence import SessionLocal, WorkflowModel
from orchestrator.api_models import StateUpdateRequest, HumanDecisionRequest
from adapters.pitch_evaluator import PitchEvaluatorAdapter

app = FastAPI()
db = SessionLocal()
pitch_evaluator = PitchEvaluatorAdapter("http://localhost:8000") # Assuming Pitch Evaluator runs here

@app.post("/api/workflow/start")
def start_workflow(opportunity_id: str):
    instance = WorkflowInstance(str(uuid.uuid4()), opportunity_id)
    # Persist
    db_wf = WorkflowModel(workflow_id=instance.workflow_id, state=instance.state.name, context={})
    db.add(db_wf)
    db.commit()
    return {"workflow_id": instance.workflow_id}

@app.post("/api/workflow/transition")
def transition(req: StateUpdateRequest):
    db_wf = db.query(WorkflowModel).filter(WorkflowModel.workflow_id == req.workflow_id).first()
    if not db_wf:
        raise HTTPException(status_code=404)

    # ... In a real implementation: reload instance from DB, call transition_to, save back ...
    # This is a minimal implementation for the checkpoint
    return {"status": "transitioned"}
