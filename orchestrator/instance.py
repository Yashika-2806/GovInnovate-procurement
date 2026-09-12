from typing import Dict, Any, List, Optional
from .state import ProcurementState
from shared.schemas.audit_event import AuditEvent
import uuid
from datetime import datetime

class WorkflowEvent:
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data

class WorkflowInstance:
    def __init__(self, instance_id: str, opportunity_id: str):
        self.workflow_id = instance_id
        self.opportunity_id = opportunity_id
        self.startup_id: Optional[str] = None
        self.state = ProcurementState.OPPORTUNITY_DISCOVERED
        self.context: Dict[str, Any] = {}
        self.history: List[AuditEvent] = []

    def transition_to(self, new_state: ProcurementState, event_type: str, reason: str, actor: Optional[str] = None):
        self._validate_transition(new_state)
        old_state = self.state
        self.state = new_state

        audit = AuditEvent(
            audit_event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            workflow_id=self.workflow_id,
            entity_id=self.opportunity_id,
            event_type=event_type,
            reason=reason,
            relevant_agent=actor,
            success=True,
            previous_state=old_state.name, # Need to add previous_state to AuditEvent schema
            new_state=new_state.name
        )
        self.history.append(audit)

    def _validate_transition(self, new_state: ProcurementState):
        # Simplistic validation: No looping, must progress generally
        # In full production, this would be a matrix table
        if new_state == self.state:
            raise ValueError(f"Invalid transition: {self.state} to {new_state}")

    def add_audit_event(self, event_type: str, data: Dict[str, Any]):
        # Implementation for arbitrary events
        pass
