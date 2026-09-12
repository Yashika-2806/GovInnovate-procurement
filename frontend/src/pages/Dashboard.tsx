import { Layout } from '../layouts/Layout';
import { useState, useEffect } from 'react';
import { workflowsApi, Workflow } from '../api/workflows';
import { WorkflowTimeline } from '../components/WorkflowTimeline';
import { StatusBadge } from '../components/StatusBadge';

const STAGE_DESCRIPTION: Record<string, string> = {
  OPPORTUNITY_DISCOVERED: "Initial opportunity identified.",
  PITCH_SUBMITTED: "Startup pitch proposal received.",
  PITCH_EVALUATED: "AI pitch evaluation completed.",
  RISK_ASSESSED: "AI risk assessment completed.",
  STARTUP_SELECTED: "Startup selected by committee.",
  FAILED: "Procurement process terminated.",
};

export const Dashboard = () => {
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>GovInnovate Dashboard</h1>
        <StatusBadge status={status} />
      </div>

      {!workflowId && (
        <button onClick={startWorkflow}>Start New Procurement Workflow</button>
      )}

      {workflow && (
        <div style={{ marginTop: '20px' }}>
          <h2>Workflow: {workflow.workflow_id}</h2>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
            <WorkflowTimeline workflow={workflow} />

            <div style={{ border: '1px solid #ddd', padding: '20px', borderRadius: '8px' }}>
              <h3>Current Stage: {workflow.state.replace('_', ' ')}</h3>
              <p>{STAGE_DESCRIPTION[workflow.state] || "Stage processing."}</p>

              <div style={{ marginTop: '20px' }}>
                <h4>Actions</h4>
                <div style={{ display: 'flex', gap: '10px' }}>
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

                {workflow.state === 'RISK_ASSESSED' && (
                   <button onClick={() => handleAction(() => workflowsApi.submitHumanReview(workflow.workflow_id, "APPROVE"))}>
                      Approve Startup
                   </button>
                )}
                </div>
              </div>

              <div style={{ marginTop: '20px', fontSize: '0.8em', color: '#666' }}>
                <h4>Backend Blocked Functions</h4>
                <ul>
                    <li>Startup Selection</li>
                    <li>Allocation</li>
                    <li>Pilot Stages</li>
                    <li>Milestone Management</li>
                    <li>Evidence/Audit trails</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};
