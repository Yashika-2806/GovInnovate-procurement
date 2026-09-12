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
  AWAITING_HUMAN_REVIEW: "Awaiting human review of risk assessment.",
  STARTUP_SELECTED: "Startup selected by committee.",
  AWAITING_FINAL_DECISION: "Awaiting final human procurement decision.",
  MILESTONE_EVALUATED: "Milestone evaluation completed.",
  FAILED: "Procurement process terminated.",
};

export const Dashboard = ({ onSelectWorkflow }: { onSelectWorkflow?: (id: string) => void }) => {
  const [status, setStatus] = useState<string>('Connecting...');
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [showFinalDecision, setShowFinalDecision] = useState(false);

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

  const startWorkflow = async (opp: any) => {
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
        <div style={{ padding: '20px', border: '1px solid #ccc' }}>
          <h3>Create New Opportunity</h3>
          <button onClick={() => startWorkflow({title: "Drone Monitoring", description: "Efficient drone surveillance", organization: "GovTest", status: "active"})}>Start Workflow</button>
        {workflowId && onSelectWorkflow && (
          <button onClick={() => onSelectWorkflow(workflowId)} style={{ marginLeft: '10px' }}>
            View Full Workflow Detail
          </button>
        )}
        </div>
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
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
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

                {workflow.state === 'AWAITING_FINAL_DECISION' && (
                   <button onClick={() => setShowFinalDecision(true)}>
                      Make Final Decision
                   </button>
                )}
                </div>

                {showFinalDecision && (
                  <div style={{ padding: '10px', border: '1px solid black', marginTop: '10px' }}>
                      <h4>Make Final Decision</h4>
                      <button onClick={() => handleAction(() => workflowsApi.submitFinalDecision(workflow.workflow_id, "APPROVE"))}>Approve Scale</button>
                      <button onClick={() => setShowFinalDecision(false)}>Cancel</button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};
