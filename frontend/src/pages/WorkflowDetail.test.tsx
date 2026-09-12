import { render, screen, waitFor } from '@testing-library/react';
import { WorkflowDetail } from './WorkflowDetail';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as api from '../api/workflows';

vi.mock('../api/workflows');

describe('WorkflowDetail Lifecycle', () => {
  beforeEach(() => { vi.resetAllMocks(); });

  it('renders workflow detail with opportunity', async () => {
    (api.workflowsApi.get as any).mockResolvedValue({
      data: {
        workflow_id: 'wf-1',
        state: 'PITCH_SUBMITTED',
        context: {
          opportunity: { title: 'Test', description: 'D', organization: 'O', status: 'active' },
          milestones: {}, evidence: {}, evaluation_result: null, performance: null, scale_recommendation: null, startup_selection: null, pilot: null, remediations: {}
        }
      }
    });
    render(<WorkflowDetail workflowId="wf-1" />);
    await waitFor(() => expect(screen.getByText('Test')).toBeDefined());
  });

  it('shows human gate labels', async () => {
    (api.workflowsApi.get as any).mockResolvedValue({
      data: { workflow_id: 'wf-2', state: 'AWAITING_FINAL_DECISION', context: { milestones: {}, evidence: {}, startup_selection: null, pilot: null } }
    });
    render(<WorkflowDetail workflowId="wf-2" />);
    await waitFor(() => expect(screen.getByText(/HUMAN GATE/i)).toBeDefined());
  });
});
