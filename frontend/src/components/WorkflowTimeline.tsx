import { Workflow } from '../api/workflows';
import { StatusBadge } from './StatusBadge';

const STAGES = [
  'OPPORTUNITY_DISCOVERED',
  'PITCH_SUBMITTED',
  'PITCH_EVALUATED',
  'RISK_ASSESSED',
  'AWAITING_HUMAN_REVIEW',
  'STARTUP_SELECTED',
  'PROBLEM_ALLOCATED',
  'PILOT_CREATED',
  'MILESTONE_ACTIVE',
  'EVIDENCE_SUBMITTED',
  'MILESTONE_EVALUATED',
  'NEXT_MILESTONE',
  'REMEDIATION',
  'FINAL_EVALUATION',
  'PERFORMANCE_UPDATED',
  'SCALE_RECOMMENDATION',
  'AWAITING_FINAL_DECISION',
  'HUMAN_FINAL_DECISION',
  'FAILED'
];

export const WorkflowTimeline = ({ workflow }: { workflow: Workflow }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '20px' }}>
      {STAGES.map((stage) => {
        const isActive = workflow.state === stage;
        const isCompleted = STAGES.indexOf(stage) < STAGES.indexOf(workflow.state);

        return (
          <div key={stage} style={{
            padding: '10px',
            border: '1px solid #ccc',
            background: isActive ? '#e0f7fa' : isCompleted ? '#f0f0f0' : '#fff',
            opacity: !isActive && !isCompleted && workflow.state !== 'FAILED' ? 0.5 : 1
          }}>
            <strong>{stage.replace('_', ' ')}</strong>
            {isActive && <StatusBadge status="ACTIVE" />}
            {isCompleted && <StatusBadge status="COMPLETED" />}
          </div>
        );
      })}
    </div>
  );
};
