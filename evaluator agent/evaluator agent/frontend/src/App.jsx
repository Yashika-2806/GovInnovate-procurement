import React, { useState, useEffect, useRef } from 'react';
import LangGraphVisualizer from './components/LangGraphVisualizer';
import MilestoneLifecycleBoard from './components/MilestoneLifecycleBoard';
import ScoringJustificationConsole from './components/ScoringJustificationConsole';
import SubagentAuditCards from './components/SubagentAuditCards';
import EvidenceEvaluatorStudio from './components/EvidenceEvaluatorStudio';

const API = 'http://127.0.0.1:8000';

const NODE_SEQUENCE = [
  'initialize_evaluation',
  'validate_evidence',
  'analyze_evidence',
  'calculate_milestone_score',
  'generate_recommendations',
  'security_audit',
  'telemetry_analysis',
  'escrow_disbursement',
  'finalize_evaluation',
];

/* ── build the LangGraph state payload the backend actually expects ── */
function buildState(startup, milestone, evidence) {
  return {
    startup_profile: {
      startup_id:                   startup.id,
      startup_name:                 startup.name,
      primary_domain:               startup.primary_domain,
      initial_pitch_score:          startup.initial_pitch_score ?? 80,
      demonstrated_execution_score: startup.demonstrated_execution_score ?? 0,
      domain_relevance_vector:      startup.domain_relevance_vector ?? {},
      problem:                      startup.problem ?? {},
      historical_milestones_completed: 0,
      historical_milestones_failed:    0,
    },
    current_milestone: {
      id:                            milestone.id,
      title:                         milestone.title,
      project_type:                  milestone.project_type ?? 'Software',
      sequence_index:                milestone.sequence_index ?? 1,
      objective:                     milestone.objective ?? '',
      requirements:                  milestone.requirements ?? [],
      kpis:                          milestone.kpis ?? [],
      acceptance_criteria:           milestone.acceptance_criteria ?? [],
      contractual_approval_required: milestone.contractual_approval_required ?? false,
      contractual_approval_granted:  milestone.contractual_approval_granted ?? false,
      status:                        milestone.status ?? 'Pending',
    },
    submitted_evidence: evidence ?? [],
    scoring_weights:    {},
    human_approval_granted: false,
    status: 'In Progress',
    audit_logs: [],
  };
}

export default function App() {
  const [startups,         setStartups]         = useState([]);
  const [selectedStartup,  setSelectedStartup]  = useState(null);
  const [selectedMilestone,setSelectedMilestone]= useState(null);

  const [running,          setRunning]           = useState(false);
  const [activeNode,       setActiveNode]        = useState(null);
  const [completedNodes,   setCompletedNodes]    = useState([]);
  const [nodeLog,          setNodeLog]           = useState([]);

  const [result,           setResult]            = useState(null);
  const [error,            setError]             = useState(null);
  const [activeTab,        setActiveTab]         = useState('evidence');
  const [showApproval,     setShowApproval]      = useState(false);
  const [approving,        setApproving]         = useState(false);
  const [loadingId,        setLoadingId]         = useState(null);

  /* ── load startups once ── */
  useEffect(() => {
    fetch(`${API}/api/sample-startups`)
      .then(r => r.json())
      .then(d => setStartups(d.startups ?? []))
      .catch(() => setError('Cannot reach API at ' + API));
  }, []);

  function resetEval() {
    setActiveNode(null);
    setCompletedNodes([]);
    setNodeLog([]);
    setResult(null);
    setError(null);
  }

  function pickStartup(startup) {
    setLoadingId(startup.id);
    resetEval();
    setSelectedStartup(startup);
    setSelectedMilestone(startup.milestone ?? null);
    setActiveTab('evidence');
    setLoadingId(null);
  }

  /* ── main evaluate ── */
  async function handleEvaluate() {
    if (!selectedStartup || !selectedMilestone) return;
    setRunning(true);
    resetEval();
    setActiveNode(NODE_SEQUENCE[0]);

    const state = buildState(
      selectedStartup,
      selectedMilestone,
      selectedStartup.evidence ?? []
    );

    /* animate nodes while API call runs */
    let nodeIdx = 0;
    const timer = setInterval(() => {
      nodeIdx++;
      if (nodeIdx < NODE_SEQUENCE.length) {
        setCompletedNodes(c => [...c, NODE_SEQUENCE[nodeIdx - 1]]);
        setActiveNode(NODE_SEQUENCE[nodeIdx]);
        setNodeLog(l => [...l, { node: NODE_SEQUENCE[nodeIdx - 1], ts: new Date().toLocaleTimeString() }]);
      }
    }, 650);

    try {
      const res  = await fetch(`${API}/api/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state }),
      });
      clearInterval(timer);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`);

      setCompletedNodes([...NODE_SEQUENCE]);
      setActiveNode(null);
      setNodeLog(l => [...l, { node: 'finalize_evaluation', ts: new Date().toLocaleTimeString() }]);
      setResult(data.result ?? data);
    } catch (e) {
      clearInterval(timer);
      setActiveNode(null);
      setError(e.message);
    } finally {
      setRunning(false);
    }
  }

  /* ── approve milestone ── */
  async function handleApprove() {
    if (!selectedStartup || !selectedMilestone) return;
    setApproving(true);
    try {
      const state = buildState(selectedStartup, selectedMilestone, selectedStartup.evidence ?? []);
      state.human_approval_granted = true;
      const res  = await fetch(`${API}/api/grant-approval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state, granted_by: 'Human Evaluator' }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? 'Approval failed');
      setResult(data.result ?? data);
      setShowApproval(false);
    } catch (e) {
      setError('Approval error: ' + e.message);
    } finally {
      setApproving(false);
    }
  }

  /* ── export report ── */
  async function handleExport() {
    if (!result) return;
    try {
      const res  = await fetch(`${API}/api/export-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: result }),
      });
      const data = await res.json();
      const blob = new Blob(
        [data.report_markdown ?? JSON.stringify(data, null, 2)],
        { type: 'text/markdown' }
      );
      const url = URL.createObjectURL(blob);
      const a   = document.createElement('a');
      a.href = url; a.download = `eval-${Date.now()}.md`; a.click();
    } catch (e) {
      setError('Export failed: ' + e.message);
    }
  }

  /* ── derived values ── */
  const score  = result?.milestone_score;
  const passed = score?.passed;
  const canEvaluate = !running && !!selectedStartup && !!selectedMilestone;

  /* ── TABS ── */
  const TABS = [
    { id: 'evidence',   icon: '🔬', label: 'Evidence' },
    { id: 'scoring',    icon: '📊', label: 'Scoring' },
    { id: 'subagents',  icon: '🤖', label: 'Agents' },
    { id: 'state',      icon: '🕰️', label: 'State Trail' },
  ];

  return (
    <div style={{ minHeight: '100vh' }}>

      {/* ══════════════════ HEADER ══════════════════ */}
      <header className="app-header">
        <div className="brand">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
              stroke="url(#hg)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <defs>
              <linearGradient id="hg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#6366f1"/><stop offset="100%" stopColor="#a78bfa"/>
              </linearGradient>
            </defs>
          </svg>
          Evaluator Agent
        </div>

        {/* Startup selector buttons */}
        <div style={{ display:'flex', gap:'0.4rem', alignItems:'center', flexWrap:'wrap' }}>
          <span style={{ fontSize:'0.65rem', color:'var(--text-muted)', flexShrink:0 }}>Select startup:</span>
          {startups.length === 0 && (
            <span style={{ fontSize:'0.68rem', color:'var(--text-dim)' }}>Loading…</span>
          )}
          {startups.map(s => (
            <button
              key={s.id}
              id={`btn-startup-${s.id}`}
              onClick={() => pickStartup(s)}
              disabled={running}
              style={{
                background: selectedStartup?.id === s.id
                  ? 'rgba(99,102,241,0.22)' : 'rgba(255,255,255,0.05)',
                border: `1px solid ${selectedStartup?.id === s.id ? 'rgba(99,102,241,0.7)' : 'rgba(255,255,255,0.1)'}`,
                color: selectedStartup?.id === s.id ? '#c7d2fe' : 'var(--text-muted)',
                borderRadius: 9, padding: '0.32rem 0.75rem',
                fontSize: '0.72rem', fontWeight: 700, cursor: 'pointer',
                transition: 'all 0.18s',
                opacity: running ? 0.5 : 1,
              }}
            >
              {loadingId === s.id ? '…' : s.name}
            </button>
          ))}
        </div>

        {/* Right actions */}
        <div style={{ display:'flex', gap:'0.5rem', alignItems:'center', flexShrink:0 }}>
          {result && (
            <button
              onClick={handleExport}
              style={{ background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.1)', color:'var(--text-main)', borderRadius:9, padding:'0.35rem 0.75rem', fontSize:'0.72rem', fontWeight:700, cursor:'pointer' }}
            >
              ⬇ Export
            </button>
          )}
          {passed && (
            <button
              onClick={() => setShowApproval(true)}
              style={{ background:'linear-gradient(135deg,#10b981,#059669)', color:'#fff', border:'none', borderRadius:9, padding:'0.35rem 0.85rem', fontSize:'0.72rem', fontWeight:700, cursor:'pointer', boxShadow:'0 4px 15px rgba(16,185,129,0.3)' }}
            >
              🎉 Approve
            </button>
          )}
          <button
            id="btn-evaluate"
            onClick={handleEvaluate}
            disabled={!canEvaluate}
            style={{
              background: canEvaluate
                ? 'linear-gradient(135deg,#6366f1,#8b5cf6)'
                : 'rgba(255,255,255,0.06)',
              color: canEvaluate ? '#fff' : 'var(--text-dim)',
              border: 'none', borderRadius: 9, padding: '0.38rem 1rem',
              fontSize: '0.75rem', fontWeight: 800, cursor: canEvaluate ? 'pointer' : 'not-allowed',
              boxShadow: canEvaluate ? '0 4px 18px rgba(99,102,241,0.4)' : 'none',
              transition: 'all 0.2s', display:'flex', alignItems:'center', gap:'0.4rem',
            }}
          >
            {running ? (
              <>
                <span style={{ display:'inline-block', width:11, height:11, border:'2px solid rgba(255,255,255,0.4)', borderTopColor:'#fff', borderRadius:'50%', animation:'spin 0.9s linear infinite' }} />
                Evaluating…
              </>
            ) : '▶ Evaluate'}
          </button>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div style={{ background:'rgba(239,68,68,0.1)', borderBottom:'1px solid rgba(239,68,68,0.2)', padding:'0.5rem 1.5rem', display:'flex', justifyContent:'space-between', fontSize:'0.72rem', color:'#fca5a5' }}>
          <span>⚠ {error}</span>
          <button onClick={() => setError(null)} style={{ background:'none', border:'none', color:'#fca5a5', cursor:'pointer', fontWeight:700 }}>✕</button>
        </div>
      )}

      {/* Hint when nothing selected */}
      {!selectedStartup && !error && (
        <div style={{ textAlign:'center', padding:'3rem 1rem', color:'var(--text-dim)' }}>
          <div style={{ fontSize:'2.5rem', marginBottom:'0.75rem' }}>👆</div>
          <div style={{ fontSize:'0.9rem', fontWeight:700, color:'var(--text-muted)', marginBottom:'0.35rem' }}>
            Select a startup above to get started
          </div>
          <div style={{ fontSize:'0.75rem' }}>Then click <strong style={{ color:'#818cf8' }}>▶ Evaluate</strong> to run the full LangGraph pipeline</div>
        </div>
      )}

      {/* ══════════════════ MAIN GRID ══════════════════ */}
      {selectedStartup && (
        <div className="dashboard">

          {/* LEFT – pipeline + log */}
          <div style={{ display:'flex', flexDirection:'column', gap:'0.85rem' }}>
            <LangGraphVisualizer
              activeNode={activeNode}
              completedNodes={completedNodes}
              isRunning={running}
            />

            {nodeLog.length > 0 && (
              <div className="glass" style={{ padding:'0.75rem' }}>
                <div className="section-title" style={{ fontSize:'0.7rem', marginBottom:'0.45rem' }}>📋 Execution Log</div>
                <div style={{ display:'flex', flexDirection:'column', gap:'0.22rem', maxHeight:160, overflowY:'auto' }}>
                  {nodeLog.map((l, i) => (
                    <div key={i} style={{ display:'flex', gap:'0.5rem', fontSize:'0.6rem', color:'var(--text-muted)', alignItems:'center' }}>
                      <span style={{ color:'#10b981' }}>✓</span>
                      <span style={{ flex:1 }}>{l.node.replace(/_/g,' ')}</span>
                      <span style={{ color:'var(--text-dim)', fontFamily:'var(--font-mono)' }}>{l.ts}</span>
                    </div>
                  ))}
                  {running && activeNode && (
                    <div style={{ display:'flex', gap:'0.5rem', fontSize:'0.6rem', color:'#6366f1', alignItems:'center' }}>
                      <span style={{ display:'inline-block', width:8, height:8, border:'1.5px solid #6366f1', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.9s linear infinite' }} />
                      <span style={{ flex:1 }}>{activeNode.replace(/_/g,' ')}</span>
                      <span style={{ color:'var(--text-dim)' }}>running…</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* CENTRE – tabs */}
          <div style={{ display:'flex', flexDirection:'column', gap:'0.85rem', minWidth:0 }}>

            {/* Startup info bar */}
            <div className="glass" style={{ padding:'0.75rem 1rem', display:'flex', gap:'0.75rem', alignItems:'center', flexWrap:'wrap' }}>
              <div style={{ flex:1 }}>
                <div style={{ fontSize:'1rem', fontWeight:800, color:'#f1f5f9', marginBottom:2 }}>{selectedStartup.name}</div>
                <div style={{ fontSize:'0.68rem', color:'var(--text-muted)' }}>
                  {selectedStartup.primary_domain} · {selectedMilestone?.project_type ?? 'Unknown'} · Milestone #{selectedMilestone?.sequence_index ?? '?'}
                </div>
              </div>
              <span style={{ fontSize:'0.65rem', padding:'0.18rem 0.55rem', borderRadius:9999, background:'rgba(99,102,241,0.15)', color:'#a5b4fc', border:'1px solid rgba(99,102,241,0.3)', fontWeight:700 }}>
                {selectedStartup.primary_domain}
              </span>
              {result && (
                <div style={{ display:'flex', alignItems:'center', gap:'0.45rem', background: passed ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', border:`1px solid ${passed ? 'rgba(16,185,129,0.3)':'rgba(239,68,68,0.3)'}`, borderRadius:10, padding:'0.35rem 0.75rem' }}>
                  <span style={{ fontSize:'1.15rem', fontWeight:900, color: passed ? '#10b981':'#ef4444' }}>
                    {score?.total_weighted_score?.toFixed(1) ?? '—'}
                  </span>
                  <div>
                    <div style={{ fontSize:'0.58rem', color:'var(--text-muted)' }}>Score / 100</div>
                    <div style={{ fontSize:'0.65rem', fontWeight:700, color: passed ? '#6ee7b7':'#fca5a5' }}>
                      {passed ? '✓ Passed' : '✗ Failed'}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Milestone info */}
            {selectedMilestone && (
              <div className="glass" style={{ padding:'0.75rem 1rem', borderLeft:'3px solid #6366f1' }}>
                <div style={{ fontSize:'0.62rem', color:'var(--text-dim)', textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:2 }}>Active Milestone</div>
                <div style={{ fontSize:'0.88rem', fontWeight:800, color:'#c7d2fe', marginBottom:3 }}>{selectedMilestone.title}</div>
                <div style={{ fontSize:'0.68rem', color:'var(--text-muted)' }}>{selectedMilestone.objective}</div>
              </div>
            )}

            {/* Tab bar */}
            <div className="glass" style={{ overflow:'hidden', flex:1 }}>
              <div style={{ display:'flex', borderBottom:'1px solid var(--border-color)', padding:'0 0.5rem', overflowX:'auto' }}>
                {TABS.map(t => (
                  <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
                    background:'transparent', border:'none', cursor:'pointer',
                    padding:'0.6rem 0.8rem', fontSize:'0.7rem', fontWeight:600,
                    color: activeTab === t.id ? '#c7d2fe' : 'var(--text-dim)',
                    borderBottom:`2px solid ${activeTab === t.id ? '#6366f1':'transparent'}`,
                    transition:'all 0.18s', whiteSpace:'nowrap',
                    display:'flex', alignItems:'center', gap:'0.3rem',
                  }}>
                    {t.icon} {t.label}
                  </button>
                ))}
              </div>

              <div style={{ padding:'1rem', overflowY:'auto', maxHeight:'calc(100vh - 320px)' }}>
                {activeTab === 'evidence' && (
                  <EvidenceEvaluatorStudio
                    evidence={selectedStartup?.evidence ?? []}
                    analysis={result?.evidence_analysis}
                  />
                )}
                {activeTab === 'scoring' && (
                  <ScoringJustificationConsole
                    score={result?.milestone_score}
                    recommendations={result?.justification_report}
                  />
                )}
                {activeTab === 'subagents' && (
                  <SubagentAuditCards
                    security={result?.security_audit}
                    telemetry={result?.telemetry_report}
                    escrow={result?.escrow_disbursement}
                  />
                )}
                {activeTab === 'state' && <StateTrail result={result} nodeLog={nodeLog} />}
              </div>
            </div>
          </div>

          {/* RIGHT – live scoring + milestones */}
          <div style={{ display:'flex', flexDirection:'column', gap:'0.85rem' }}>
            <div className="glass" style={{ padding:'1rem' }}>
              <div className="section-title">
                📊 Live Score
                {running && <span style={{ marginLeft:'auto', fontSize:'0.6rem', padding:'0.15rem 0.45rem', background:'rgba(99,102,241,0.15)', color:'#a5b4fc', border:'1px solid rgba(99,102,241,0.35)', borderRadius:9999, fontWeight:700 }}>LIVE</span>}
              </div>
              <ScoringJustificationConsole score={result?.milestone_score} recommendations={result?.justification_report} />
            </div>

            {/* Milestone details */}
            {selectedMilestone && (
              <div className="glass" style={{ padding:'1rem', flex:1, overflowY:'auto' }}>
                <div className="section-title">🏁 Requirements</div>
                <div style={{ display:'flex', flexDirection:'column', gap:'0.35rem' }}>
                  {(selectedMilestone.requirements ?? []).map((req, i) => (
                    <div key={i} style={{ display:'flex', gap:'0.4rem', fontSize:'0.68rem', color:'#c7d2fe', padding:'0.4rem 0.6rem', background:'rgba(255,255,255,0.02)', border:'1px solid rgba(255,255,255,0.06)', borderRadius:8 }}>
                      <span style={{ color:'#6366f1', fontWeight:800, flexShrink:0 }}>→</span> {req}
                    </div>
                  ))}
                </div>

                {selectedMilestone.kpis?.length > 0 && (
                  <div style={{ marginTop:'0.85rem' }}>
                    <div className="section-title" style={{ marginBottom:'0.45rem' }}>📈 KPIs</div>
                    {selectedMilestone.kpis.map((kpi, i) => (
                      <div key={i} style={{ padding:'0.45rem 0.6rem', background:'rgba(255,255,255,0.02)', border:'1px solid rgba(255,255,255,0.06)', borderRadius:8, marginBottom:4, fontSize:'0.67rem' }}>
                        <div style={{ display:'flex', justifyContent:'space-between', marginBottom:3 }}>
                          <span style={{ color:'#e2e8f0', fontWeight:600 }}>{kpi.name}</span>
                          <span style={{ color: kpi.achieved ? '#10b981' : '#f59e0b', fontWeight:700 }}>
                            {kpi.actual_value}{kpi.unit} / {kpi.target_value}{kpi.unit}
                          </span>
                        </div>
                        <div className="prog-bar">
                          <div className="prog-fill" style={{ width:`${Math.min(100, (kpi.actual_value / kpi.target_value) * 100)}%`, background: kpi.achieved ? 'linear-gradient(90deg,#10b981,#34d399)' : 'linear-gradient(90deg,#f59e0b,#fbbf24)' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ══════════════════ APPROVAL MODAL ══════════════════ */}
      {showApproval && (
        <div
          style={{ position:'fixed', inset:0, background:'rgba(0,0,0,0.8)', backdropFilter:'blur(12px)', zIndex:200, display:'flex', alignItems:'center', justifyContent:'center', padding:'1.5rem' }}
          onClick={() => setShowApproval(false)}
        >
          <div
            className="glass"
            style={{ width:'min(480px,100%)', padding:'1.5rem', borderRadius:20 }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ fontSize:'1.25rem', fontWeight:800, marginBottom:'0.4rem' }}>🎉 Approve Milestone</div>
            <div style={{ fontSize:'0.75rem', color:'var(--text-muted)', marginBottom:'1rem', lineHeight:1.6 }}>
              You are approving <strong style={{ color:'#c7d2fe' }}>{selectedMilestone?.title}</strong> for <strong style={{ color:'#c7d2fe' }}>{selectedStartup?.name}</strong>. This triggers escrow disbursement and is a contractual action.
            </div>
            <div style={{ background:'rgba(245,158,11,0.08)', border:'1px solid rgba(245,158,11,0.25)', borderRadius:10, padding:'0.7rem', marginBottom:'1.1rem' }}>
              <div style={{ fontSize:'0.7rem', color:'#fcd34d', fontWeight:700, marginBottom:3 }}>⚠ Requires human authority</div>
              <div style={{ fontSize:'0.65rem', color:'var(--text-muted)' }}>
                Score: {score?.total_weighted_score?.toFixed(1)}/100 · Threshold: {score?.pass_threshold ?? 70}/100
              </div>
            </div>
            <div style={{ display:'flex', gap:'0.6rem', justifyContent:'flex-end' }}>
              <button onClick={() => setShowApproval(false)} style={{ background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.1)', color:'var(--text-main)', borderRadius:8, padding:'0.45rem 0.85rem', fontSize:'0.72rem', fontWeight:700, cursor:'pointer' }}>Cancel</button>
              <button onClick={handleApprove} disabled={approving} style={{ background:'linear-gradient(135deg,#10b981,#059669)', color:'#fff', border:'none', borderRadius:8, padding:'0.45rem 0.95rem', fontSize:'0.72rem', fontWeight:700, cursor:'pointer' }}>
                {approving ? 'Processing…' : '✓ Confirm Approval'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── State Trail ─── */
function StateTrail({ result, nodeLog }) {
  if (!result) return (
    <div style={{ textAlign:'center', padding:'2rem', color:'var(--text-dim)', fontSize:'0.75rem' }}>
      <div style={{ fontSize:'2rem', marginBottom:'0.5rem' }}>🕰️</div>
      State snapshots appear here after evaluation
    </div>
  );

  const rows = [
    { l:'Startup ID',     v: result.startup_profile?.startup_id ?? 'N/A' },
    { l:'Status',         v: result.status ?? 'N/A' },
    { l:'Score',          v: result.milestone_score ? `${result.milestone_score.total_weighted_score?.toFixed(2)}/100` : 'N/A' },
    { l:'Passed',         v: result.milestone_score?.passed ? '✓ Yes' : '✗ No' },
    { l:'Evidence Items', v: result.submitted_evidence?.length ?? 0 },
    { l:'Security Risk',  v: result.security_audit?.overall_risk_level ?? 'N/A' },
    { l:'Anomalies',      v: result.telemetry_report?.anomalies?.length ?? 0 },
    { l:'Escrow Amount',  v: result.escrow_disbursement?.net_payout_usd != null ? `$${result.escrow_disbursement.net_payout_usd.toLocaleString()}` : 'N/A' },
    { l:'Exec Step',      v: result.execution_step ?? 'N/A' },
    { l:'Action',         v: result.recommended_action ?? 'N/A' },
  ];

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:'0.65rem' }}>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0.4rem' }}>
        {rows.map(r => (
          <div key={r.l} style={{ background:'rgba(255,255,255,0.02)', border:'1px solid rgba(255,255,255,0.06)', borderRadius:8, padding:'0.45rem 0.65rem' }}>
            <div style={{ fontSize:'0.58rem', color:'var(--text-dim)', textTransform:'uppercase', letterSpacing:'0.04em' }}>{r.l}</div>
            <div style={{ fontSize:'0.75rem', fontWeight:700, color:'#c7d2fe', marginTop:2 }}>{String(r.v)}</div>
          </div>
        ))}
      </div>

      {nodeLog.length > 0 && (
        <div>
          <div style={{ fontSize:'0.68rem', fontWeight:700, color:'var(--text-muted)', marginBottom:5, textTransform:'uppercase' }}>Node Timeline</div>
          {nodeLog.map((l, i) => (
            <div key={i} style={{ display:'flex', gap:'0.5rem', alignItems:'center', padding:'0.3rem 0', borderBottom:'1px solid rgba(255,255,255,0.04)', fontSize:'0.65rem' }}>
              <span style={{ color:'var(--text-dim)', fontFamily:'var(--font-mono)', width:65, flexShrink:0 }}>{l.ts}</span>
              <div style={{ width:5, height:5, borderRadius:'50%', background:'#10b981', flexShrink:0 }} />
              <span style={{ color:'#e2e8f0' }}>{l.node.replace(/_/g,' ')}</span>
            </div>
          ))}
        </div>
      )}

      <details>
        <summary style={{ fontSize:'0.67rem', color:'var(--text-muted)', cursor:'pointer', padding:'0.25rem 0' }}>🔍 Raw JSON state</summary>
        <pre style={{ fontSize:'0.58rem', color:'#94a3b8', background:'rgba(0,0,0,0.3)', borderRadius:8, padding:'0.65rem', marginTop:6, overflowX:'auto', maxHeight:280, overflowY:'auto' }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      </details>
    </div>
  );
}
