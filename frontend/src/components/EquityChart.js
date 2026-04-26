import ReactECharts from 'echarts-for-react';

export default function EquityChart({ backtestResult, stockData, symbol }) {
  if (!backtestResult?.equity_curve) return null;

  const data = backtestResult.equity_curve;
  const dates = data.map(d => d.date);
  const equity = data.map(d => d.equity);

  const option = {
    backgroundColor: '#0f0f1a',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(26, 26, 46, 0.9)',
      borderColor: '#2a2a4a',
      textStyle: { color: '#fff' },
      formatter: (params) => {
        const p = params[0];
        const value = p.value || 0;
        return '<div style="padding: 8px">'
          + '<div style="font-weight: bold; margin-bottom: 4px">' + (stockData.name || '') + ' (' + symbol + ')</div>'
          + '<div style="font-size: 12px; color: #a0a0a0; margin-bottom: 8px">' + p.name + '</div>'
          + '<div>权益: ¥' + value.toLocaleString() + '</div>'
          + '</div>';
      }
    },
    grid: { left: '10%', right: '5%', top: '12%', bottom: '15%' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { color: '#a0a0a0' }
    },
    yAxis: {
      scale: true,
      splitLine: { lineStyle: { color: '#2a2a4a' } },
      axisLabel: {
        color: '#a0a0a0',
        formatter: (v) => (v / 10000).toFixed(0) + '万'
      }
    },
    series: [{
      name: '权益曲线',
      type: 'line',
      data: equity,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0)' }
          ]
        }
      },
      lineStyle: { color: '#3b82f6', width: 2 },
      symbol: 'none'
    }]
  };

  return <ReactECharts option={option} style={{ height: '100%' }} />;
}
