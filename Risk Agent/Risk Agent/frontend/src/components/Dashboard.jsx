import React from 'react';
import RiskGauge from './RiskGauge';
import RiskRadar from './RiskRadar';
import RiskMatrix from './RiskMatrix';
import RiskBarChart from './RiskBarChart';

export default function Dashboard({ results }) {
  if (!results) return null;
  const { overallScore, riskLevel, categoryScores, topRisks, matrixItems, stats } = results;

  return (
    <div className="space-y-6 pb-8">
      {/* Top Row: Gauge */}
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg flex flex-col items-center justify-center min-h-[300px]">
        <h2 className="text-xl font-bold text-gray-300 mb-2">Overall Risk Assessment</h2>
        <RiskGauge score={overallScore || 0} riskLevel={riskLevel || 'Unknown'} />
      </div>

      {/* Second Row: Radar + Top Risks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg">
          <h3 className="text-lg font-bold text-gray-300 mb-4">Risk Profile</h3>
          <div className="h-80">
            <RiskRadar categoryScores={categoryScores || []} />
          </div>
        </div>
        
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg flex flex-col">
          <h3 className="text-lg font-bold text-gray-300 mb-4">Top 5 Risk Factors</h3>
          <div className="flex-1 space-y-3 overflow-y-auto">
            {(topRisks || []).map((risk, i) => (
              <div key={i} className="p-3 bg-gray-950 rounded border border-gray-800 flex justify-between items-center">
                <span className="font-medium text-gray-200">{risk.name}</span>
                <span className={`px-2 py-1 text-xs font-bold rounded-full ${getBadgeColor(risk.score)}`}>
                  {risk.score} / 100
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Third Row: Matrix */}
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg">
        <h3 className="text-lg font-bold text-gray-300 mb-4">Risk Matrix (Probability × Impact)</h3>
        <div className="h-96">
          <RiskMatrix riskItems={matrixItems || []} />
        </div>
      </div>

      {/* Fourth Row: Bar Chart */}
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg">
        <h3 className="text-lg font-bold text-gray-300 mb-4">Risk Categories Breakdown</h3>
        <div className="h-96">
          <RiskBarChart categoryScores={categoryScores || []} />
        </div>
      </div>

      {/* Bottom: Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-900 p-4 rounded-xl border border-gray-800 text-center">
          <div className="text-sm text-gray-400">Total Sources Analyzed</div>
          <div className="text-2xl font-bold text-white">{stats?.sources || 0}</div>
        </div>
        <div className="bg-gray-900 p-4 rounded-xl border border-gray-800 text-center">
          <div className="text-sm text-gray-400">Data Quality</div>
          <div className="text-2xl font-bold text-white">{stats?.dataQuality || 'N/A'}</div>
        </div>
        <div className="bg-gray-900 p-4 rounded-xl border border-gray-800 text-center">
          <div className="text-sm text-gray-400">Confidence Score</div>
          <div className="text-2xl font-bold text-white">{stats?.confidence || 0}%</div>
        </div>
      </div>
    </div>
  );
}

function getBadgeColor(score) {
  if (score <= 20) return 'bg-green-500/20 text-green-400 border-green-500/30 border';
  if (score <= 40) return 'bg-blue-500/20 text-blue-400 border-blue-500/30 border';
  if (score <= 60) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30 border';
  if (score <= 80) return 'bg-orange-500/20 text-orange-400 border-orange-500/30 border';
  return 'bg-red-500/20 text-red-400 border-red-500/30 border';
}
