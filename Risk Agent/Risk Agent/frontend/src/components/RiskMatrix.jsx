import React from 'react';
import Plot from 'react-plotly.js';

export default function RiskMatrix({ riskItems }) {
  if (!riskItems) return null;

  const x = riskItems.map(item => item.impact);
  const y = riskItems.map(item => item.probability);
  const text = riskItems.map(item => item.name);
  const colors = riskItems.map(item => {
    const sev = item.severity || (item.impact * item.probability);
    if (sev <= 6) return '#22c55e';
    if (sev <= 12) return '#eab308';
    return '#ef4444';
  });

  return (
    <div className="w-full h-full">
      <Plot
        data={[
          {
            z: [
              [1, 2, 3, 4, 5],
              [2, 4, 6, 8, 10],
              [3, 6, 9, 12, 15],
              [4, 8, 12, 16, 20],
              [5, 10, 15, 20, 25]
            ],
            type: 'heatmap',
            colorscale: [
              [0, '#14532d'],   // dark green
              [0.5, '#854d0e'], // dark yellow
              [1, '#7f1d1d']    // dark red
            ],
            showscale: false,
            hoverinfo: 'none',
            opacity: 0.6
          },
          {
            x: x.map(val => val - 0.5), // offset for grid center
            y: y.map(val => val - 0.5),
            text: text,
            mode: 'markers+text',
            type: 'scatter',
            textposition: 'top center',
            textfont: { color: 'white', size: 10 },
            marker: {
              size: 12,
              color: colors,
              line: { color: 'white', width: 1 }
            },
            hoverinfo: 'text'
          }
        ]}
        layout={{
          autosize: true,
          margin: { t: 20, b: 40, l: 40, r: 20 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#d1d5db' },
          xaxis: { 
            title: 'Impact', 
            range: [0, 5], 
            tickvals: [0.5, 1.5, 2.5, 3.5, 4.5], 
            ticktext: ['1', '2', '3', '4', '5'],
            gridcolor: 'rgba(255,255,255,0.1)'
          },
          yaxis: { 
            title: 'Probability', 
            range: [0, 5], 
            tickvals: [0.5, 1.5, 2.5, 3.5, 4.5], 
            ticktext: ['1', '2', '3', '4', '5'],
            gridcolor: 'rgba(255,255,255,0.1)'
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
