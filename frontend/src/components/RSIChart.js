import ReactECharts from 'echarts-for-react';
import THEME from '../utils/chartTheme';

export default function RSIChart({ stockData, symbol }) {
  if (!stockData?.data) return null;

  const data = stockData.data;
  const dates = data.map((d) => d.date);
  const rsiValues = data.map((d) => d.rsi);

  const buySignals = data
    .filter((d) => d.signal === 1)
    .map((d) => ({
      name: '买入',
      xAxis: d.date,
      yAxis: d.rsi,
      itemStyle: { color: THEME.up },
      value: d.rsi,
    }));

  const sellSignals = data
    .filter((d) => d.signal === -1)
    .map((d) => ({
      name: '卖出',
      xAxis: d.date,
      yAxis: d.rsi,
      itemStyle: { color: THEME.sellBlue },
      value: d.rsi,
    }));

  const option = {
    backgroundColor: THEME.bg,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(17, 23, 34, 0.95)',
      borderColor: THEME.border,
      borderWidth: 1,
      textStyle: { color: THEME.textPrimary, fontSize: 12 },
      extraCssText: 'border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);',
      formatter: function (params) {
        const date = params[0]?.axisValue;
        let html = `<div style="padding:8px 10px">
          <div style="font-weight:bold;margin-bottom:4px;color:${THEME.titleGold}">${stockData.name || ''} (${symbol})</div>
          <div style="font-size:11px;color:${THEME.textSecondary};margin-bottom:6px">${date || ''}</div>`;
        params.forEach((p) => {
          if (p.seriesName === 'RSI' && p.data != null) {
            html += `<div style="color:${THEME.ma20}">RSI: ${p.data.toFixed(2)}</div>`;
          } else if (p.seriesName === '买入信号' && p.data != null) {
            html += `<div style="color:${THEME.up}">● 买入信号</div>`;
          } else if (p.seriesName === '卖出信号' && p.data != null) {
            html += `<div style="color:${THEME.sellBlue}">● 卖出信号</div>`;
          }
        });
        html += '</div>';
        return html;
      },
    },
    legend: {
      data: ['RSI', '买入信号', '卖出信号'],
      textStyle: { color: THEME.textSecondary, fontSize: 11 },
      top: 0,
    },
    grid: { left: '8%', right: '8%', top: '12%', bottom: '15%' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: THEME.border } },
      axisLabel: { color: THEME.textSecondary },
    },
    yAxis: {
      min: 0,
      max: 100,
      position: 'right',
      splitLine: { lineStyle: { color: THEME.grid, type: 'dashed', opacity: 0.5 } },
      axisLabel: {
        color: THEME.textSecondary,
        formatter: '{value}',
      },
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      {
        type: 'slider',
        bottom: 0,
        height: 18,
        borderColor: THEME.border,
        fillerColor: 'rgba(228, 185, 106, 0.15)',
        handleStyle: { color: THEME.titleGold, borderColor: THEME.titleGold },
        textStyle: { color: THEME.textSecondary, fontSize: 10 },
      },
    ],
    series: [
      {
        name: 'RSI',
        type: 'line',
        data: rsiValues,
        lineStyle: { color: THEME.ma20, width: 1.8 },
        symbol: 'none',
        z: 2,
        markLine: {
          silent: true,
          lineStyle: { type: 'dashed', width: 1 },
          label: { show: true, color: '#fff', fontSize: 10 },
          data: [
            { yAxis: 70, lineStyle: { color: THEME.up }, label: { formatter: '超买 70' } },
            { yAxis: 50, lineStyle: { color: THEME.textWeak }, label: { formatter: '中轴 50' } },
            { yAxis: 30, lineStyle: { color: THEME.down }, label: { formatter: '超卖 30' } },
          ],
        },
      },
      {
        name: '买入信号',
        type: 'scatter',
        data: buySignals.map((s) => [s.xAxis, s.yAxis]),
        symbol: 'triangle',
        symbolSize: 12,
        itemStyle: { color: THEME.up, borderColor: '#fff', borderWidth: 1 },
        z: 3,
      },
      {
        name: '卖出信号',
        type: 'scatter',
        data: sellSignals.map((s) => [s.xAxis, s.yAxis]),
        symbol: 'triangle',
        symbolRotate: 180,
        symbolSize: 12,
        itemStyle: { color: THEME.sellBlue, borderColor: '#fff', borderWidth: 1 },
        z: 3,
      },
    ],
    media: [
      {
        query: { maxWidth: 768 },
        option: {
          legend: { textStyle: { fontSize: 11 } },
          grid: { left: '8%', right: '3%', top: '15%', bottom: '18%' },
          dataZoom: [
            { type: 'inside', start: 30, end: 100 },
            { type: 'slider', height: 24, bottom: 0 },
          ],
          series: [
            { markLine: { label: { fontSize: 9 } } },
            { symbolSize: 10 },
            { symbolSize: 10 },
          ],
        },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: '100%' }} />;
}
