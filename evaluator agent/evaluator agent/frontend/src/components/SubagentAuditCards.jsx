import React, { useState } from 'react';

const SUBAGENT_META = {
  security: { icon: '🛡️', label: 'Security Auditor', color: '#ef4444', bg: 'rgba(239,68,68,0.08)' },
  telemetry: { icon: '📡', label: 'Telemetry Analyst', color: '#10b981', bg: 'rgba(16,185,129,0.08)' },
  escrow: { icon: '💰', label: 'Escrow Controller', color: '#f59e0b', bg: 'rgba(245,158,11,0.08)' },
};

function SecurityCard({ data }) {
  const [open, setOpen] = useState(false);
  const meta = SUBAGENT_META.security;
  if (!data) return null;
  const vulnCount = data.vulnerabilities?.length ?? 0;
  const compCount = data.compliance_frameworks?.length ?? 0;

  return (
    <div className="glass" style={{ border: `1px solid ${meta.color}25`, overflow: 'hidden' }}>
      <div
        style={{ padding: '0.75rem 1rem', cursor: 'pointer', background: meta.bg, display: 'flex', alignItems: 'center', gap: '0.6rem' }}
        onClick={() => setOpen(o => !o)}
      >
        <span style={{ fontSize: '1.2rem' }}>{meta.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: meta.color }}>{meta.label}</div>
          <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)' }}>
            {vulnCount} vulnerabilities · Risk: {data.overall_risk_level ?? 'N/A'}
          </div>
        </div>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
      </div>

      {open && (
        <div style={{ padding: '0.75rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }} className="animate-fade">
          {/* Risk Level */}
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, padding: '0.45rem 0.75rem', flex: 1 }}>
              <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>RISK LEVEL</div>
              <div style={{ fontSize: '1rem', fontWeight: 800, color: '#fca5a5', marginTop: 2 }}>{data.overall_risk_level ?? 'N/A'}</div>
            </div>
            <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 8, padding: '0.45rem 0.75rem', flex: 1 }}>
              <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>COMPLIANCE</div>
              <div style={{ fontSize: '1rem', fontWeight: 800, color: '#6ee7b7', marginTop: 2 }}>{compCount} frameworks</div>
            </div>
          </div>

          {/* Vulnerabilities */}
          {vulnCount > 0 && (
            <div>
              <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Vulnerabilities</div>
              {data.vulnerabilities.map((v, i) => (
                <div key={i} className="audit-row" style={{ marginBottom: 4 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#f1f5f9', fontWeight: 600 }}>{v.type}</span>
                    <span style={{ background: 'rgba(239,68,68,0.15)', borderRadius: 4, padding: '1px 6px', color: '#fca5a5', fontWeight: 700, fontSize: '0.6rem' }}>{v.severity}</span>
                  </div>
                  <div style={{ color: 'var(--text-muted)', marginTop: 3 }}>{v.description}</div>
                </div>
              ))}
            </div>
          )}

          {/* Compliance frameworks */}
          {compCount > 0 && (
            <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
              {data.compliance_frameworks.map((f, i) => (
                <span key={i} className="badge badge-emerald">{f}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TelemetryCard({ data }) {
  const [open, setOpen] = useState(false);
  const meta = SUBAGENT_META.telemetry;
  if (!data) return null;
  const anomalies = data.anomalies ?? [];
  const slos = data.slo_assessments ?? {};
  const sloKeys = Object.keys(slos);

  return (
    <div className="glass" style={{ border: `1px solid ${meta.color}25`, overflow: 'hidden' }}>
      <div
        style={{ padding: '0.75rem 1rem', cursor: 'pointer', background: meta.bg, display: 'flex', alignItems: 'center', gap: '0.6rem' }}
        onClick={() => setOpen(o => !o)}
      >
        <span style={{ fontSize: '1.2rem' }}>{meta.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: meta.color }}>{meta.label}</div>
          <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)' }}>
            {anomalies.length} anomalies · {sloKeys.length} SLOs monitored
          </div>
        </div>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
      </div>

      {open && (
        <div style={{ padding: '0.75rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }} className="animate-fade">
          {sloKeys.length > 0 && (
            <div>
              <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase' }}>SLO Status</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
                {sloKeys.map(key => {
                  const slo = slos[key];
                  const met = slo?.met ?? false;
                  return (
                    <div key={key} style={{ background: met ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)', border: `1px solid ${met ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`, borderRadius: 8, padding: '0.45rem 0.6rem' }}>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{key.replace(/_/g, ' ')}</div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 700, color: met ? '#6ee7b7' : '#fca5a5', marginTop: 2 }}>
                        {met ? '✓ Met' : '✗ Breached'}
                      </div>
                      {slo?.value != null && (
                        <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginTop: 1 }}>
                          {slo.value}{slo.unit ?? ''} / {slo.threshold ?? 'N/A'}{slo.unit ?? ''}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {anomalies.length > 0 && (
            <div>
              <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Anomalies</div>
              {anomalies.map((a, i) => (
                <div key={i} className="audit-row" style={{ marginBottom: 4 }}>
                  <div style={{ color: '#f59e0b', fontWeight: 600 }}>{a.type ?? a.metric}</div>
                  <div style={{ color: 'var(--text-muted)', marginTop: 2 }}>{a.description ?? a.detail}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function EscrowCard({ data }) {
  const [open, setOpen] = useState(false);
  const meta = SUBAGENT_META.escrow;
  if (!data) return null;

  return (
    <div className="glass" style={{ border: `1px solid ${meta.color}25`, overflow: 'hidden' }}>
      <div
        style={{ padding: '0.75rem 1rem', cursor: 'pointer', background: meta.bg, display: 'flex', alignItems: 'center', gap: '0.6rem' }}
        onClick={() => setOpen(o => !o)}
      >
        <span style={{ fontSize: '1.2rem' }}>{meta.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: meta.color }}>{meta.label}</div>
          <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)' }}>
            ${(data.disbursement_amount ?? 0).toLocaleString()} · {data.disbursement_status ?? 'N/A'}
          </div>
        </div>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
      </div>

      {open && (
        <div style={{ padding: '0.75rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }} className="animate-fade">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
            {[
              { label: 'Total Contract', value: `$${(data.total_contract_value ?? 0).toLocaleString()}`, color: '#c7d2fe' },
              { label: 'Disbursable',    value: `$${(data.disbursement_amount ?? 0).toLocaleString()}`,  color: '#fcd34d' },
              { label: 'Milestone %',   value: `${data.milestone_percentage ?? 0}%`,                    color: '#a78bfa' },
              { label: 'Status',        value: data.disbursement_status ?? 'N/A',                       color: data.disbursement_status === 'Approved' ? '#6ee7b7' : '#fca5a5' },
            ].map(item => (
              <div key={item.label} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, padding: '0.45rem 0.6rem' }}>
                <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{item.label}</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: item.color, marginTop: 2 }}>{item.value}</div>
              </div>
            ))}
          </div>

          {data.conditions_for_release?.length > 0 && (
            <div>
              <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Release Conditions</div>
              {data.conditions_for_release.map((c, i) => (
                <div key={i} style={{ display: 'flex', gap: '0.4rem', fontSize: '0.68rem', color: '#c7d2fe', marginBottom: 3 }}>
                  <span style={{ color: '#f59e0b' }}>→</span>{c}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function SubagentAuditCards({ security, telemetry, escrow }) {
  if (!security && !telemetry && !escrow) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-dim)', fontSize: '0.78rem' }}>
        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🤖</div>
        Specialist subagents will appear here after evaluation
      </div>
    );
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
      <SecurityCard data={security} />
      <TelemetryCard data={telemetry} />
      <EscrowCard data={escrow} />
    </div>
  );
}
