import unittest
from orchestrator.instance import WorkflowInstance
from orchestrator.state import ProcurementState
from shared.schemas.opportunity import Opportunity

class TestWorkflowInstance(unittest.TestCase):
    def test_initial_state(self):
        opp = Opportunity(opportunity_id="test_1", title="Test", description="D", organization="O", status="active")
        instance = WorkflowInstance("test_1", opp)
        self.assertEqual(instance.state, ProcurementState.OPPORTUNITY_DISCOVERED)

    def test_valid_transition(self):
        opp = Opportunity(opportunity_id="test_1", title="Test", description="D", organization="O", status="active")
        instance = WorkflowInstance("test_1", opp)
        instance.transition_to(ProcurementState.PITCH_SUBMITTED, "submit", "pitch submitted")
        self.assertEqual(instance.state, ProcurementState.PITCH_SUBMITTED)
        self.assertEqual(len(instance.history), 1)

if __name__ == "__main__":
    unittest.main()
