import ReactECharts from 'echarts-for-react';
import { detectMACDDivergence } from '../utils/divergence';

export default function MACDChart({ stockData, symbol }) {
  if (!stockData?.data) return null;

  const data = stockData.data;
  const dates = data.map(d => d.date);
  const { topDivergence, bottomDivergence } = detectMACDDivergence(data);

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
          const val = p.data;
          const numVal = typeof val === 'object' ? val.value : val;
          if (typeof numVal === 'number') {
            html += `<div>${p.seriesName}: ${numVal.toFixed(4)}</div>`;
          }
        });
        html += '</div>';
        return html;
      }
    },
    legend: {
      data: ['DIF', 'DEA', 'MACD柱', '顶背离', '底背离'],
      textStyle: { color: '#a0a0a0' },
      top: 0
    },
    grid: { left: '10%', right: '5%', top: '12%', bottom: '15%' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#2a2a4a' } },
      axisLabel: { color: '#a0a0a0' }
    },
    yAxis: {
      scale: true,
      splitLine: { lineStyle: { color: '#2a2a4a' } },
      axisLabel: { color: '#a0a0a0' }
    },
    dataZoom: [
      { type: 'inside', start: 50, end: 100 },
      { type: 'slider', bottom: 0, height: 20 }
    ],
    series: [
      { name: 'DIF', type: 'line', data: data.map(d => d.macd), lineStyle: { color: '#3b82f6', width: 2 }, symbol: 'none' },
      { name: 'DEA', type: 'line', data: data.map(d => d.macd_signal), lineStyle: { color: '#fbbf24', width: 2 }, symbol: 'none' },
      { name: 'MACD柱', type: 'bar', data: data.map(d => ({ value: d.macd_hist, itemStyle: { color: d.macd_hist >= 0 ? '#ef4444' : '#22c55e' } })) },
      {
        name: '顶背离', type: 'scatter',
        data: topDivergence.map(d => ({ value: d.coord[1], ...d })),
        markPoint: { data: topDivergence, symbol: 'arrow', symbolSize: 16, label: { show: true, formatter: '顶背离', color: '#ef4444', fontSize: 11, fontWeight: 'bold', position: 'top' }, itemStyle: { color: '#ef4444' } }
      },
      {
        name: '底背离', type: 'scatter',
        data: bottomDivergence.map(d => ({ value: d.coord[1], ...d })),
        markPoint: { data: bottomDivergence, symbol: 'arrow', symbolSize: 16, label: { show: true, formatter: '底背离', color: '#22c55e', fontSize: 11, fontWeight: 'bold', position: 'bottom' }, itemStyle: { color: '#22c55e' } }
      }
    ]
  };

  return <ReactECharts option={option} style={{ height: '100%' }} />;
}
