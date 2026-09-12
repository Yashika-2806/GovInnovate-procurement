import unittest
from orchestrator.instance import WorkflowInstance, WorkflowEvent
from orchestrator.state import ProcurementState

class TestWorkflowOrchestrator(unittest.TestCase):
    def test_workflow_lifecycle(self):
        instance = WorkflowInstance("wf-1", "opp-1")
        # Test transition
        instance.transition_to(ProcurementState.PITCH_SUBMITTED, "submit", "pitch submitted")
        self.assertEqual(instance.state, ProcurementState.PITCH_SUBMITTED)
        # Test audit
        self.assertEqual(instance.history[0].event_type, "submit")

if __name__ == "__main__":
    unittest.main()
