import unittest
from orchestrator.instance import WorkflowInstance
from orchestrator.state import ProcurementState
from shared.schemas.opportunity import Opportunity, OpportunityStatus

class TestE2EWorkflow(unittest.TestCase):
    def test_full_lifecycle(self):
        opp = Opportunity(
            opportunity_id="opp-1",
            title="AI Drone Inspection",
            description="Inspect oil pipelines.",
            organization="OilCo",
            status=OpportunityStatus.ACTIVE
        )
        instance = WorkflowInstance("wf-1", opp)

        # Test transition PITCH_SUBMITTED -> PITCH_EVALUATED
        instance.transition_to(ProcurementState.PITCH_SUBMITTED, "submit", "pitch submitted")
        instance.transition_to(ProcurementState.PITCH_EVALUATED, "evaluate", "pitch evaluated")

        self.assertEqual(instance.state, ProcurementState.PITCH_EVALUATED)
        self.assertEqual(len(instance.history), 2)

if __name__ == "__main__":
    unittest.main()
