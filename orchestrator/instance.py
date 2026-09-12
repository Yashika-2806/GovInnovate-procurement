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
        self.pitch_evaluation: Optional[PitchEvaluation] = None
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
        self.startup_selection: Optional[StartupSelection] = None
        self.allocation: Optional[Dict[str, Any]] = None

    @classmethod
    def from_db(cls, db_model: Any, opportunity: Opportunity):
        instance = cls(db_model.workflow_id, opportunity)
        instance.state = ProcurementState[db_model.state]
        context = db_model.context or {}
        instance.startup_id = context.get('startup_id')
        instance.pitch_id = context.get('pitch_id')
        instance.startup_selection = StartupSelection(**context['startup_selection']) if context.get('startup_selection') else None
        instance.pilot = Pilot(**context['pilot']) if context.get('pilot') else None
        instance.milestones = {k: Milestone(**v) for k, v in context.get('milestones', {}).items()}
        instance.evidence = {
            k: [Evidence(**e) for e in ev]
            for k, ev in context.get('evidence', {}).items()
        }
        instance.remediations = {k: Remediation(**v) for k, v in context.get('remediations', {}).items()}
        instance.performance = PerformanceProfile(**context['performance']) if context.get('performance') else None
        instance.scale_recommendation = ScaleRecommendation(**context['scale_recommendation']) if context.get('scale_recommendation') else None
        instance.history = [AuditEvent(**a) for a in context.get('history', [])]
        instance.evaluation_result = EvaluationResult(**context['evaluation_result']) if context.get('evaluation_result') else None
        return instance

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

    def add_milestone(self, milestone: Milestone):
        self.milestones[milestone.milestone_id] = milestone
        self.transition_to(ProcurementState.MILESTONE_ACTIVE, "MILESTONE_CREATED", f"Milestone {milestone.milestone_id} created")
        return milestone.milestone_id

    def add_evidence(self, evidence: Evidence):
        if evidence.milestone_id not in self.evidence:
            self.evidence[evidence.milestone_id] = []
        self.evidence[evidence.milestone_id].append(evidence)
        self.transition_to(ProcurementState.EVIDENCE_SUBMITTED, "EVIDENCE_SUBMITTED", f"Evidence {evidence.evidence_id} submitted for {evidence.milestone_id}")

    def select_startup(self, selection: StartupSelection):
        self.startup_id = selection.startup_id
        self.startup_selection = selection
        self.transition_to(ProcurementState.STARTUP_SELECTED, "STARTUP_SELECTED", f"Startup {selection.startup_id} selected")

    def create_pilot(self, pilot: Pilot):
        self.pilot = pilot
        self.transition_to(ProcurementState.PILOT_CREATED, "PILOT_CREATED", f"Pilot {pilot.pilot_id} created")

    def evaluate_milestone(self, milestone_id: str):
        if milestone_id not in self.milestones:
            raise ValueError(f"Milestone {milestone_id} not found")
        ev_list = self.evidence.get(milestone_id, [])
        # Real evaluation: inspect evidence status
        if not ev_list:
            result = "REQUIRES_VERIFICATION"
            reason = f"No evidence submitted for milestone {milestone_id}"
        elif any(getattr(e, 'status', '') == 'rejected' for e in ev_list):
            result = "FAIL"
            reason = f"Rejected evidence for milestone {milestone_id}"
        elif all(getattr(e, 'status', '') == 'verified' for e in ev_list):
            result = "PASS"
            reason = f"All evidence verified for milestone {milestone_id}"
        elif any(getattr(e, 'status', '') == 'verified' for e in ev_list):
            # Partial verification with some verified
            verified_count = sum(1 for e in ev_list if getattr(e, 'status', '') == 'verified')
            if verified_count >= len(ev_list) / 2:
                result = "PASS"
                reason = f"Sufficient verified evidence for milestone {milestone_id}"
            else:
                result = "REQUIRES_VERIFICATION"
                reason = f"Insufficient verified evidence for milestone {milestone_id}"
        else:
            # All submitted but none verified
            result = "REQUIRES_VERIFICATION"
            reason = f"Evidence submitted but not verified for milestone {milestone_id}"

        milestone = self.milestones[milestone_id]
        milestone.status = "completed" if result == "PASS" else ("failed" if result == "FAIL" else "pending_verification")
        # State transition logic: from EVIDENCE_SUBMITTED to MILESTONE_EVALUATED
        # If result is FAIL, allow remediation path (already allowed by transition rules from MILESTONE_EVALUATED to REMEDIATION)
        self.transition_to(ProcurementState.MILESTONE_EVALUATED, "MILESTONE_EVALUATED", f"Milestone {milestone_id} evaluated: {result} — {reason}")
        return result

    def submit_remediation(self, remediation: Remediation):
        self.remediations[remediation.milestone_id] = remediation
        self.transition_to(ProcurementState.REMEDIATION, "REMEDIATION_SUBMITTED", f"Remediation submitted for {remediation.milestone_id}")

    def final_evaluation(self, evaluation: EvaluationResult):
        self.evaluation_result = evaluation
        self.transition_to(ProcurementState.FINAL_EVALUATION, "FINAL_EVALUATION", "Final evaluation completed")

    def final_decision(self, decision: str):
        # Must come from AWAITING_FINAL_DECISION
        if self.state != ProcurementState.AWAITING_FINAL_DECISION:
            raise ValueError("Final decision allowed only from AWAITING_FINAL_DECISION")
        self.transition_to(ProcurementState.HUMAN_FINAL_DECISION, "FINAL_DECISION", f"Final decision: {decision}")

    def submit_scale_recommendation(self, recommendation: ScaleRecommendation):
        self.scale_recommendation = recommendation
        self.transition_to(ProcurementState.SCALE_RECOMMENDATION, "SCALE_RECOMMENDATION", f"Scale recommendation: {recommendation.recommendation}")

    def update_performance(self, performance: PerformanceProfile):
        self.performance = performance
        self.transition_to(ProcurementState.PERFORMANCE_UPDATED, "PERFORMANCE_UPDATED", "Performance profile updated")

    def _validate_transition(self, new_state: ProcurementState):
        allowed = {
            ProcurementState.OPPORTUNITY_DISCOVERED: [ProcurementState.PITCH_SUBMITTED],
            ProcurementState.PITCH_SUBMITTED: [ProcurementState.PITCH_EVALUATED],
            ProcurementState.PITCH_EVALUATED: [ProcurementState.RISK_ASSESSED],
            ProcurementState.RISK_ASSESSED: [ProcurementState.STARTUP_SELECTED, ProcurementState.AWAITING_HUMAN_REVIEW, ProcurementState.FAILED],
            ProcurementState.AWAITING_HUMAN_REVIEW: [ProcurementState.STARTUP_SELECTED, ProcurementState.FAILED],
            ProcurementState.STARTUP_SELECTED: [ProcurementState.PROBLEM_ALLOCATED, ProcurementState.PILOT_CREATED],
            ProcurementState.PROBLEM_ALLOCATED: [ProcurementState.PILOT_CREATED],
            ProcurementState.PILOT_CREATED: [ProcurementState.MILESTONE_ACTIVE, ProcurementState.MILESTONE_EVALUATED],
            ProcurementState.MILESTONE_ACTIVE: [ProcurementState.EVIDENCE_SUBMITTED, ProcurementState.REMEDIATION],
            ProcurementState.EVIDENCE_SUBMITTED: [ProcurementState.MILESTONE_EVALUATED, ProcurementState.REMEDIATION, ProcurementState.SCALE_RECOMMENDATION],
            ProcurementState.MILESTONE_EVALUATED: [ProcurementState.NEXT_MILESTONE, ProcurementState.SCALE_RECOMMENDATION, ProcurementState.REMEDIATION, ProcurementState.AWAITING_FINAL_DECISION, ProcurementState.PERFORMANCE_UPDATED],
            ProcurementState.REMEDIATION: [ProcurementState.EVIDENCE_SUBMITTED],
            ProcurementState.NEXT_MILESTONE: [ProcurementState.MILESTONE_ACTIVE, ProcurementState.EVIDENCE_SUBMITTED],
            ProcurementState.FINAL_EVALUATION: [ProcurementState.PERFORMANCE_UPDATED],
            ProcurementState.PERFORMANCE_UPDATED: [ProcurementState.SCALE_RECOMMENDATION],
            ProcurementState.SCALE_RECOMMENDATION: [ProcurementState.AWAITING_FINAL_DECISION],
            ProcurementState.AWAITING_FINAL_DECISION: [ProcurementState.HUMAN_FINAL_DECISION],
        }
        if new_state not in allowed.get(self.state, []):
            raise ValueError(f"Invalid transition from {self.state.name} to {new_state.name}")

    def to_dict(self):
        return {
            "workflow_id": self.workflow_id,
            "opportunity_id": self.opportunity.id,
            "opportunity": self.opportunity.model_dump() if self.opportunity else None,
            "state": self.state.name,
            "startup_id": self.startup_id,
            "pitch_id": self.pitch_id,
            "startup_selection": self.startup_selection.model_dump() if self.startup_selection else None,
            "pilot": self.pilot.model_dump() if self.pilot else None,
            "milestones": {k: v.model_dump() for k, v in self.milestones.items()},
            "evidence": {k: [e.model_dump() for e in ev] for k, ev in self.evidence.items()},
            "remediations": {k: v.model_dump() for k, v in self.remediations.items()},
            "performance": self.performance.model_dump() if self.performance else None,
            "scale_recommendation": self.scale_recommendation.model_dump() if self.scale_recommendation else None,
            "evaluation_result": self.evaluation_result.model_dump() if self.evaluation_result else None,
            "history": [
                {
                    **a.model_dump(),
                    "timestamp": a.timestamp.isoformat() if hasattr(a.timestamp, 'isoformat') else str(a.timestamp)
                } for a in self.history
            ]
        }
