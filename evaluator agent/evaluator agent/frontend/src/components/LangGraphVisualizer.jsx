import React, { useState, useEffect, useRef } from 'react';

const NODES = [
  { id: 'initialize_evaluation',     icon: '⚡', label: 'Initialize Evaluation',  desc: 'State bootstrap & config',  color: '#6366f1' },
  { id: 'validate_evidence',         icon: '🔍', label: 'Validate Evidence',       desc: 'Type & completeness checks', color: '#22d3ee' },
  { id: 'analyze_evidence',          icon: '🧠', label: 'Analyze Evidence',        desc: 'Deep-dive evidence audit',   color: '#8b5cf6' },
  { id: 'calculate_milestone_score', icon: '📊', label: 'Calculate Score',         desc: 'Weighted 8-criterion score', color: '#a78bfa' },
  { id: 'generate_recommendations',  icon: '💡', label: 'Generate Recs',           desc: 'Actionable next steps',      color: '#f59e0b' },
  { id: 'security_audit',            icon: '🛡️', label: 'Security Audit',          desc: 'CVE & compliance check',     color: '#ef4444' },
  { id: 'telemetry_analysis',        icon: '📡', label: 'Telemetry Analysis',      desc: 'SLO & latency anomalies',    color: '#10b981' },
  { id: 'escrow_disbursement',       icon: '💰', label: 'Escrow Disbursement',     desc: 'Fund release computation',   color: '#f59e0b' },
  { id: 'finalize_evaluation',       icon: '✅', label: 'Finalize Evaluation',     desc: 'Persist & emit result',      color: '#10b981' },
];

export default function LangGraphVisualizer({ activeNode, completedNodes = [], isRunning }) {
  const [animatingEdges, setAnimatingEdges] = useState(new Set());
  const prevActive = useRef(null);

  useEffect(() => {
    if (activeNode && activeNode !== prevActive.current) {
      const idx = NODES.findIndex(n => n.id === activeNode);
      if (idx > 0) setAnimatingEdges(e => new Set([...e, idx]));
      prevActive.current = activeNode;
    }
  }, [activeNode]);

  return (
    <div className="glass" style={{ padding: '1rem 0.85rem', height: '100%', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <div className="section-title" style={{ marginBottom: '0.6rem' }}>
        <span>⛓️</span> LangGraph Pipeline
        {isRunning && (
          <span className="badge badge-indigo" style={{ marginLeft: 'auto' }}>
            <span className="animate-spin" style={{ display: 'inline-block', width: 8, height: 8, border: '2px solid #6366f1', borderTopColor: 'transparent', borderRadius: '50%' }} />
            LIVE
          </span>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 }}>
        {NODES.map((node, idx) => {
          const isActive = activeNode === node.id;
          const isDone   = completedNodes.includes(node.id);
          const isPending = !isActive && !isDone;
          const borderColor = isActive ? node.color : isDone ? '#10b981' : 'rgba(255,255,255,0.06)';
          const bgColor     = isActive ? `${node.color}18` : isDone ? 'rgba(16,185,129,0.07)' : 'rgba(255,255,255,0.018)';

          return (
            <React.Fragment key={node.id}>
              {/* Edge line */}
              {idx > 0 && (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 8, position: 'relative' }}>
                  <div style={{
                    width: 2, height: '100%',
                    background: isDone || isActive
                      ? `linear-gradient(to bottom, ${NODES[idx-1].color}, ${node.color})`
                      : 'rgba(255,255,255,0.08)',
                    transition: 'background 0.4s ease',
                  }} />
                  {animatingEdges.has(idx) && (
                    <div style={{
                      position: 'absolute', width: 6, height: 6, borderRadius: '50%',
                      background: node.color, boxShadow: `0 0 8px ${node.color}`,
                      animation: 'slideDown 0.5s ease forwards',
                    }} />
                  )}
                </div>
              )}

              <div
                className={`node-item ${isActive ? 'node-active' : ''} ${isDone ? 'node-done' : ''} animate-fade`}
                style={{ borderColor, background: bgColor, transition: 'all 0.35s ease' }}
              >
                <div className="node-icon" style={{
                  background: isActive ? `${node.color}30` : isDone ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${borderColor}`,
                  fontSize: '0.85rem',
                }}>
                  {isActive
                    ? <span className="animate-spin" style={{ display: 'inline-block', width: 12, height: 12, border: `2px solid ${node.color}`, borderTopColor: 'transparent', borderRadius: '50%' }} />
                    : isDone ? '✓' : node.icon}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="node-label" style={{ color: isActive ? node.color : isDone ? '#6ee7b7' : '#e2e8f0' }}>
                    {node.label}
                  </div>
                  <div className="node-desc">{node.desc}</div>
                  {isActive && (
                    <div className="prog-bar" style={{ marginTop: 4 }}>
                      <div className="prog-fill" style={{
                        width: '60%',
                        background: `linear-gradient(90deg, ${node.color}80, ${node.color})`,
                        animation: 'shimmer 1.4s linear infinite',
                        backgroundSize: '200% auto',
                      }} />
                    </div>
                  )}
                </div>
                <div>
                  {isDone && <span style={{ color: '#10b981', fontSize: 11 }}>✓</span>}
                  {isPending && <span style={{ color: 'rgba(255,255,255,0.2)', fontSize: 10 }}>○</span>}
                </div>
              </div>
            </React.Fragment>
          );
        })}
      </div>

      {/* Progress footer */}
      <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.6rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.67rem', color: 'var(--text-muted)', marginBottom: 4 }}>
          <span>Pipeline Progress</span>
          <span>{completedNodes.length}/{NODES.length} nodes</span>
        </div>
        <div className="prog-bar">
          <div className="prog-fill" style={{
            width: `${(completedNodes.length / NODES.length) * 100}%`,
            background: 'linear-gradient(90deg, #6366f1, #8b5cf6, #a78bfa)',
          }} />
        </div>
      </div>
    </div>
  );
}
