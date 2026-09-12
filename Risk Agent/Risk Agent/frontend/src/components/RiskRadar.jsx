import React from 'react';
import Plot from 'react-plotly.js';

export default function RiskRadar({ categoryScores }) {
  if (!categoryScores || categoryScores.length === 0) return null;

  const categories = categoryScores.map(c => c.category);
  // close the loop
  categories.push(categories[0]);
  
  const scores = categoryScores.map(c => c.score);
  scores.push(scores[0]);

  return (
    <div className="w-full h-full relative">
      <Plot
        data={[
          {
            type: 'scatterpolar',
            r: scores,
            theta: categories,
            fill: 'toself',
            name: 'Risk Profile',
            line: { color: '#8b5cf6' },
            fillcolor: 'rgba(139, 92, 246, 0.4)'
          }
        ]}
        layout={{
          autosize: true,
          margin: { t: 40, b: 40, l: 40, r: 40 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#d1d5db', size: 10 },
          polar: {
            radialaxis: {
              visible: true,
              range: [0, 100],
              color: '#4b5563',
              gridcolor: '#374151'
            },
            angularaxis: {
              color: '#9ca3af',
              gridcolor: '#374151'
            },
            bgcolor: 'transparent'
          },
          showlegend: false
        }}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
        config={{ displayModeBar: false, responsive: true }}
      />
    </div>
  );
}
