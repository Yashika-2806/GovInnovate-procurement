import { useState, useEffect } from 'react';
import { Layout } from '../layouts/Layout';
import { workflowsApi } from '../api/workflows';
import { StatusBadge } from '../components/StatusBadge';

export const WorkflowDetail = ({ workflowId }: { workflowId: string }) => {
  const [workflow, setWorkflow] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    refresh();
  }, [workflowId]);

  const refresh = async () => {
    setLoading(true);
    try {
      const res = await workflowsApi.get(workflowId);
      setWorkflow(res.data);
      setError(null);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to load workflow');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !workflow) return <Layout><p>Loading workflow...</p></Layout>;
  if (error) return <Layout><p>Error: {error}</p><button onClick={refresh}>Retry</button></Layout>;
  if (!workflow) return <Layout><p>No workflow found.</p></Layout>;

  const ctx = workflow.context || {};
  const stateName = workflow.state || ctx.state || 'Unknown';

  return (
    <Layout>
      <h1>Workflow: {workflow.workflow_id}</h1>
      <StatusBadge status={stateName} />
      <p>State: <strong>{stateName.replace(/_/g, ' ')}</strong></p>

      <section>
        <h2>Opportunity</h2>
        {ctx.opportunity ? (
          <div>
            <p><strong>{ctx.opportunity.title}</strong></p>
            <p>{ctx.opportunity.description}</p>
            <p>Organization: {ctx.opportunity.organization}</p>
          </div>
        ) : <p>No opportunity data.</p>}
      </section>

      <section>
        <h2>Pitch</h2>
        {ctx.pitch_id ? <p>Pitch ID: {ctx.pitch_id}</p> : <p>No pitch submitted.</p>}
      </section>

      <section>
        <h2>Pitch Evaluation</h2>
        <p>State reflects pitch evaluation status.</p>
      </section>

      <section>
        <h2>Risk Assessment</h2>
        <p>State: {stateName}</p>
      </section>

      <section>
        <h2>Startup Selection</h2>
        {ctx.startup_selection ? (
          <div>
            <p>Startup: {ctx.startup_selection.startup_id}</p>
            <p>Reason: {ctx.startup_selection.selection_reason}</p>
          </div>
        ) : <p>No startup selected.</p>}
      </section>

      <section>
        <h2>Allocation / Pilot</h2>
        {ctx.pilot ? (
          <div>
            <p>Pilot: {ctx.pilot.pilot_id}</p>
            <p>Description: {ctx.pilot.description}</p>
          </div>
        ) : <p>No pilot created.</p>}
      </section>

      <section>
        <h2>Milestones</h2>
        {ctx.milestones && Object.keys(ctx.milestones).length > 0 ? (
          Object.entries(ctx.milestones).map(([k, v]: [string, any]) => (
            <div key={k} style={{ border: '1px solid #ccc', padding: '8px', marginBottom: '8px' }}>
              <p><strong>{v.milestone_id}</strong> — {v.description}</p>
              <p>Status: {v.status}</p>
              <p>Due: {v.due_date || 'Not set'}</p>
            </div>
          ))
        ) : <p>No milestones.</p>}
      </section>

      <section>
        <h2>Evidence</h2>
        {ctx.evidence && Object.keys(ctx.evidence).length > 0 ? (
          Object.entries(ctx.evidence || {}).map(([milestoneId, evList]: [string, any]) => (
            <div key={milestoneId}>
              <h4>Milestone: {milestoneId}</h4>
              {(Array.isArray(evList) ? evList : []).map((e: any, i: number) => (
                <div key={i} style={{ padding: '6px', borderLeft: '3px solid #ccc' }}>
                  <p><strong>{e.evidence_id}</strong> — {e.description}</p>
                  <p>Link: <a href={e.link} target="_blank" rel="noopener noreferrer">{e.link}</a></p>
                  <p>
                    Verification:{' '}
                    <span style={{
                      color: e.status === 'verified' ? 'green' : e.status === 'rejected' ? 'red' : 'orange',
                      fontWeight: 'bold'
                    }}>
                      {e.status || 'UNKNOWN'}
                    </span>
                  </p>
                </div>
              ))}
            </div>
          ))
        ) : <p>No evidence submitted.</p>}
      </section>

      <section>
        <h2>Milestone Evaluation</h2>
        {ctx.milestones && Object.values(ctx.milestones).some((m: any) => m.status === 'completed' || m.status === 'failed' || m.status === 'pending_verification') ? (
          <p>Milestone results: {Object.values(ctx.milestones).map((m: any) => `${m.milestone_id}=${m.status}`).join(', ')}</p>
        ) : <p>Pending evaluation.</p>}
      </section>

      <section>
        <h2>Remediation</h2>
        {ctx.remediations && Object.keys(ctx.remediations).length > 0 ? (
          Object.entries(ctx.remediations).map(([k, v]: [string, any]) => (
            <div key={k}>
              <p>Remediation for milestone {v.milestone_id}: {v.action} (status: {v.status || 'submitted'})</p>
            </div>
          ))
        ) : <p>No remediations.</p>}
      </section>

      <section>
        <h2>Final Evaluation</h2>
        {ctx.evaluation_result ? (
          <div>
            <p><strong>System/AI Evaluation:</strong> {ctx.evaluation_result.status || 'Pending'}</p>
            <p>Explanation: {ctx.evaluation_result.explanation}</p>
            <p>Confidence: {ctx.evaluation_result.confidence}</p>
            <p>Recommendation: {ctx.evaluation_result.recommendation}</p>
            <p style={{ fontWeight: 'bold', color: 'blue' }}>This is an AI evaluation. Human final decision is separate.</p>
          </div>
        ) : <p>No final evaluation submitted.</p>}
      </section>

      <section>
        <h2>Performance</h2>
        {ctx.performance ? (
          <div>
            <p>Startup: {ctx.performance.startup_id}</p>
            <p>Summary: {ctx.performance.summary}</p>
            <pre>{JSON.stringify(ctx.performance.metrics || {}, null, 2)}</pre>
          </div>
        ) : <p>No performance profile.</p>}
      </section>

      <section>
        <h2>Scale Recommendation</h2>
        {ctx.scale_recommendation ? (
          <div style={{ border: '2px solid #0066cc', padding: '12px', borderRadius: '6px' }}>
            <h3 style={{ color: '#0066cc', marginTop: 0 }}>RECOMMENDATION (NOT APPROVAL)</h3>
            <p><strong>Recommendation:</strong> {ctx.scale_recommendation.recommendation}</p>
            <p><strong>Rationale:</strong> {ctx.scale_recommendation.rationale}</p>
            <p><strong>Confidence:</strong> {ctx.scale_recommendation.confidence_score}</p>
            <p>Supporting factors: {ctx.scale_recommendation.supporting_factors || 'Not specified'}</p>
          </div>
        ) : <p>No scale recommendation submitted.</p>}
      </section>

      <section>
        <h2>Audit</h2>
        <button onClick={async () => {
          try {
            const res = await workflowsApi.getAudit(workflowId);
            alert('Audit events: ' + (res.data || []).length);
          } catch { alert('Failed to load audit'); }
        }}>Load Audit</button>
      </section>

      <section>
        <h2>Actions</h2>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '10px' }}>
          {stateName === 'PITCH_SUBMITTED' && (
            <button onClick={async () => { await workflowsApi.evaluatePitch(workflowId); refresh(); }}>Evaluate Pitch</button>
          )}
          {stateName === 'PITCH_EVALUATED' && (
            <button onClick={async () => { await workflowsApi.assessRisk(workflowId); refresh(); }}>Assess Risk</button>
          )}
          {stateName === 'RISK_ASSESSED' && (
            <button onClick={async () => { await workflowsApi.submitHumanReview(workflowId, 'APPROVE'); refresh(); }}>Approve (Human Review)</button>
          )}
          {stateName === 'AWAITING_HUMAN_REVIEW' && (
            <button onClick={async () => {
              const sid = prompt('Startup ID');
              if (sid) { await workflowsApi.selectStartup(workflowId, { startup_id: sid, selection_reason: 'Selected via UI' }); refresh(); }
            }}>Select Startup</button>
          )}
          {(stateName === 'STARTUP_SELECTED' || stateName === 'PROBLEM_ALLOCATED') && (
            <button onClick={async () => { await workflowsApi.createPilot(workflowId, { pilot_id: 'pilot-' + Date.now(), description: 'UI-created pilot' }); refresh(); }}>Create Pilot</button>
          )}
          {stateName === 'PILOT_CREATED' && (
            <button onClick={async () => {
              const mid = prompt('Milestone ID');
              if (mid) { await workflowsApi.createMilestone(workflowId, { milestone_id: mid, description: 'UI milestone', due_date: '2026-12-01' }); refresh(); }
            }}>Create Milestone</button>
          )}
          {stateName === 'MILESTONE_ACTIVE' && (
            <button onClick={async () => {
              const mid = prompt('Milestone ID to submit evidence');
              const eid = prompt('Evidence ID');
              if (mid && eid) {
                await workflowsApi.submitEvidence(workflowId, mid, { evidence_id: eid, milestone_id: mid, description: 'Evidence from UI', link: 'http://example.com', status: 'verified' });
                refresh();
              }
            }}>Submit Verified Evidence</button>
          )}
          {stateName === 'EVIDENCE_SUBMITTED' && (
            <button onClick={async () => {
              const mid = prompt('Milestone ID to evaluate');
              if (mid) { await workflowsApi.evaluateMilestone(workflowId, mid); refresh(); }
            }}>Evaluate Milestone</button>
          )}
          {stateName === 'MILESTONE_EVALUATED' && (
            <button onClick={async () => {
              const mid = prompt('Milestone ID');
              const action = prompt('Remediation action');
              if (mid && action) { await workflowsApi.submitRemediation(workflowId, mid, { milestone_id: mid, action, status: 'submitted' }); refresh(); }
            }}>Submit Remediation</button>
          )}
          {stateName === 'REMEDIATION' && (
            <button onClick={async () => {
              const mid = prompt('Milestone ID for new evidence');
              if (mid) { await workflowsApi.submitEvidence(workflowId, mid, { evidence_id: 're-' + mid, milestone_id: mid, description: 'Remediation evidence', link: 'http://example.com/remediation', status: 'verified' }); refresh(); }
            }}>Submit Remediation Evidence</button>
          )}
          {stateName === 'FINAL_EVALUATION' && (
            <button onClick={async () => {
              await workflowsApi.submitPerformance(workflowId, { startup_id: ctx.startup_selection?.startup_id || 'unknown', summary: 'Performance from UI', metrics: { uptime: 0.99, cost_savings: 0.15 } });
              refresh();
            }}>Update Performance</button>
          )}
          {stateName === 'PERFORMANCE_UPDATED' && (
            <button onClick={async () => {
              await workflowsApi.submitScaleRecommendation(workflowId, { recommendation: 'SCALE', rationale: 'Positive performance', confidence_score: 0.91, supporting_factors: 'Verified milestones, strong pilot' });
              refresh();
            }}>Submit Scale Recommendation</button>
          )}
          {stateName === 'AWAITING_FINAL_DECISION' && (
            <button onClick={async () => {
              await workflowsApi.submitFinalDecision(workflowId, 'APPROVE');
              refresh();
            }}>Approve Final Decision</button>
          )}
        </div>
      </section>

      <section style={{ marginTop: '20px', borderTop: '2px solid #ddd', paddingTop: '20px' }}>
        <h2>Timeline / Status Visibility</h2>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {[
            'OPPORTUNITY_DISCOVERED', 'PITCH_SUBMITTED', 'PITCH_EVALUATED', 'RISK_ASSESSED',
            'AWAITING_HUMAN_REVIEW', 'STARTUP_SELECTED', 'PROBLEM_ALLOCATED', 'PILOT_CREATED',
            'MILESTONE_ACTIVE', 'EVIDENCE_SUBMITTED', 'MILESTONE_EVALUATED', 'REMEDIATION',
            'FINAL_EVALUATION', 'PERFORMANCE_UPDATED', 'SCALE_RECOMMENDATION', 'AWAITING_FINAL_DECISION',
            'HUMAN_FINAL_DECISION', 'COMPLETED', 'FAILED'
          ].map((stage) => {
            const completed = [
              'OPPORTUNITY_DISCOVERED','PITCH_SUBMITTED','PITCH_EVALUATED','RISK_ASSESSED',
              'AWAITING_HUMAN_REVIEW','STARTUP_SELECTED','PROBLEM_ALLOCATED','PILOT_CREATED',
              'MILESTONE_ACTIVE','EVIDENCE_SUBMITTED','MILESTONE_EVALUATED','REMEDIATION',
              'FINAL_EVALUATION','PERFORMANCE_UPDATED','SCALE_RECOMMENDATION','AWAITING_FINAL_DECISION',
              'HUMAN_FINAL_DECISION','COMPLETED'
            ].indexOf(stage) < [
              'OPPORTUNITY_DISCOVERED','PITCH_SUBMITTED','PITCH_EVALUATED','RISK_ASSESSED',
              'AWAITING_HUMAN_REVIEW','STARTUP_SELECTED','PROBLEM_ALLOCATED','PILOT_CREATED',
              'MILESTONE_ACTIVE','EVIDENCE_SUBMITTED','MILESTONE_EVALUATED','REMEDIATION',
              'FINAL_EVALUATION','PERFORMANCE_UPDATED','SCALE_RECOMMENDATION','AWAITING_FINAL_DECISION',
              'HUMAN_FINAL_DECISION','COMPLETED','FAILED'
            ].indexOf(stateName);
            const isCurrent = stage === stateName;
            return (
              <div key={stage} style={{
                padding: '6px 10px',
                borderRadius: '4px',
                background: isCurrent ? '#e0f7fa' : completed ? '#e8f5e9' : '#f5f5f5',
                border: `1px solid ${isCurrent ? '#4fc3f7' : completed ? '#81c784' : '#ccc'}`,
                opacity: completed || isCurrent ? 1 : 0.4,
                fontSize: '12px',
                fontWeight: isCurrent ? 'bold' : 'normal'
              }}>
                {stage.replace(/_/g, ' ')}
                {isCurrent ? ' (CURRENT)' : completed ? ' ✓' : ''}
                {stage === 'AWAITING_HUMAN_REVIEW' || stage === 'AWAITING_FINAL_DECISION' ? ' [HUMAN GATE]' : ''}
                {stage === 'FAILED' ? ' [TERMINATED]' : ''}
              </div>
            );
          })}
        </div>
      </section>
    </Layout>
  );
};
