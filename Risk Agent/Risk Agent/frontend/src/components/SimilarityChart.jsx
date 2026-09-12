import React from 'react';
import Plot from 'react-plotly.js';

export default function SimilarityChart({ companies }) {
  if (!companies || companies.length === 0) {
    return <div className="flex h-full items-center justify-center text-gray-500">No data available</div>;
  }

  // Sort descending by similarity
  const sorted = [...companies].sort((a, b) => a.similarity_score - b.similarity_score);
  
  const names = sorted.map(c => c.company_name);
  const scores = sorted.map(c => c.similarity_score);
  
  const colors = sorted.map(c => {
    const outcome = String(c.outcome).toUpperCase();
    if (outcome === 'FAILED') return '#ef4444'; // red
    if (outcome === 'SUCCEEDED') return '#22c55e'; // green
    if (outcome === 'ACQUIRED') return '#3b82f6'; // blue
    return '#6b7280'; // gray
  });

  return (
    <Plot
      data={[{
        type: 'bar',
        x: scores,
        y: names,
        orientation: 'h',
        marker: { color: colors },
        text: scores.map(s => `${s}%`),
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
