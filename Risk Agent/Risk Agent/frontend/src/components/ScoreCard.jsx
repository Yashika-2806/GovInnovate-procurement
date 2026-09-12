import React, { useState } from 'react';

export default function ScoreCard({ categoryScore }) {
  const [expanded, setExpanded] = useState(false);
  
  if (!categoryScore) {
    return <div className="p-4 border border-gray-700 bg-gray-800 rounded-xl text-gray-500">No data available</div>;
  }

  const {
    category = 'Unknown',
    score = 0,
    confidence = 'LOW',
    sub_factors = [],
    explanation = '',
    evidence = [],
    comparable_failures = [],
    impact = '',
    probability = '',
    mitigation = ''
  } = categoryScore;

  const getRiskColor = (s) => {
    if (s <= 20) return 'border-green-500 text-green-400 bg-green-500/10';
    if (s <= 40) return 'border-blue-500 text-blue-400 bg-blue-500/10';
    if (s <= 60) return 'border-yellow-500 text-yellow-400 bg-yellow-500/10';
    if (s <= 80) return 'border-orange-500 text-orange-400 bg-orange-500/10';
    return 'border-red-500 text-red-400 bg-red-500/10';
  };

  const getRiskBorder = (s) => {
    if (s <= 20) return 'border-l-green-500';
    if (s <= 40) return 'border-l-blue-500';
    if (s <= 60) return 'border-l-yellow-500';
    if (s <= 80) return 'border-l-orange-500';
    return 'border-l-red-500';
  };

  const getConfidenceBadge = (c) => {
    const conf = (c || '').toUpperCase();
    if (conf === 'HIGH') return 'bg-green-500/20 text-green-400 border-green-500/30';
    if (conf === 'MEDIUM') return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    return 'bg-red-500/20 text-red-400 border-red-500/30';
  };

  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-xl overflow-hidden border-l-4 ${getRiskBorder(score)}`}>
      <div 
        className="p-4 cursor-pointer hover:bg-gray-800/50 flex justify-between items-center"
        onClick={() => setExpanded(!expanded)}
      >
        <div>
          <h3 className="text-xl font-bold text-white mb-1">{category}</h3>
          <div className="flex space-x-2">
            <span className={`px-2 py-0.5 text-xs font-semibold rounded border ${getRiskColor(score)}`}>
              Score: {score}
            </span>
            <span className={`px-2 py-0.5 text-xs font-semibold rounded border ${getConfidenceBadge(confidence)}`}>
              Confidence: {confidence}
            </span>
          </div>
        </div>
        <div className="text-3xl font-black text-gray-300 mr-4">
          {score}
        </div>
      </div>
      
      {expanded && (
        <div className="p-4 border-t border-gray-800 bg-gray-800/20">
          <p className="text-gray-300 mb-4">{explanation}</p>
          
          {sub_factors && sub_factors.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-bold text-gray-400 uppercase mb-2">Sub Factors</h4>
              <div className="grid grid-cols-1 gap-2">
                {sub_factors.map((sf, idx) => (
                  <div key={idx} className="flex justify-between p-2 bg-gray-900 rounded border border-gray-700 text-sm text-gray-300">
                    <span>{sf.name}</span>
                    <span>{sf.score}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {evidence && evidence.length > 0 && (
              <div>
                <h4 className="text-sm font-bold text-gray-400 uppercase mb-2">Evidence</h4>
                <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
                  {evidence.map((ev, i) => <li key={i}>{ev}</li>)}
                </ul>
              </div>
            )}
            
            {comparable_failures && comparable_failures.length > 0 && (
              <div>
                <h4 className="text-sm font-bold text-gray-400 uppercase mb-2">Comparable Failures</h4>
                <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
                  {comparable_failures.map((cf, i) => <li key={i}>{cf}</li>)}
                </ul>
              </div>
            )}
          </div>
          
          <div className="bg-gray-900 p-3 rounded border border-gray-700 text-sm text-gray-300">
            <div className="mb-2"><strong className="text-gray-400">Impact:</strong> {impact}</div>
            <div className="mb-2"><strong className="text-gray-400">Probability:</strong> {probability}</div>
            <div><strong className="text-gray-400">Mitigation:</strong> {mitigation}</div>
          </div>
        </div>
      )}
    </div>
  );
}
