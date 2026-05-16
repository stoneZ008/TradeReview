import ReactECharts from 'echarts-for-react';

export default function RSIChart({ stockData, symbol }) {
  if (!stockData?.data) return null;

  const data = stockData.data;
  const dates = data.map(d => d.date);
  const rsiValues = data.map(d => d.rsi);

  const buySignals = data.filter(d => d.signal === 1).map(d => ({
    name: '买入',
    xAxis: d.date,
    yAxis: d.rsi,
    itemStyle: { color: '#22c55e' },
    value: d.rsi
  }));

  const sellSignals = data.filter(d => d.signal === -1).map(d => ({
    name: '卖出',
    xAxis: d.date,
    yAxis: d.rsi,
    itemStyle: { color: '#ef4444' },
    value: d.rsi
  }));

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
          if (p.seriesName === 'RSI' && p.data != null) {
            html += `<div style="color: #a78bfa">RSI: ${p.data.toFixed(2)}</div>`;
          } else if (p.seriesName === '买入信号' && p.data != null) {
            html += `<div style="color: #22c55e">🔴 买入信号</div>`;
          } else if (p.seriesName === '卖出信号' && p.data != null) {
            html += `<div style="color: #ef4444">🔴 卖出信号</div>`;
          }
        });
        html += '</div>';
        return html;
      }
    },
    legend: {
      data: ['RSI', '买入信号', '卖出信号'],
      textStyle: { color: '#fff' },
      top: 0
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
      splitLine: { lineStyle: { color: '#2a2a4a' } },
      axisLabel: {
        formatter: '{value}'
      }
    },
    dataZoom: [
      { type: 'inside', start: 50, end: 100 },
      { type: 'slider', bottom: 0, height: 20 }
    ],
    series: [
      {
        name: 'RSI',
        type: 'line',
        data: rsiValues,
        lineStyle: { color: '#a78bfa' },
        symbol: 'none',
        z: 2,
        markLine: {
          silent: true,
          lineStyle: { type: 'dashed', width: 1 },
          label: { show: true, color: '#fff', fontSize: 10 },
          data: [
            { yAxis: 70, lineStyle: { color: '#ef4444' }, label: { formatter: '超买 70' } },
            { yAxis: 50, lineStyle: { color: '#666' }, label: { formatter: '中轴 50' } },
            { yAxis: 30, lineStyle: { color: '#22c55e' }, label: { formatter: '超卖 30' } }
          ]
        }
      },
      {
        name: '买入信号',
        type: 'scatter',
        data: buySignals.map(s => [s.xAxis, s.yAxis]),
        symbol: 'triangle',
        symbolSize: 12,
        itemStyle: { color: '#22c55e', borderColor: '#fff', borderWidth: 1 },
        z: 3
      },
      {
        name: '卖出信号',
        type: 'scatter',
        data: sellSignals.map(s => [s.xAxis, s.yAxis]),
        symbol: 'triangle',
        symbolRotate: 180,
        symbolSize: 12,
        itemStyle: { color: '#ef4444', borderColor: '#fff', borderWidth: 1 },
        z: 3
      }
    ],
    media: [
      {
        query: { maxWidth: 768 },
        option: {
          legend: { textStyle: { fontSize: 11 } },
          grid: { left: '8%', right: '3%', top: '15%', bottom: '18%' },
          dataZoom: [
            { type: 'inside', start: 30, end: 100 },
            { type: 'slider', height: 24, bottom: 0 }
          ],
          series: [
            { markLine: { label: { fontSize: 9 } } },
            { symbolSize: 10 },
            { symbolSize: 10 }
          ]
        }
      }
    ]
  };

  return <ReactECharts option={option} style={{ height: '100%' }} />;
}
