import { Layout } from './layouts/Layout';
import { useState, useEffect } from 'react';
import { workflowsApi, Workflow } from './api/workflows';

function App() {
  const [status, setStatus] = useState<string>('Connecting...');
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [workflow, setWorkflow] = useState<Workflow | null>(null);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      await workflowsApi.getHealth();
      setStatus('Backend Online');
    } catch {
      setStatus('Backend Offline');
    }
  };

  const refreshWorkflow = async (id: string) => {
    try {
      const res = await workflowsApi.get(id);
      setWorkflow(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const startWorkflow = async () => {
    const opp = {
      opportunity_id: `opp-${Math.random().toString(36).substring(7)}`,
      title: "Test AI Drone",
      description: "Test description",
      organization: "GovTest",
      status: "active"
    };
    const res = await workflowsApi.create(opp);
    setWorkflowId(res.data.workflow_id);
    refreshWorkflow(res.data.workflow_id);
  };

  const handleAction = async (action: () => Promise<any>) => {
    await action();
    if (workflowId) {
        refreshWorkflow(workflowId);
    }
  };

  return (
    <Layout>
      <h1>Dashboard</h1>
      <p>System Status: <strong>{status}</strong></p>

      {!workflowId && (
        <button onClick={startWorkflow}>Start Workflow</button>
      )}

      {workflow && (
        <div>
          <h2>Workflow: {workflow.workflow_id}</h2>
          <p>State: <strong>{workflow.state}</strong></p>

          <div style={{ marginTop: '10px' }}>
            {workflow.state === 'OPPORTUNITY_DISCOVERED' && (
              <button onClick={() => handleAction(() => workflowsApi.submitPitch(workflow.workflow_id, {pitch_id: 'p1', startup_id: 's1', opportunity_id: 'o1'}))}>
                Submit Pitch
              </button>
            )}

            {workflow.state === 'PITCH_SUBMITTED' && (
              <button onClick={() => handleAction(() => workflowsApi.evaluatePitch(workflow.workflow_id))}>
                Evaluate Pitch
              </button>
            )}

            {workflow.state === 'PITCH_EVALUATED' && (
              <button onClick={() => handleAction(() => workflowsApi.assessRisk(workflow.workflow_id))}>
                Assess Risk
              </button>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}

export default App;
