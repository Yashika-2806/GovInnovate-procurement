import client from './client';

export interface Workflow {
  workflow_id: string;
  state: string;
  context: any;
}

export const workflowsApi = {
  // Core lifecycle
  create: (opportunity: any) => client.post('/api/workflows', opportunity),
  get: (workflowId: string) => client.get<Workflow>(`/api/workflows/${workflowId}`),

  // Pitch
  submitPitch: (workflowId: string, pitch: any) => client.post(`/api/workflows/${workflowId}/pitch`, pitch),
  evaluatePitch: (workflowId: string) => client.post(`/api/workflows/${workflowId}/pitch/evaluate`),

  // Risk
  assessRisk: (workflowId: string) => client.post(`/api/workflows/${workflowId}/risk/assess`),

  // Human review gate
  submitHumanReview: (workflowId: string, decision: string) =>
    client.post(`/api/workflows/${workflowId}/human-review`, null, { params: { decision } }),

  // Startup selection (real endpoint)
  selectStartup: (workflowId: string, selection: any) =>
    client.post(`/api/workflows/${workflowId}/startup-selection`, selection),

  // Allocation (transition from STARTUP_SELECTED -> PROBLEM_ALLOCATED; backend handles via state machine when needed)
  // No separate endpoint; allocation embedded in startup/pilot flow per backend

  // Pilot
  createPilot: (workflowId: string, pilot: any) =>
    client.post(`/api/workflows/${workflowId}/pilot`, pilot),

  // Milestones
  createMilestone: (workflowId: string, milestone: any) =>
    client.post(`/api/workflows/${workflowId}/milestones`, milestone),
  getMilestones: (workflowId: string) => client.get(`/api/workflows/${workflowId}/milestones`),
  getMilestone: (workflowId: string, milestoneId: string) =>
    client.get(`/api/workflows/${workflowId}/milestones/${milestoneId}`),

  // Evidence
  submitEvidence: (workflowId: string, milestoneId: string, evidence: any) =>
    client.post(`/api/workflows/${workflowId}/milestones/${milestoneId}/evidence`, evidence),
  getEvidence: (workflowId: string, milestoneId: string) =>
    client.get(`/api/workflows/${workflowId}/milestones/${milestoneId}/evidence`),

  // Milestone evaluation (real backend logic — PASS/FAIL/REQUIRES_VERIFICATION)
  evaluateMilestone: (workflowId: string, milestoneId: string) =>
    client.post(`/api/workflows/${workflowId}/milestones/${milestoneId}/evaluate`),

  // Remediation
  submitRemediation: (workflowId: string, milestoneId: string, remediation: any) =>
    client.post(`/api/workflows/${workflowId}/milestones/${milestoneId}/remediation`, remediation),

  // Final evaluation
  submitFinalEvaluation: (workflowId: string, evaluation: any) =>
    client.post(`/api/workflows/${workflowId}/final-evaluation`, evaluation),

  // Performance profile
  submitPerformance: (workflowId: string, performance: any) =>
    client.post(`/api/workflows/${workflowId}/performance`, performance),
  getPerformance: (workflowId: string) =>
    client.get(`/api/workflows/${workflowId}/performance`),

  // Scale recommendation
  submitScaleRecommendation: (workflowId: string, recommendation: any) =>
    client.post(`/api/workflows/${workflowId}/scale-recommendation`, recommendation),

  // Final decision (human gate — must be from AWAITING_FINAL_DECISION)
  submitFinalDecision: (workflowId: string, decision: string) =>
    client.post(`/api/workflows/${workflowId}/final-decision`, null, { params: { decision } }),

  // Audit
  getAudit: (workflowId: string) => client.get(`/api/workflows/${workflowId}/audit`),

  getHealth: () => client.get('/health'),
};
