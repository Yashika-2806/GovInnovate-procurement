export interface Workflow {
    workflow_id: string;
    state: string;
    context: any;
}
export declare const workflowsApi: {
    create: (opportunity: any) => any;
    get: (workflowId: string) => any;
    submitPitch: (workflowId: string, pitch: any) => any;
    evaluatePitch: (workflowId: string) => any;
    assessRisk: (workflowId: string) => any;
    submitHumanReview: (workflowId: string, decision: string) => any;
    evaluateMilestone: (workflowId: string, milestoneId: string) => any;
    submitFinalDecision: (workflowId: string, decision: string) => any;
    getHealth: () => any;
};
//# sourceMappingURL=workflows.d.ts.map