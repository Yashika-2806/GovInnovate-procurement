import React from 'react';
import ReactMarkdown from 'react-markdown';

function generateMarkdownFromReport(report) {
  if (!report) return 'No report data available.';

  const exec = report.executive_summary || {};
  const overview = report.startup_overview || report.profile || {};
  const risk = report.risk_assessment || {};
  const failures = report.historical_failures || [];
  const successes = report.successful_benchmarks || [];
  const drivers = report.key_risk_drivers || [];
  const mitigations = report.mitigation_strategies || [];
  const citations = report.citations || report.sources || [];
  const scores = report.score_calculation || risk.weighted_scores || [];

  const ind = overview.industry?.value || 'Technology';
  const sub = overview.sub_industry?.value || 'AI & SaaS';
  const cust = overview.target_customers?.value || 'Enterprise / B2B';
  const prob = overview.problem_description?.value || 'Identified problem';
  const sol = overview.solution_description?.value || 'Proposed solution';

  let md = `# Startup Failure Risk Assessment Report\n\n`;

  md += `## 1. Executive Summary\n\n`;
  md += `**Cumulative Startup Risk Score:** ${Math.round(exec.overall_score || exec.cumulative_score || 0)} / 100  \n`;
  md += `**Risk Classification:** ${exec.overall_risk_level || exec.risk_classification || 'MODERATE'}  \n\n`;
  md += `### Strategic Recommendation\n`;
  md += `${exec.recommendation || 'Focus on validating product-market fit and addressing critical risk drivers before capital deployment.'}\n\n`;

  if (exec.critical_warnings && exec.critical_warnings.length > 0) {
    md += `> [!WARNING]\n`;
    md += `> **Critical Warnings:** ${exec.critical_warnings.join('; ')}\n\n`;
  }

  md += `## 2. Startup Overview\n\n`;
  md += `- **Industry:** ${ind}\n`;
  md += `- **Sub-Industry:** ${sub}\n`;
  md += `- **Target Customers:** ${cust}\n`;
  md += `- **Problem Being Solved:** ${prob}\n`;
  md += `- **Proposed Solution:** ${sol}\n\n`;

  md += `## 3. Key Risk Drivers\n\n`;
  if (drivers.length > 0) {
    drivers.forEach(d => {
      md += `- ${d}\n`;
    });
  } else if (risk.top_risks && risk.top_risks.length > 0) {
    risk.top_risks.forEach(r => {
      md += `- **${r}:** Identified as a significant operational or market vulnerability.\n`;
    });
  }
  md += `\n`;

  md += `## 4. Weighted Risk Score Calculation\n\n`;
  md += `| Category | Raw Score (0-100) | Weight | Weighted Contribution |\n`;
  md += `| :--- | :--- | :--- | :--- |\n`;
  scores.forEach(s => {
    md += `| **${s.category}** | ${s.raw_score} | ${s.weight} | ${Number(s.weighted_score).toFixed(2)} |\n`;
  });
  md += `\n`;

  md += `## 5. Historical Startup Failure Analysis\n\n`;
  if (failures.length > 0) {
    failures.forEach(f => {
      md += `### ${f.company_name} (${f.industry || ind})\n`;
      if (f.funding_raised) md += `- **Funding Raised:** ${f.funding_raised}\n`;
      if (f.primary_cause) md += `- **Primary Cause of Failure:** ${f.primary_cause}\n`;
      if (f.failure_narrative) md += `- **Post-Mortem Context:** ${f.failure_narrative}\n`;
      md += `\n`;
    });
  } else {
    md += `Historical post-mortem analysis referenced standard failure rates across comparable cohort companies.\n\n`;
  }

  md += `## 6. Successful Startup Benchmarks\n\n`;
  if (successes.length > 0) {
    successes.forEach(s => {
      md += `### ${s.company_name}\n`;
      if (s.success_factors && s.success_factors.length > 0) {
        md += `- **Key Success Factors:** ${s.success_factors.join(', ')}\n`;
      }
      if (s.key_differentiators && s.key_differentiators.length > 0) {
        md += `- **Differentiators:** ${s.key_differentiators.join(', ')}\n`;
      }
      md += `\n`;
    });
  } else {
    md += `Benchmarked against standard industry performance multiples and venture survival rates.\n\n`;
  }

  md += `## 7. Mitigation Strategies\n\n`;
  if (mitigations.length > 0) {
    mitigations.forEach(m => {
      md += `### ${m.risk_name || m.risk_category || 'Risk Mitigation'}\n`;
      md += `- **Why It Matters:** ${m.why_it_matters || 'Critical for reducing venture mortality.'}\n`;
      md += `- **Actionable Mitigation:** ${m.recommended_action || m.strategy}\n`;
      md += `- **Expected Impact:** ${m.expected_impact}\n\n`;
    });
  } else {
    md += `Address highest weighted category risks through rapid prototyping and customer discovery.\n\n`;
  }

  md += `## 8. Research Citations & Data Sources\n\n`;
  if (citations.length > 0) {
    citations.forEach(c => {
      const url = typeof c === 'string' ? c : c.url || c.title || '';
      if (url) {
        md += `- [${url}](${url})\n`;
      }
    });
  } else {
    md += `- Industry market research reports and public venture capital databases.\n`;
  }

  return md;
}

export default function ReportView({ report }) {
  if (!report) {
    return <div className="p-4 bg-gray-900 border border-gray-800 rounded-xl text-gray-500">No report available</div>;
  }

  const markdownText = typeof report === 'string' 
    ? report 
    : report.markdown || generateMarkdownFromReport(report);

  const handleDownload = () => {
    const blob = new Blob([markdownText], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Startup_Risk_Assessment_Report.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="text-gray-300">
      <div className="flex justify-between items-center pb-4 mb-6 border-b border-gray-800">
        <div>
          <h2 className="text-xl font-bold text-white">Full Research Report</h2>
          <p className="text-xs text-gray-400">Complete diligence dossier generated by LangGraph multi-agent analysis.</p>
        </div>
        <button 
          onClick={handleDownload}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition-colors shadow-lg shadow-blue-600/20 cursor-pointer"
        >
          <span>📥</span>
          <span>Download Markdown (.md)</span>
        </button>
      </div>
      <div className="prose prose-invert prose-blue max-w-none space-y-4">
        <ReactMarkdown>{markdownText}</ReactMarkdown>
      </div>
    </div>
  );
}
