import React from 'react';
import { TrendingUp, Layers, CheckCircle2, XCircle, ShieldCheck, Compass } from 'lucide-react';

export default function StartupPerformanceMatrix({ profile }) {
  if (!profile) return null;

  const pitchScore = profile.initial_pitch_score || 85.0;
  const execScore = profile.demonstrated_execution_score || 0.0;
  const domainVector = profile.domain_relevance_vector || {};

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <TrendingUp size={18} style={{ color: 'var(--accent-emerald)' }} />
            Dynamic Contextual Startup Performance
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Contextual ranking engine &bull; Distinguishes Pitch Capability vs Actual Demonstrated Execution
          </p>
        </div>
        <span className="badge badge-emerald">{profile.primary_domain} Core</span>
      </div>

      {/* Pitch Capability vs Demonstrated Execution Dual Metric Display */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        {/* Initial Pitch Score */}
        <div style={{ background: 'rgba(255, 255, 255, 0.02)', borderRadius: '12px', padding: '0.85rem', border: '1px solid var(--border-color)', textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>
            Initial Pitch Capability
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--accent-purple)', fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
            {pitchScore} <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>/ 100</span>
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', marginTop: '0.1rem' }}>Pitch deck & preliminary evaluation</div>
        </div>

        {/* Demonstrated Execution Score */}
        <div style={{ background: 'rgba(16, 185, 129, 0.06)', borderRadius: '12px', padding: '0.85rem', border: '1px solid rgba(16, 185, 129, 0.25)', textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--accent-emerald)', textTransform: 'uppercase', fontWeight: '700' }}>
            Demonstrated Execution
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
            {execScore > 0 ? execScore : '--'} <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>/ 100</span>
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>
            {profile.historical_milestones_completed} Passed &bull; {profile.historical_milestones_failed} Failed
          </div>
        </div>
      </div>

      {/* Contextual Domain Relevance Ranking Vector */}
      <div>
        <h4 style={{ fontSize: '0.78rem', fontWeight: '700', color: 'var(--text-main)', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <Compass size={14} style={{ color: 'var(--accent-cyan)' }} />
          Domain Relevance Contextual Scores (Non-Universal Ranking)
        </h4>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.65rem' }}>
          Evaluates competence relative to domain context (No flat universal leaderboard)
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {Object.keys(domainVector).length > 0 ? (
            Object.entries(domainVector).map(([domName, domScore]) => (
              <div key={domName} style={{ fontSize: '0.74rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                  <span style={{ color: domName === profile.primary_domain ? '#fff' : 'var(--text-muted)', fontWeight: domName === profile.primary_domain ? '700' : '500' }}>
                    {domName} {domName === profile.primary_domain ? '(Core Domain)' : ''}
                  </span>
                  <span style={{ fontWeight: '700', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{domScore}</span>
                </div>
                <div style={{ height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ width: `${domScore}%`, height: '100%', background: domName === profile.primary_domain ? 'linear-gradient(90deg, var(--accent-cyan), var(--accent-primary))' : 'rgba(255,255,255,0.2)' }}></div>
                </div>
              </div>
            ))
          ) : (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Domain relevance score updates after milestone execution</div>
          )}
        </div>
      </div>

      {/* Performance Rule Reminder */}
      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', borderTop: '1px solid var(--border-color)', paddingTop: '0.6rem', fontStyle: 'italic' }}>
        * Rule: Performance profile improves or decreases strictly based on actual demonstrated execution evidence.
      </div>
    </div>
  );
}
