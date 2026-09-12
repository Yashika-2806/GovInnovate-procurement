import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API Client
const apiClient = {
  createWorkflow: (opp: any) => axios.post(`${API_BASE}/api/workflows`, opp),
  getWorkflow: (id: string) => axios.get(`${API_BASE}/api/workflows/${id}`),
  submitPitch: (id: string, pitch: any) => axios.post(`${API_BASE}/api/workflows/${id}/pitch`, pitch),
  evaluatePitch: (id: string) => axios.post(`${API_BASE}/api/workflows/${id}/pitch/evaluate`),
  assessRisk: (id: string) => axios.post(`${API_BASE}/api/workflows/${id}/risk/assess`),
};

function App() {
  const [status, setStatus] = useState<string>('Connecting...');
  const [workflowId, setWorkflowId] = useState<string | null>(null);

  useEffect(() => {
    axios.get(`${API_BASE}/health`)
      .then(res => setStatus('Backend Online'))
      .catch(err => setStatus('Backend Offline'));
  }, []);

  const startWorkflow = async () => {
    const opp = {
      opportunity_id: `opp-${Math.random().toString(36).substring(7)}`,
      title: "Test AI Drone",
      description: "Test description",
      organization: "GovTest",
      status: "active"
    };
    const res = await apiClient.createWorkflow(opp);
    setWorkflowId(res.data.workflow_id);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>GovInnovate Procurement</h1>
      <p>System Status: <strong>{status}</strong></p>

      <button onClick={startWorkflow}>Start Workflow</button>

      {workflowId && (
        <div>
          <p>Workflow Created: <strong>{workflowId}</strong></p>
          <button onClick={() => apiClient.submitPitch(workflowId, {pitch_id: 'p1', startup_id: 's1', opportunity_id: 'o1'})}>
            Submit Pitch
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
