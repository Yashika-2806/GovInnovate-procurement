import React, { useState } from 'react';

const EV_ICONS = {
  github_repo:       '🐙',
  deployment_logs:   '🚀',
  performance_data:  '⚡',
  test_reports:      '🧪',
  documentation:     '📝',
  video_demo:        '🎬',
  architecture_docs: '🏗️',
  code_review:       '🔎',
  schematics:        '📐',
  user_documentation:'📄',
};

export default function EvidenceEvaluatorStudio({ evidence = [], analysis, onAddEvidence }) {
  const [selected, setSelected] = useState(null);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ type: 'github_repo', url: '', description: '' });

  const reqFulfill = analysis?.requirement_fulfillment ?? {};
  const kpiFulfill = analysis?.kpi_fulfillment ?? {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
      {/* Evidence list */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Evidence Items ({evidence.length})
          </div>
          <button className="btn btn-ghost" style={{ fontSize: '0.65rem', padding: '0.2rem 0.5rem' }} onClick={() => setAdding(a => !a)}>
            {adding ? '✕ Cancel' : '+ Add Evidence'}
          </button>
        </div>

        {adding && (
          <div style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 10, padding: '0.75rem', marginBottom: '0.5rem' }} className="animate-fade">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
              <select value={form.type} onChange={e => setForm(f => ({...f, type: e.target.value}))}>
                {Object.keys(EV_ICONS).map(k => <option key={k} value={k}>{k.replace(/_/g, ' ')}</option>)}
              </select>
              <input type="text" placeholder="URL or identifier" value={form.url} onChange={e => setForm(f => ({...f, url: e.target.value}))} />
              <input type="text" placeholder="Short description" value={form.description} onChange={e => setForm(f => ({...f, description: e.target.value}))} />
              <button className="btn btn-primary" style={{ fontSize: '0.7rem' }} onClick={() => {
                if (onAddEvidence) onAddEvidence({ ...form, id: `ev-${Date.now()}`, timestamp: new Date().toISOString() });
                setAdding(false);
                setForm({ type: 'github_repo', url: '', description: '' });
              }}>
                Add Evidence
              </button>
            </div>
          </div>
        )}

        {evidence.length === 0 && !adding && (
          <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-dim)', fontSize: '0.75rem', border: '1px dashed rgba(255,255,255,0.08)', borderRadius: 10 }}>
            No evidence submitted yet
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          {evidence.map((ev, idx) => {
            const icon = EV_ICONS[ev.type] ?? '📎';
            const isSelected = selected === idx;
            return (
              <div
                key={idx}
                onClick={() => setSelected(isSelected ? null : idx)}
                style={{
                  border: `1px solid ${isSelected ? 'rgba(99,102,241,0.45)' : 'rgba(255,255,255,0.06)'}`,
                  borderRadius: 10, padding: '0.55rem 0.7rem',
                  background: isSelected ? 'rgba(99,102,241,0.08)' : 'rgba(255,255,255,0.015)',
                  cursor: 'pointer', transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1rem' }}>{icon}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#e2e8f0' }}>
                      {ev.type?.replace(/_/g, ' ') ?? 'Evidence'}
                    </div>
                    {ev.url && (
                      <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {ev.url}
                      </div>
                    )}
                  </div>
                  {ev.verified != null && (
                    <span className={`badge ${ev.verified ? 'badge-emerald' : 'badge-rose'}`} style={{ fontSize: '0.6rem' }}>
                      {ev.verified ? '✓ Verified' : '? Unverified'}
                    </span>
                  )}
                </div>

                {isSelected && (
                  <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.3rem', fontSize: '0.65rem' }} className="animate-fade">
                    {ev.description && <div style={{ color: 'var(--text-muted)' }}>{ev.description}</div>}
                    {ev.timestamp && <div style={{ color: 'var(--text-dim)' }}>🕐 {new Date(ev.timestamp).toLocaleString()}</div>}
                    {ev.source && <div style={{ color: 'var(--text-dim)' }}>Source: {ev.source}</div>}
                    {ev.claims?.length > 0 && (
                      <div style={{ marginTop: 4 }}>
                        <span style={{ color: 'var(--text-muted)', fontWeight: 700 }}>Claims: </span>
                        {ev.claims.join(', ')}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Analysis results */}
      {analysis && (
        <div>
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
            Analysis Results
          </div>

          {Object.keys(reqFulfill).length > 0 && (
            <div style={{ marginBottom: '0.6rem' }}>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginBottom: 4 }}>Requirements</div>
              {Object.entries(reqFulfill).slice(0, 4).map(([req, data]) => {
                const fulfilled = data?.status === 'Fulfilled';
                return (
                  <div key={req} style={{ display: 'flex', gap: '0.4rem', marginBottom: 3, fontSize: '0.65rem', alignItems: 'flex-start' }}>
                    <span style={{ color: fulfilled ? '#10b981' : '#ef4444', flexShrink: 0, fontWeight: 700 }}>{fulfilled ? '✓' : '✗'}</span>
                    <span style={{ color: '#c7d2fe' }}>{req}</span>
                    {data?.gap && <span style={{ color: 'var(--text-dim)', fontSize: '0.6rem' }}>— {data.gap}</span>}
                  </div>
                );
              })}
            </div>
          )}

          {Object.keys(kpiFulfill).length > 0 && (
            <div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginBottom: 4 }}>KPIs</div>
              {Object.entries(kpiFulfill).slice(0, 3).map(([kpi, data]) => (
                <div key={kpi} style={{ display: 'flex', gap: '0.4rem', marginBottom: 3, fontSize: '0.65rem', alignItems: 'flex-start' }}>
                  <span style={{ color: data?.achieved ? '#10b981' : '#f59e0b', flexShrink: 0 }}>{data?.achieved ? '✓' : '△'}</span>
                  <span style={{ color: '#c7d2fe' }}>{kpi}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
