import React from 'react';

const STATUS_META = {
  Pending:             { color: '#94a3b8', bg: 'rgba(148,163,184,0.1)', icon: '○' },
  'In Progress':       { color: '#6366f1', bg: 'rgba(99,102,241,0.12)', icon: '◷' },
  Submitted:           { color: '#22d3ee', bg: 'rgba(34,211,238,0.1)',  icon: '↑' },
  'Under Review':      { color: '#a78bfa', bg: 'rgba(167,139,250,0.1)', icon: '⧖' },
  Passed:              { color: '#10b981', bg: 'rgba(16,185,129,0.1)',  icon: '✓' },
  Failed:              { color: '#ef4444', bg: 'rgba(239,68,68,0.1)',   icon: '✗' },
  'Requires Remediation': { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', icon: '⚠' },
  Blocked:             { color: '#6b7280', bg: 'rgba(107,114,128,0.1)', icon: '⊘' },
};

const PHASE_COLORS = ['#6366f1','#22d3ee','#8b5cf6','#f59e0b','#10b981','#ef4444'];

export default function MilestoneLifecycleBoard({ milestones = [], onSelect, selectedId, evaluationResult }) {
  const currentMilestone = evaluationResult?.milestone;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
      {milestones.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)', fontSize: '0.78rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🏁</div>
          No milestones yet. Select a startup sample to load milestones.
        </div>
      )}
      {milestones.map((m, idx) => {
        const isSelected  = selectedId === m.id;
        const isCurrent   = currentMilestone?.id === m.id;
        const meta        = STATUS_META[m.status] ?? STATUS_META['Pending'];
        const phaseColor  = PHASE_COLORS[idx % PHASE_COLORS.length];
        const score       = isCurrent ? evaluationResult?.score?.total_weighted_score : null;

        return (
          <div
            key={m.id}
            onClick={() => onSelect(m)}
            style={{
              border: `1px solid ${isSelected ? phaseColor : isCurrent ? phaseColor+'60' : 'var(--border-color)'}`,
              borderLeft: `3px solid ${phaseColor}`,
              borderRadius: 12, padding: '0.65rem 0.75rem',
              background: isSelected ? `${phaseColor}12` : 'rgba(255,255,255,0.02)',
              cursor: 'pointer',
              transition: 'all 0.25s ease',
              display: 'flex', flexDirection: 'column', gap: '0.35rem',
            }}
          >
            {/* Header row */}
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
              <div style={{
                width: 24, height: 24, borderRadius: 6, flexShrink: 0,
                background: `${phaseColor}20`, border: `1px solid ${phaseColor}50`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.65rem', fontWeight: 800, color: phaseColor,
              }}>
                {idx + 1}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f1f5f9', marginBottom: 2, lineHeight: 1.2 }}>
                  {m.name}
                </div>
                <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)', display: '-webkit-box', WebkitLineClamp: 1, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {m.objective}
                </div>
              </div>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 3,
                background: meta.bg, border: `1px solid ${meta.color}40`,
                borderRadius: 9999, padding: '0.15rem 0.45rem',
                fontSize: '0.62rem', fontWeight: 700, color: meta.color,
                flexShrink: 0,
              }}>
                {meta.icon} {m.status}
              </div>
            </div>

            {/* KPI row */}
            {m.kpis?.length > 0 && (
              <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                {m.kpis.slice(0, 3).map((kpi, ki) => (
                  <span key={ki} style={{
                    fontSize: '0.6rem', padding: '0.1rem 0.4rem',
                    background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 5, color: 'var(--text-muted)',
                  }}>
                    {typeof kpi === 'string' ? kpi : kpi.metric ?? 'KPI'}
                  </span>
                ))}
                {m.kpis.length > 3 && (
                  <span style={{ fontSize: '0.6rem', color: 'var(--text-dim)' }}>+{m.kpis.length - 3}</span>
                )}
              </div>
            )}

            {/* Score bar if evaluated */}
            {isCurrent && score != null && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.62rem', color: 'var(--text-muted)', marginBottom: 3 }}>
                  <span>Evaluation Score</span>
                  <span style={{ color: score >= 70 ? '#10b981' : '#ef4444', fontWeight: 700 }}>{score.toFixed(1)}/100</span>
                </div>
                <div className="prog-bar">
                  <div className="prog-fill" style={{
                    width: `${score}%`,
                    background: score >= 70
                      ? 'linear-gradient(90deg, #10b981, #34d399)'
                      : 'linear-gradient(90deg, #ef4444, #f97316)',
                  }} />
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
