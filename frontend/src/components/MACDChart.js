import ReactECharts from 'echarts-for-react';
import { detectMACDDivergence } from '../utils/divergence';
import THEME from '../utils/chartTheme';

export default function MACDChart({ stockData, symbol }) {
  if (!stockData?.data) return null;

  const data = stockData.data;
  const dates = data.map((d) => d.date);
  const { topDivergence, bottomDivergence } = detectMACDDivergence(data);
  const bottomByDate = {};
  bottomDivergence.forEach((d) => { bottomByDate[d.coord[0]] = d; });
  const topByDate = {};
  topDivergence.forEach((d) => { topByDate[d.coord[0]] = d; });

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
          const val = p.data;
          const numVal = typeof val === 'object' ? val.value : val;
          if (typeof numVal === 'number') {
            html += `<div style="font-size:12px">${p.seriesName}: <span style="color:${THEME.textPrimary}">${numVal.toFixed(4)}</span></div>`;
          }
        });
        if (date && bottomByDate[date]) {
          const dv = bottomByDate[date];
          html += `<div style="color:${THEME.down};margin-top:4px;font-weight:bold">${dv.name} 分值 ${dv.score} (对比前低 ${dv.prevDate})</div>`;
        }
        if (date && topByDate[date]) {
          const dv = topByDate[date];
          html += `<div style="color:${THEME.up};margin-top:4px;font-weight:bold">${dv.name} 分值 ${dv.score}</div>`;
        }
        html += '</div>';
        return html;
      },
    },
    legend: {
      data: ['DIF', 'DEA', 'MACD柱', '顶背离', '底背离'],
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
      scale: true,
      position: 'right',
      splitLine: { lineStyle: { color: THEME.grid, type: 'dashed', opacity: 0.5 } },
      axisLabel: { color: THEME.textSecondary },
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
        name: 'DIF',
        type: 'line',
        data: data.map((d) => d.macd),
        lineStyle: { color: THEME.dif, width: 1.8 },
        symbol: 'none',
      },
      {
        name: 'DEA',
        type: 'line',
        data: data.map((d) => d.macd_signal),
        lineStyle: { color: THEME.dea, width: 1.8 },
        symbol: 'none',
      },
      {
        name: 'MACD柱',
        type: 'bar',
        barMaxWidth: 8,
        data: data.map((d, i) => {
          const prev = i > 0 ? data[i - 1].macd_hist : 0;
          const curr = d.macd_hist;
          const shrinking = (curr > 0 && curr < prev) || (curr < 0 && curr > prev);
          let color;
          if (curr >= 0) {
            color = shrinking ? 'rgba(250, 62, 62, 0.55)' : THEME.up;
          } else {
            color = shrinking ? 'rgba(0, 176, 124, 0.55)' : THEME.down;
          }
          return { value: curr, itemStyle: { color } };
        }),
      },
      {
        name: '顶背离',
        type: 'scatter',
        data: topDivergence.map((d) => ({ value: d.coord[1], ...d })),
        markPoint: {
          data: topDivergence,
        },
      },
      {
        name: '底背离',
        type: 'scatter',
        data: bottomDivergence.map((d) => ({ value: d.coord[1], ...d })),
        markPoint: {
          data: bottomDivergence,
        },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: '100%' }} />;
}
