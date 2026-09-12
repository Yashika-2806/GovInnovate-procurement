import React from 'react';
import Plot from 'react-plotly.js';

export default function RiskHeatmap({ data, xLabels, yLabels, title }) {
  if (!data || data.length === 0) {
    return <div className="flex h-full items-center justify-center text-gray-500">No data available</div>;
  }

  return (
    <Plot
      data={[{
        type: 'heatmap',
        z: data,
        x: xLabels,
        y: yLabels,
        colorscale: [
          [0, '#22c55e'],
          [0.25, '#3b82f6'],
          [0.5, '#eab308'],
          [0.75, '#f97316'],
          [1, '#ef4444']
        ],
        showscale: true,
      }]}
      layout={{
        title: { text: title || 'Risk Heatmap', font: { color: '#e5e7eb' } },
        autosize: true,
        margin: { l: 150, r: 50, t: 50, b: 50 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e5e7eb' },
      }}
      useResizeHandler={true}
      style={{ width: '100%', height: '100%' }}
      config={{ displayModeBar: false, responsive: true }}
    />
  );
}
