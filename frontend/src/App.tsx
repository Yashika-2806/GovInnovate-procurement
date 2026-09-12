import { Dashboard } from './pages/Dashboard';
import { WorkflowDetail } from './pages/WorkflowDetail';
import { useState } from 'react';

function App() {
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif', background: '#fafbfc', minHeight: '100vh' }}>
      <header style={{ background: '#0a2540', color: '#fff', padding: '20px 24px', borderBottom: '3px solid #0066cc' }}>
        <h1 style={{ margin: 0, fontSize: '22px', letterSpacing: '0.5px' }}>GovInnovate — Procurement Lifecycle</h1>
        <p style={{ margin: '4px 0 0', opacity: 0.85, fontSize: '14px' }}>Public-sector AI-assisted procurement with mandatory human gates.</p>
      </header>
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
        {!selectedWorkflowId ? (
          <Dashboard onSelectWorkflow={(id: string) => setSelectedWorkflowId(id)} />
        ) : (
          <>
            <button onClick={() => setSelectedWorkflowId(null)} style={{ marginBottom: '16px', padding: '8px 16px', cursor: 'pointer' }}>
              ← Back to Dashboard
            </button>
            <WorkflowDetail workflowId={selectedWorkflowId} />
          </>
        )}
      </main>
    </div>
  );
}

export default App;
