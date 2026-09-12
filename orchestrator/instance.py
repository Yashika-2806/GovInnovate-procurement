from typing import Dict, Any, List, Optional
from orchestrator.state import ProcurementState
from shared.schemas.audit_event import AuditEvent
from shared.schemas.opportunity import Opportunity
from shared.schemas.pitch import Pitch
from shared.schemas.pitch_evaluation import PitchEvaluation
from shared.schemas.risk_assessment import RiskAssessment
from shared.schemas.evaluation_result import EvaluationResult
import uuid
from datetime import datetime

from shared.schemas.startup_selection import StartupSelection
from shared.schemas.pilot import Pilot
from shared.schemas.milestone import Milestone
from shared.schemas.evidence import Evidence
from shared.schemas.remediation import Remediation
from shared.schemas.performance import PerformanceProfile
from shared.schemas.scale_recommendation import ScaleRecommendation

class WorkflowInstance:
    def __init__(self, workflow_id: str, opportunity: Opportunity):
        self.workflow_id = workflow_id
        self.opportunity = opportunity
        self.startup_id: Optional[str] = None
        self.pitch_id: Optional[str] = None
        self.evaluation: Optional[PitchEvaluation] = None
        self.risk_assessment: Optional[RiskAssessment] = None
        self.evaluation_result: Optional[EvaluationResult] = None
        self.pilot: Optional[Pilot] = None
        self.milestones: Dict[str, Milestone] = {}
        self.evidence: Dict[str, List[Evidence]] = {}
        self.remediations: Dict[str, Remediation] = {}
        self.performance: Optional[PerformanceProfile] = None
        self.scale_recommendation: Optional[ScaleRecommendation] = None
        self.state = ProcurementState.OPPORTUNITY_DISCOVERED
        self.history: List[AuditEvent] = []

    def transition_to(self, new_state: ProcurementState, event_type: str, reason: str, actor: Optional[str] = None):
        self._validate_transition(new_state)
        old_state = self.state
        self.state = new_state

        audit = AuditEvent(
            audit_event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            workflow_id=self.workflow_id,
            entity_id=self.opportunity.id,
            event_type=event_type,
            reason=reason,
            relevant_agent=actor,
            success=True,
            previous_state=old_state.name,
            new_state=new_state.name
        )
        self.history.append(audit)

    def _validate_transition(self, new_state: ProcurementState):
        if new_state == self.state:
            raise ValueError(f"Invalid transition: {self.state} to {new_state}")

    def to_dict(self):
        return {
            "workflow_id": self.workflow_id,
            "opportunity_id": self.opportunity.id,
            "state": self.state.name,
            "startup_id": self.startup_id,
            "pilot": self.pilot.dict() if self.pilot else None,
            "milestones": {k: v.dict() for k, v in self.milestones.items()},
        }
