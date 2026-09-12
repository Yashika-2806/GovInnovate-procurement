import React from 'react';
import Plot from 'react-plotly.js';

export default function RiskGauge({ score, riskLevel }) {
  let color = '#22c55e'; // green
  if (score > 20) color = '#3b82f6'; // blue
  if (score > 40) color = '#eab308'; // yellow
  if (score > 60) color = '#f97316'; // orange
  if (score > 80) color = '#ef4444'; // red

  return (
    <div className="flex flex-col items-center">
      <Plot
        data={[
          {
            type: 'indicator',
            mode: 'gauge+number',
            value: score,
            number: { font: { color: 'white', size: 48 } },
            gauge: {
              axis: { range: [0, 100], tickwidth: 1, tickcolor: 'gray' },
              bar: { color: 'white', thickness: 0.2 },
              bgcolor: 'rgba(0,0,0,0)',
              borderwidth: 0,
              steps: [
                { range: [0, 20], color: '#22c55e' },
                { range: [20, 40], color: '#3b82f6' },
                { range: [40, 60], color: '#eab308' },
                { range: [60, 80], color: '#f97316' },
                { range: [80, 100], color: '#ef4444' }
              ]
            }
          }
        ]}
        layout={{
          width: 350,
          height: 250,
          margin: { t: 30, b: 30, l: 30, r: 30 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: 'white' }
        }}
        config={{ displayModeBar: false, responsive: true }}
      />
      <div className="text-xl font-bold uppercase tracking-wider" style={{ color }}>
        {riskLevel}
      </div>
    </div>
  );
}
