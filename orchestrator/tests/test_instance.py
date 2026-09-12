import unittest
from orchestrator.instance import WorkflowInstance, WorkflowEvent
from orchestrator.state import ProcurementState

class TestWorkflowInstance(unittest.TestCase):
    def test_initial_state(self):
        instance = WorkflowInstance("test_1")
        self.assertEqual(instance.state, ProcurementState.OPPORTUNITY_DISCOVERED)

    def test_valid_transition(self):
        instance = WorkflowInstance("test_1")
        event = WorkflowEvent("submit_pitch", {"data": "test"})
        instance.transition_to(ProcurementState.PITCH_SUBMITTED, event)
        self.assertEqual(instance.state, ProcurementState.PITCH_SUBMITTED)
        self.assertEqual(len(instance.history), 1)

if __name__ == "__main__":
    unittest.main()
