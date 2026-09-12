import React from 'react';

export default function ScoreTable({ weightedScores, cumulativeScore }) {
  if (!weightedScores || weightedScores.length === 0) {
    return <div className="p-4 border border-gray-700 bg-gray-800 rounded-xl text-gray-500">No data available</div>;
  }

  const getRiskColor = (score) => {
    if (score <= 20) return 'text-green-400';
    if (score <= 40) return 'text-blue-400';
    if (score <= 60) return 'text-yellow-400';
    if (score <= 80) return 'text-orange-400';
    return 'text-red-400';
  };

  return (
    <div className="bg-gray-800/50 rounded-xl border border-gray-700 overflow-hidden shadow-lg mt-6 mb-6">
      <table className="w-full text-left text-sm text-gray-300">
        <thead className="bg-gray-900/80 text-xs uppercase text-gray-400 border-b border-gray-700">
          <tr>
            <th className="px-6 py-4">Risk Category</th>
            <th className="px-6 py-4">Score</th>
            <th className="px-6 py-4">Weight</th>
            <th className="px-6 py-4">Weighted Score</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700">
          {weightedScores.map((row, idx) => (
            <tr key={idx} className="hover:bg-gray-800/80 transition-colors">
              <td className="px-6 py-4 font-medium text-white">{row.category}</td>
              <td className={`px-6 py-4 font-bold ${getRiskColor(row.raw_score)}`}>{row.raw_score}</td>
              <td className="px-6 py-4 text-gray-400">{row.weight}</td>
              <td className={`px-6 py-4 font-bold ${getRiskColor(row.weighted_score)}`}>{row.weighted_score.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="bg-gray-900 font-bold text-white border-t-2 border-gray-600">
            <td colSpan="3" className="px-6 py-4 text-right">Cumulative Risk Score:</td>
            <td className={`px-6 py-4 text-lg ${getRiskColor(cumulativeScore)}`}>{Number(cumulativeScore).toFixed(2)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
