import React from 'react';
import Plot from 'react-plotly.js';

export default function RiskBarChart({ categoryScores }) {
  if (!categoryScores || categoryScores.length === 0) {
    return <div className="flex h-full items-center justify-center text-gray-500">No data available</div>;
  }

  const sortedScores = [...categoryScores].sort((a, b) => a.score - b.score);
  const categories = sortedScores.map(d => d.category);
  const scores = sortedScores.map(d => d.score);
  
  const colors = scores.map(score => {
    if (score <= 20) return '#22c55e'; // green
    if (score <= 40) return '#3b82f6'; // blue
    if (score <= 60) return '#eab308'; // yellow
    if (score <= 80) return '#f97316'; // orange
    return '#ef4444'; // red
  });

  return (
    <Plot
      data={[{
        type: 'bar',
        x: scores,
        y: categories,
        orientation: 'h',
        marker: { color: colors },
        text: scores.map(s => String(s)),
        textposition: 'auto',
      }]}
      layout={{
        autosize: true,
        margin: { l: 150, r: 20, t: 20, b: 40 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e5e7eb' },
        xaxis: { 
          range: [0, 100], 
          gridcolor: '#374151',
          zerolinecolor: '#374151' 
        },
        yaxis: { 
          autorange: true 
        }
      }}
      useResizeHandler={true}
      style={{ width: '100%', height: '100%' }}
      config={{ displayModeBar: false, responsive: true }}
    />
  );
}
