import React, { useState } from 'react';

/* ─────────────────────────────────────────────────────────────────────────────
   Scoring Criteria: full definitions sourced from state.py + nodes.py
───────────────────────────────────────────────────────────────────────────── */
const CRITERIA_META = [
  {
    key: 'requirement_completion_score',
    label: 'Requirement Completion',
    weight: 0.25,
    color: '#6366f1',
    icon: '📋',
    short: 'Did the startup fulfil every stated milestone requirement?',
    how: 'The agent counts how many of the milestone\'s defined requirements have at least one piece of verified evidence that satisfies them. Score = (fulfilled ÷ total requirements) × 100.',
    drivers_up: [
      'Every listed requirement has matching, verified evidence',
      'Evidence ties directly to the requirement text',
      'Independent or system-generated verification',
    ],
    drivers_down: [
      'Requirements with no evidence at all',
      'Only self-reported evidence with no cross-verification',
      'Evidence doesn\'t match the requirement claim',
    ],
    formula: 'fulfilled_reqs / total_reqs × 100',
    example: '3 of 4 requirements met → 75.0',
  },
  {
    key: 'kpi_achievement_score',
    label: 'KPI Achievement',
    weight: 0.20,
    color: '#22d3ee',
    icon: '📈',
    short: 'Did the startup hit every measurable KPI target?',
    how: 'For each KPI, the agent checks if actual_value ≥ target_value. The actual value is either stated in the KPI definition or extracted directly from the evidence payload. Score = (achieved KPIs ÷ total KPIs) × 100.',
    drivers_up: [
      'Actual metric value meets or exceeds target',
      'KPI value is embedded in verified evidence payload',
      'All KPIs measured and reported',
    ],
    drivers_down: [
      'Actual value below target',
      'No evidence payload containing the KPI metric',
      'KPI actual_value is null (no data found)',
    ],
    formula: 'achieved_kpis / total_kpis × 100',
    example: 'KPI target 98% reliability, actual 99.4% → achieved ✓',
  },
  {
    key: 'technical_quality_score',
    label: 'Technical Quality',
    weight: 0.15,
    color: '#8b5cf6',
    icon: '⚙️',
    short: 'How well-engineered is the technical implementation?',
    how: 'Built from signals found inside evidence payloads. Software: CI/CD status (PASS=90, FAIL=40), test coverage %, code review depth, PR count. Hardware: inspection grade (A=85, B=70), GPS verification, telemetry packet quality. Average of all signals collected.',
    drivers_up: [
      'CI/CD pipeline passing (GREEN)',
      'Third-party inspection grade A or B',
      'High test coverage (>80%)',
      'GPS & telemetry independently verified',
    ],
    drivers_down: [
      'CI/CD failing or absent',
      'Low inspection grade or no audit report',
      'Template-only repository with 1 commit',
      'Telemetry self-reported only',
    ],
    formula: 'avg(tech_quality_signals[])',
    example: 'CI/CD PASS + coverage 89% → ~90',
  },
  {
    key: 'evidence_quality_score',
    label: 'Evidence Quality',
    weight: 0.15,
    color: '#a78bfa',
    icon: '🔍',
    short: 'How trustworthy and independently verified is the submitted evidence?',
    how: 'Each evidence item has a verification_level that maps to a trust multiplier. The average trust across all evidence items × 100 is the score. Trust levels: Self-reported = 0.30, System-generated = 0.60, Third-party = 0.85, Independently verified = 1.00.',
    drivers_up: [
      'Evidence verified by independent third party',
      'System-generated logs (Git, AWS, CI) — automatic trust 0.60',
      'Bureau Veritas / auditor sign-off — trust 0.85–1.00',
    ],
    drivers_down: [
      'Self-reported only (startup says it themselves) — trust 0.30',
      'No verification level stated',
      'Single piece of evidence for multiple requirements',
    ],
    formula: 'avg(trust_multiplier[]) × 100',
    example: 'Third-party (0.85) + System (0.60) → avg 0.725 → 72.5',
    scale: [
      { range: '90–100', label: 'Independently Verified', color: '#10b981' },
      { range: '75–89',  label: 'Third-party Audited',    color: '#22d3ee' },
      { range: '50–74',  label: 'System-generated Logs',  color: '#f59e0b' },
      { range: '0–49',   label: 'Self-reported Only',     color: '#ef4444' },
    ],
  },
  {
    key: 'testing_validation_score',
    label: 'Testing & Validation',
    weight: 0.10,
    color: '#10b981',
    icon: '🧪',
    short: 'Is the solution adequately tested with measurable coverage?',
    how: 'For Software: extracted from test_coverage_percent in the evidence payload. For Hardware: derived from telemetry validation completeness and independent inspection scores. Falls back to (req_ratio × 70) if no test signal found.',
    drivers_up: [
      'test_coverage_percent > 75% in evidence payload',
      'CI test suite passes all checks',
      'Hardware passed third-party inspection',
    ],
    drivers_down: [
      'No test suite present',
      'Coverage below 50%',
      'Template repo with zero test files',
    ],
    formula: 'avg(testing_signals[]) or req_ratio × 70',
    example: 'coverage 89.2% in payload → score ~89',
  },
  {
    key: 'documentation_score',
    label: 'Documentation',
    weight: 0.05,
    color: '#f59e0b',
    icon: '📝',
    short: 'Is the project properly documented for users and reviewers?',
    how: 'Software: checks readme_present and api_docs_present flags in the evidence payload. Each true = +50 points, averaged. Hardware: presence of user manuals, schematics, or inspection reports. Falls back to 60.0 if no documentation signals found.',
    drivers_up: [
      'README file present in repo',
      'OpenAPI / Swagger docs generated',
      'Hardware schematics or user manuals submitted',
    ],
    drivers_down: [
      'No README (readme_present: false)',
      'No API docs (api_docs_present: false)',
      'Bare repository with no documentation files',
    ],
    formula: 'avg(doc_signals[]) — README(+50) + API_docs(+50)',
    example: 'README ✓ + API docs ✓ → 100; only README → 50',
  },
  {
    key: 'practicality_score',
    label: 'Practicality',
    weight: 0.05,
    color: '#34d399',
    icon: '🔧',
    short: 'Is the solution practically deployable and real-world ready?',
    how: 'A threshold gate: if Requirement Completion ≥ 80%, practicality = 85 (solution demonstrably works in field/production). If < 80%, practicality = 60 (partial execution; real-world readiness questionable). Designed to penalize startups that pass KPIs on paper but miss core requirements.',
    drivers_up: [
      'Requirement Completion score ≥ 80%',
      'Evidence shows real-world deployment (not just lab/demo)',
    ],
    drivers_down: [
      'Requirement Completion < 80%',
      'Only proof-of-concept without field validation',
    ],
    formula: '85 if req_completion ≥ 80 else 60',
    example: 'Req Completion = 75% → Practicality = 60',
  },
  {
    key: 'delivery_timeliness_score',
    label: 'Delivery Timeliness',
    weight: 0.05,
    color: '#60a5fa',
    icon: '⏱️',
    short: 'Was the milestone delivered on schedule?',
    how: 'Compares evidence submission timestamps against the milestone schedule. Currently uses a simulated baseline of 95 (on-time by default). In production this would compare submission_date vs deadline_date; late submissions incur a penalty proportional to delay.',
    drivers_up: [
      'Evidence submitted before or on milestone deadline',
      'No extension requests in record',
    ],
    drivers_down: [
      'Evidence submitted significantly after deadline',
      'Multiple milestone deadline extensions granted',
    ],
    formula: '95 (simulated on-time baseline)',
    example: 'On-time delivery → 95 | Late by 2 weeks → ~70',
  },
];

/* ── Score ring SVG ── */
function ScoreRing({ score = 0, size = 100, strokeWidth = 9 }) {
  const r    = (size - strokeWidth) / 2;
  const circ = 2 * Math.PI * r;
  const pct  = Math.min(100, Math.max(0, score));
  const off  = circ - (pct / 100) * circ;
  const col  = pct >= 75 ? '#10b981' : pct >= 55 ? '#f59e0b' : '#ef4444';

  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)', flexShrink: 0 }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none"
        stroke="rgba(255,255,255,0.06)" strokeWidth={strokeWidth} />
      <circle cx={size/2} cy={size/2} r={r} fill="none"
        stroke={col} strokeWidth={strokeWidth} strokeLinecap="round"
        strokeDasharray={circ} strokeDashoffset={off}
        style={{ transition: 'stroke-dashoffset 1.1s cubic-bezier(.4,0,.2,1), stroke 0.5s' }} />
      <text x="50%" y="50%" textAnchor="middle" dominantBaseline="central"
        fill={col} fontSize={size < 90 ? 15 : 20} fontWeight={800}
        fontFamily="Plus Jakarta Sans,sans-serif"
        style={{ transform: 'rotate(90deg)', transformOrigin: 'center' }}>
        {pct.toFixed(0)}
      </text>
    </svg>
  );
}

/* ── Criterion card ── */
function CriterionCard({ meta, value, isExpanded, onToggle }) {
  const pct = Math.min(100, Math.max(0, value ?? 0));
  const hasValue = value != null;

  return (
    <div style={{
      border: `1px solid ${isExpanded ? meta.color + '55' : 'rgba(255,255,255,0.07)'}`,
      borderLeft: `3px solid ${meta.color}`,
      borderRadius: 12,
      background: isExpanded ? `${meta.color}09` : 'rgba(255,255,255,0.02)',
      overflow: 'hidden',
      transition: 'all 0.25s ease',
    }}>
      {/* Header row — always visible */}
      <div
        onClick={onToggle}
        style={{ padding: '0.65rem 0.85rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.65rem' }}
      >
        {/* Icon */}
        <div style={{ width: 32, height: 32, borderRadius: 8, flexShrink: 0,
          background: `${meta.color}18`, border: `1px solid ${meta.color}40`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem' }}>
          {meta.icon}
        </div>

        {/* Label + bar */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#e2e8f0' }}>{meta.label}</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexShrink: 0 }}>
              <span style={{ fontSize: '0.6rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                w={Math.round(meta.weight * 100)}%
              </span>
              {hasValue && (
                <span style={{ fontSize: '0.78rem', fontWeight: 800, color: meta.color }}>
                  {pct.toFixed(1)}
                </span>
              )}
              {!hasValue && <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>—</span>}
            </div>
          </div>
          {/* Progress bar */}
          <div style={{ height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 2,
              width: hasValue ? `${pct}%` : '0%',
              background: `linear-gradient(90deg, ${meta.color}80, ${meta.color})`,
              transition: 'width 0.9s cubic-bezier(.4,0,.2,1)',
            }} />
          </div>
          <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginTop: 3 }}>{meta.short}</div>
        </div>

        {/* Expand toggle */}
        <span style={{ color: 'var(--text-dim)', fontSize: '0.65rem', flexShrink: 0,
          transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
      </div>

      {/* Expanded detail panel */}
      {isExpanded && (
        <div style={{ padding: '0 0.85rem 0.85rem', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}
          className="animate-fade">

          {/* How it's computed */}
          <div style={{ background: 'rgba(0,0,0,0.25)', borderRadius: 8, padding: '0.65rem 0.75rem' }}>
            <div style={{ fontSize: '0.62rem', fontWeight: 800, color: meta.color, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 5 }}>
              How it's calculated
            </div>
            <div style={{ fontSize: '0.68rem', color: '#cbd5e1', lineHeight: 1.6 }}>{meta.how}</div>
          </div>

          {/* Formula chip */}
          <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: '0.5rem 0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Formula</span>
            <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: '#a78bfa', flex: 1 }}>{meta.formula}</code>
          </div>

          {/* Example */}
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', padding: '0 0.1rem' }}>
            <span style={{ color: '#64748b' }}>Example: </span>{meta.example}
          </div>

          {/* Trust scale (evidence quality only) */}
          {meta.scale && (
            <div>
              <div style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: 5 }}>Verification Trust Scale</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.3rem' }}>
                {meta.scale.map(s => (
                  <div key={s.range} style={{ background: `${s.color}12`, border: `1px solid ${s.color}35`, borderRadius: 7, padding: '0.35rem 0.5rem' }}>
                    <div style={{ fontSize: '0.62rem', fontWeight: 800, color: s.color }}>{s.range}</div>
                    <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginTop: 1 }}>{s.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Drivers */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.45rem' }}>
            <div>
              <div style={{ fontSize: '0.6rem', fontWeight: 700, color: '#10b981', textTransform: 'uppercase', marginBottom: 4 }}>↑ Score goes UP when</div>
              {meta.drivers_up.map((d, i) => (
                <div key={i} style={{ display: 'flex', gap: '0.3rem', fontSize: '0.63rem', color: '#6ee7b7', marginBottom: 3, alignItems: 'flex-start' }}>
                  <span style={{ flexShrink: 0 }}>✓</span>{d}
                </div>
              ))}
            </div>
            <div>
              <div style={{ fontSize: '0.6rem', fontWeight: 700, color: '#ef4444', textTransform: 'uppercase', marginBottom: 4 }}>↓ Score goes DOWN when</div>
              {meta.drivers_down.map((d, i) => (
                <div key={i} style={{ display: 'flex', gap: '0.3rem', fontSize: '0.63rem', color: '#fca5a5', marginBottom: 3, alignItems: 'flex-start' }}>
                  <span style={{ flexShrink: 0 }}>✗</span>{d}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Main exported component ── */
export default function ScoringJustificationConsole({ score, recommendations }) {
  const [expanded, setExpanded] = useState(null);
  const [showFormula, setShowFormula] = useState(false);

  const toggle = (key) => setExpanded(e => e === key ? null : key);

  const total   = score?.total_weighted_score ?? 0;
  const passed  = score?.passed;
  const thresh  = score?.pass_threshold ?? 75;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>

      {/* ── Overall score ring + status ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <ScoreRing score={total} size={104} />

        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: 3 }}>Overall Weighted Score</div>

          {score ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: 6 }}>
                <span style={{ fontSize: '0.72rem', padding: '0.22rem 0.65rem', borderRadius: 9999, fontWeight: 800,
                  background: passed ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                  color: passed ? '#6ee7b7' : '#fca5a5',
                  border: `1px solid ${passed ? 'rgba(16,185,129,0.35)' : 'rgba(239,68,68,0.35)'}` }}>
                  {passed ? '🎉 PASSED' : '❌ FAILED'}
                </span>
              </div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', lineHeight: 1.7 }}>
                Pass threshold: <span style={{ color: '#f59e0b', fontWeight: 700 }}>{thresh}/100</span><br/>
                {passed
                  ? <span style={{ color: '#6ee7b7' }}>Score is {(total - thresh).toFixed(1)} points above threshold.</span>
                  : <span style={{ color: '#fca5a5' }}>Need {(thresh - total).toFixed(1)} more points to pass.</span>}
              </div>
            </>
          ) : (
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
              Run evaluation to see score
            </div>
          )}
        </div>
      </div>

      {/* ── Formula banner (toggle) ── */}
      <div
        onClick={() => setShowFormula(f => !f)}
        style={{ background: 'rgba(99,102,241,0.07)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 10, padding: '0.55rem 0.75rem', cursor: 'pointer' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#a5b4fc' }}>∑ How the total score is computed</span>
          <span style={{ fontSize: '0.62rem', color: 'var(--text-dim)', transform: showFormula ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
        </div>

        {showFormula && (
          <div style={{ marginTop: '0.65rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }} className="animate-fade">
            <div style={{ fontSize: '0.63rem', color: '#94a3b8', lineHeight: 1.7 }}>
              All 8 criterion scores are multiplied by their weights, summed, then <strong style={{ color: '#c7d2fe' }}>normalized</strong> so they always add to 100 regardless of any manual weight edits.
            </div>
            <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', color: '#a78bfa', background: 'rgba(0,0,0,0.3)', padding: '0.45rem 0.6rem', borderRadius: 7, display: 'block', lineHeight: 1.8 }}>
              total = Σ(score_i × weight_i) / Σ(weight_i)<br/>
              total = min(100, round(total, 2))<br/>
              passed = total ≥ {thresh}
            </code>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.3rem', marginTop: 4 }}>
              {CRITERIA_META.map(c => (
                <div key={c.key} style={{ background: `${c.color}10`, border: `1px solid ${c.color}30`, borderRadius: 6, padding: '0.3rem 0.4rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.6rem', color: c.color, fontWeight: 800 }}>{Math.round(c.weight * 100)}%</div>
                  <div style={{ fontSize: '0.55rem', color: 'var(--text-dim)', lineHeight: 1.3 }}>{c.label.split(' ')[0]}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── 8 criterion cards ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>
          Score Breakdown — click any row to see full explanation
        </div>
        {CRITERIA_META.map(meta => (
          <CriterionCard
            key={meta.key}
            meta={meta}
            value={score?.[meta.key]}
            isExpanded={expanded === meta.key}
            onToggle={() => toggle(meta.key)}
          />
        ))}
      </div>

      {/* ── Recommendations ── */}
      {recommendations?.next_actions?.length > 0 && (
        <div>
          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
            💡 Recommended Next Actions
          </div>
          {recommendations.next_actions.map((a, i) => (
            <div key={i} style={{ display: 'flex', gap: '0.45rem', alignItems: 'flex-start', padding: '0.4rem 0.6rem', background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)', borderRadius: 8, marginBottom: 5, fontSize: '0.68rem', color: '#c7d2fe' }}>
              <span style={{ color: '#6366f1', fontWeight: 800, flexShrink: 0 }}>→</span>{a}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
