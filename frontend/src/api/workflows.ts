import client from './client';

export interface Workflow {
  workflow_id: string;
  state: string;
  context: any;
}

export const workflowsApi = {
  create: (opportunity: any) => client.post('/api/workflows', opportunity),
  get: (workflowId: string) => client.get<Workflow>(`/api/workflows/${workflowId}`),
  submitPitch: (workflowId: string, pitch: any) => client.post(`/api/workflows/${workflowId}/pitch`, pitch),
  evaluatePitch: (workflowId: string) => client.post(`/api/workflows/${workflowId}/pitch/evaluate`),
  assessRisk: (workflowId: string) => client.post(`/api/workflows/${workflowId}/risk/assess`),
  submitHumanReview: (workflowId: string, decision: string) =>
    client.post(`/api/workflows/${workflowId}/human-review`, { decision }),
  evaluateMilestone: (workflowId: string, milestoneId: string) =>
    client.post(`/api/workflows/${workflowId}/milestones/${milestoneId}/evaluate`),
  submitFinalDecision: (workflowId: string, decision: string) =>
    client.post(`/api/workflows/${workflowId}/final-decision`, { decision }),
  getHealth: () => client.get('/health'),
};
