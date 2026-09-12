import client from './client';
export const workflowsApi = {
    create: (opportunity) => client.post('/api/workflows', opportunity),
    get: (workflowId) => client.get(`/api/workflows/${workflowId}`),
    submitPitch: (workflowId, pitch) => client.post(`/api/workflows/${workflowId}/pitch`, pitch),
    evaluatePitch: (workflowId) => client.post(`/api/workflows/${workflowId}/pitch/evaluate`),
    assessRisk: (workflowId) => client.post(`/api/workflows/${workflowId}/risk/assess`),
    submitHumanReview: (workflowId, decision) => client.post(`/api/workflows/${workflowId}/human-review`, { decision }),
    evaluateMilestone: (workflowId, milestoneId) => client.post(`/api/workflows/${workflowId}/milestones/${milestoneId}/evaluate`),
    submitFinalDecision: (workflowId, decision) => client.post(`/api/workflows/${workflowId}/final-decision`, { decision }),
    getHealth: () => client.get('/health'),
};
//# sourceMappingURL=workflows.js.map