import unittest
from orchestrator.instance import WorkflowInstance
from orchestrator.state import ProcurementState
from shared.schemas.opportunity import Opportunity

class TestWorkflowOrchestrator(unittest.TestCase):
    def test_workflow_lifecycle(self):
        opp = Opportunity(opportunity_id="opp-1", title="Test", description="D", organization="O", status="active")
        instance = WorkflowInstance("wf-1", opp)
        # Test transition
        instance.transition_to(ProcurementState.PITCH_SUBMITTED, "submit", "pitch submitted")
        self.assertEqual(instance.state, ProcurementState.PITCH_SUBMITTED)
        # Test audit
        self.assertEqual(instance.history[0].event_type, "submit")

if __name__ == "__main__":
    unittest.main()
