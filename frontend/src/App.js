import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Layout } from './layouts/Layout';
import { useState, useEffect } from 'react';
import { workflowsApi, Workflow } from './api/workflows';
function App() {
    const [status, setStatus] = useState('Connecting...');
    const [workflowId, setWorkflowId] = useState(null);
    const [workflow, setWorkflow] = useState(null);
    useEffect(() => {
        checkHealth();
    }, []);
    const checkHealth = async () => {
        try {
            await workflowsApi.getHealth();
            setStatus('Backend Online');
        }
        catch {
            setStatus('Backend Offline');
        }
    };
    const refreshWorkflow = async (id) => {
        try {
            const res = await workflowsApi.get(id);
            setWorkflow(res.data);
        }
        catch (e) {
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
    const handleAction = async (action) => {
        await action();
        if (workflowId) {
            refreshWorkflow(workflowId);
        }
    };
    return (_jsxs(Layout, { children: [_jsx("h1", { children: "Dashboard" }), _jsxs("p", { children: ["System Status: ", _jsx("strong", { children: status })] }), !workflowId && (_jsx("button", { onClick: startWorkflow, children: "Start Workflow" })), workflow && (_jsxs("div", { children: [_jsxs("h2", { children: ["Workflow: ", workflow.workflow_id] }), _jsxs("p", { children: ["State: ", _jsx("strong", { children: workflow.state })] }), _jsxs("div", { style: { marginTop: '10px' }, children: [workflow.state === 'OPPORTUNITY_DISCOVERED' && (_jsx("button", { onClick: () => handleAction(() => workflowsApi.submitPitch(workflow.workflow_id, { pitch_id: 'p1', startup_id: 's1', opportunity_id: 'o1' })), children: "Submit Pitch" })), workflow.state === 'PITCH_SUBMITTED' && (_jsx("button", { onClick: () => handleAction(() => workflowsApi.evaluatePitch(workflow.workflow_id)), children: "Evaluate Pitch" })), workflow.state === 'PITCH_EVALUATED' && (_jsx("button", { onClick: () => handleAction(() => workflowsApi.assessRisk(workflow.workflow_id)), children: "Assess Risk" }))] })] }))] }));
}
export default App;
//# sourceMappingURL=App.js.map