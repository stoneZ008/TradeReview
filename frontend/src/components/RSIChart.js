import ReactECharts from 'echarts-for-react';

export default function RSIChart({ stockData, symbol }) {
  if (!stockData?.data) return null;

  const data = stockData.data;
  const dates = data.map(d => d.date);

  const option = {
    backgroundColor: '#0f0f1a',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(26, 26, 46, 0.9)',
      borderColor: '#2a2a4a',
      textStyle: { color: '#fff' },
      formatter: function(params) {
        const date = params[0]?.axisValue;
        let html = `<div style="padding: 8px">
          <div style="font-weight: bold; margin-bottom: 4px">${stockData.name || ''} (${symbol})</div>
          <div style="font-size: 12px; color: #a0a0a0; margin-bottom: 8px">${date || ''}</div>`;
        params.forEach(p => {
          html += `<div>${p.seriesName}: ${p.data?.toFixed(2)}</div>`;
        });
        html += '</div>';
        return html;
      }
    },
    grid: { left: '10%', right: '5%', top: '12%', bottom: '15%' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#2a2a4a' } }
    },
    yAxis: {
      min: 0,
      max: 100,
      splitLine: { lineStyle: { color: '#2a2a4a' } }
    },
    dataZoom: [
      { type: 'inside', start: 50, end: 100 },
      { type: 'slider', bottom: 0, height: 20 }
    ],
    series: [
      {
        name: 'RSI',
        type: 'line',
        data: data.map(d => d.rsi),
        lineStyle: { color: '#a78bfa' },
        symbol: 'none',
        markLine: {
          data: [
            { yAxis: 70, lineStyle: { color: '#ef4444' } },
            { yAxis: 30, lineStyle: { color: '#22c55e' } }
          ]
        }
      }
    ]
  };

  return <ReactECharts option={option} style={{ height: '100%' }} />;
}
