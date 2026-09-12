import React from 'react';

export default function CompanyCard({ company }) {
  if (!company) {
    return <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-xl text-gray-500">No data available</div>;
  }

  const {
    company_name = 'Unknown',
    similarity_score = 0,
    similarity_factors = [],
    outcome = 'UNKNOWN',
    key_comparison_points = [],
    industry = 'N/A',
    funding = 'N/A',
    business_model = 'N/A',
    years_operated = 'N/A'
  } = company;

  const getOutcomeBadge = (out) => {
    const o = String(out).toUpperCase();
    if (o === 'FAILED') return 'bg-red-500/20 text-red-400 border-red-500/30';
    if (o === 'SUCCEEDED') return 'bg-green-500/20 text-green-400 border-green-500/30';
    if (o === 'ACQUIRED') return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  };

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 hover:bg-gray-800 transition-colors">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-xl font-bold text-white">{company_name}</h3>
        <span className={`px-3 py-1 text-xs font-bold rounded-full border ${getOutcomeBadge(outcome)}`}>
          {outcome}
        </span>
      </div>
      
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1 text-gray-400">
          <span>Similarity</span>
          <span>{similarity_score}%</span>
        </div>
        <div className="w-full bg-gray-900 rounded-full h-2.5 border border-gray-700 overflow-hidden">
          <div className="bg-blue-500 h-2.5 rounded-full" style={{ width: `${similarity_score}%` }}></div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4 text-sm text-gray-300 bg-gray-900 p-3 rounded border border-gray-700">
        <div><span className="text-gray-500 text-xs block">Industry</span>{industry}</div>
        <div><span className="text-gray-500 text-xs block">Funding</span>{funding}</div>
        <div><span className="text-gray-500 text-xs block">Model</span>{business_model}</div>
        <div><span className="text-gray-500 text-xs block">Years Active</span>{years_operated}</div>
      </div>

      {similarity_factors && similarity_factors.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-bold text-gray-500 uppercase mb-2">Similarity Factors</div>
          <div className="flex flex-wrap gap-2">
            {similarity_factors.map((factor, i) => (
              <span key={i} className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
                {factor}
              </span>
            ))}
          </div>
        </div>
      )}

      {key_comparison_points && key_comparison_points.length > 0 && (
        <div>
          <div className="text-xs font-bold text-gray-500 uppercase mb-2">Key Differences / Points</div>
          <ul className="list-disc list-inside text-sm text-gray-400 space-y-1">
            {key_comparison_points.map((pt, i) => (
              <li key={i}>{pt}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
