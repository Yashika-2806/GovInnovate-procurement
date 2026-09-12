from typing import Dict, Any, List
from .state import ProcurementState

class WorkflowEvent:
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data

class WorkflowInstance:
    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.state = ProcurementState.OPPORTUNITY_DISCOVERED
        self.context: Dict[str, Any] = {}
        self.history: List[WorkflowEvent] = []

    def transition_to(self, new_state: ProcurementState, event: WorkflowEvent):
        # Deterministic validation here
        self._validate_transition(new_state)
        self.state = new_state
        self.history.append(event)

    def _validate_transition(self, new_state: ProcurementState):
        # Implementation of transition rules
        pass

    def add_audit_event(self, event_type: str, data: Dict[str, Any]):
        self.history.append(WorkflowEvent(event_type, data))
