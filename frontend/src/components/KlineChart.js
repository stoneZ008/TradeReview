import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { detectMACDDivergence } from '../utils/divergence';

export default function KlineChart({ stockData, symbol }) {
  const [showSupport, setShowSupport] = useState(false);
  const [showResistance, setShowResistance] = useState(false);

  if (!stockData?.data) return null;

  const data = stockData.data;
  const dates = data.map((d) => d.date);
  const candleData = data.map((d) => [d.open, d.close, d.low, d.high]);

  // 支撑位和压力位 markLine 配置
  const supportLines = (stockData.support_levels || []).map((level) => ({
    yAxis: level.price,
    lineStyle: { color: '#22c55e', type: 'dashed', width: 1.5 },
    label: {
      show: true,
      position: 'start',
      formatter: `支撑 ${level.price.toFixed(2)}`,
      color: '#22c55e',
      fontSize: 11,
      backgroundColor: 'rgba(34, 197, 94, 0.1)',
    },
  }));

  const resistanceLines = (stockData.resistance_levels || []).map((level) => ({
    yAxis: level.price,
    lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 },
    label: {
      show: true,
      position: 'start',
      formatter: `压力 ${level.price.toFixed(2)}`,
      color: '#ef4444',
      fontSize: 11,
      backgroundColor: 'rgba(239, 68, 68, 0.1)',
    },
  }));

  const activeSupportLines = showSupport ? supportLines : [];
  const activeResistanceLines = showResistance ? resistanceLines : [];

  // 最新收盘价
  const lastClose = data.length > 0 ? data[data.length - 1].close : 0;
  const lastDate = data.length > 0 ? data[data.length - 1].date : '';

  const buyPoints = data
    .filter((d) => d.signal === 1 && d.buy_score >= 0.08)
    .map((d) => ({
      name: 'B',
      coord: [d.date, d.low],
      symbol: 'circle',
      symbolSize: 20,
      label: { show: true, formatter: 'B', color: '#fff', fontSize: 12, fontWeight: 'bold' },
      itemStyle: { color: '#ef4444', borderColor: '#fff', borderWidth: 1 },
    }));

  const sellPoints = data
    .filter((d) => {
      if (d.signal !== -1) return false;
      return d.close < d.ma5;
    })
    .map((d) => ({
      name: 'S',
      coord: [d.date, d.high],
      symbol: 'circle',
      symbolSize: 20,
      label: { show: true, formatter: 'S', color: '#fff', fontSize: 12, fontWeight: 'bold' },
      itemStyle: { color: '#3b82f6', borderColor: '#fff', borderWidth: 1 },
    }));

  const { topDivergence, bottomDivergence } = detectMACDDivergence(data);

  const stockNameWithSymbol = stockData.name ? stockData.name + ' (' + symbol + ')' : symbol;
  const titleText = stockNameWithSymbol;

  let signalTag = '';
  let signalColor = '';
  let signalBg = '';
  for (let i = data.length - 1; i >= 0; i--) {
    if (data[i].signal !== 0) {
      const dateStr = data[i].date.replace(/-/g, '.');
      if (data[i].signal === 1) {
        signalTag = dateStr + ' 出现买点';
        signalColor = '#fff';
        signalBg = '#ef4444';
      } else {
        signalTag = dateStr + ' 出现卖点';
        signalColor = '#fff';
        signalBg = '#3b82f6';
      }
      break;
    }
  }

  const titleItems = [
    {
      text: '买卖信号参考',
      left: 'center',
      top: 2,
      textStyle: { color: '#a78bfa', fontSize: 20, fontWeight: 'bold' },
    },
    {
      text: titleText,
      left: '10%',
      top: signalTag ? 34 : 36,
      textStyle: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
    },
  ];
  if (signalTag) {
    titleItems.push({
      text: '{tag|' + signalTag + '}',
      left: '10%',
      top: 58,
      textStyle: {
        rich: {
          tag: {
            backgroundColor: signalBg,
            color: signalColor,
            fontSize: 14,
            fontWeight: 'bold',
            padding: [4, 10],
            borderRadius: 4,
          },
        },
      },
    });
  }

  const option = {
    backgroundColor: '#0f0f1a',
    title: titleItems,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(26, 26, 46, 0.9)',
      borderColor: '#2a2a4a',
      textStyle: { color: '#fff' },
      formatter: function (params) {
        const date = params[0]?.axisValue;
        const dataItem = data.find((d) => d.date === date);
        let html = `<div style="padding: 8px">
          <div style="font-weight: bold; margin-bottom: 4px">${stockData.name || ''} (${symbol})</div>
          <div style="font-size: 12px; color: #a0a0a0; margin-bottom: 8px">${date || ''}</div>`;
        params.forEach((p) => {
          if (p.componentType === 'markPoint') return;
          if (p.seriesType === 'candlestick') {
            html += `<div>开盘: ${p.data[1]?.toFixed(2)}</div>
              <div>收盘: ${p.data[2]?.toFixed(2)}</div>
              <div>最低: ${p.data[3]?.toFixed(2)}</div>
              <div>最高: ${p.data[4]?.toFixed(2)}</div>`;
          } else if (p.seriesType === 'line') {
            const val = typeof p.data === 'number' ? p.data : null;
            if (val !== null) html += `<div>${p.seriesName}: ${val.toFixed(2)}</div>`;
          } else if (p.seriesType === 'bar') {
            const val = typeof p.data === 'object' && p.data !== null ? p.data.value : p.data;
            if (typeof val === 'number') html += `<div>${p.seriesName}: ${val.toFixed(2)}</div>`;
          }
        });
        if (dataItem && dataItem.signal !== 0) {
          if (dataItem.signal === 1) {
            html += `<div style="color: #ef4444; margin-top: 4px">买入信号强度: ${(dataItem.buy_score * 100).toFixed(1)}%</div>`;
          } else if (dataItem.signal === -1) {
            html += `<div style="color: #3b82f6; margin-top: 4px">卖出信号强度: ${(dataItem.sell_score * 100).toFixed(1)}%</div>`;
          }
        }
        html += '</div>';
        return html;
      },
    },
    legend: {
      data: ['K线', 'MA5', 'MA10', 'MA20', 'DIF', 'DEA', 'MACD柱'],
      textStyle: { color: '#a0a0a0' },
      top: signalTag ? 40 : 0,
    },
    grid: [
      { left: '10%', right: '5%', top: signalTag ? '18%' : '12%', height: '40%' },
      { left: '10%', right: '5%', top: '61%', height: '16%' },
      { left: '10%', right: '5%', top: '80%', height: '14%' },
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLine: { lineStyle: { color: '#2a2a4a' } },
        axisLabel: { show: false },
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLine: { lineStyle: { color: '#2a2a4a' } },
        axisLabel: { show: false },
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 2,
        axisLine: { lineStyle: { color: '#2a2a4a' } },
        axisLabel: { color: '#a0a0a0', fontSize: 10 },
      },
    ],
    yAxis: [
      {
        scale: true,
        gridIndex: 0,
        splitLine: { lineStyle: { color: '#2a2a4a' } },
        axisLabel: { color: '#a0a0a0' },
      },
      { scale: true, gridIndex: 1, splitLine: { show: false }, axisLabel: { show: false } },
      { scale: true, gridIndex: 2, splitLine: { show: false }, axisLabel: { show: false } },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1, 2], start: 50, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1, 2], bottom: 0, height: 20 },
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: candleData,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#ef4444',
          color0: '#22c55e',
          borderColor: '#ef4444',
          borderColor0: '#22c55e',
        },
        markPoint: { data: [...buyPoints, ...sellPoints] },
        markLine: {
          symbol: 'none',
          data: [...activeSupportLines, ...activeResistanceLines],
          label: { distance: [10, 0] },
        },
      },
      {
        name: 'MA5',
        type: 'line',
        data: data.map((d) => d.ma5),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: '#fbbf24', width: 1 },
        symbol: 'none',
      },
      {
        name: 'MA10',
        type: 'line',
        data: data.map((d) => d.ma10),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: '#60a5fa', width: 1 },
        symbol: 'none',
      },
      {
        name: 'MA20',
        type: 'line',
        data: data.map((d) => d.ma20),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: '#a78bfa', width: 1 },
        symbol: 'none',
      },
      {
        name: '布林带',
        type: 'line',
        data: data.map((d) => d.boll_upper),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: '#3b82f6', width: 1, type: 'dashed' },
        symbol: 'none',
      },
      {
        name: '布林中轨',
        type: 'line',
        data: data.map((d) => d.boll_middle),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: '#3b82f6', width: 1 },
        symbol: 'none',
      },
      {
        name: '布林下轨',
        type: 'line',
        data: data.map((d) => d.boll_lower),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: '#3b82f6', width: 1, type: 'dashed' },
        symbol: 'none',
      },
      {
        name: 'DIF',
        type: 'line',
        data: data.map((d) => d.macd),
        xAxisIndex: 1,
        yAxisIndex: 1,
        lineStyle: { color: '#3b82f6', width: 1.5 },
        symbol: 'none',
        markPoint: { data: [...topDivergence, ...bottomDivergence] },
      },
      {
        name: 'DEA',
        type: 'line',
        data: data.map((d) => d.macd_signal),
        xAxisIndex: 1,
        yAxisIndex: 1,
        lineStyle: { color: '#fbbf24', width: 1.5 },
        symbol: 'none',
      },
      {
        name: 'MACD柱',
        type: 'bar',
        data: data.map((d) => ({
          value: d.macd_hist,
          itemStyle: { color: d.macd_hist >= 0 ? '#ef4444' : '#22c55e' },
        })),
        xAxisIndex: 1,
        yAxisIndex: 1,
      },
      {
        name: '成交量',
        type: 'bar',
        data: data.map((d) => ({
          value: d.volume,
          itemStyle: { color: d.close >= d.open ? '#ef4444' : '#22c55e' },
        })),
        xAxisIndex: 2,
        yAxisIndex: 2,
      },
    ],
    media: [
      {
        query: { maxWidth: 768 },
        option: {
          title: [{ textStyle: { fontSize: 16 } }, { textStyle: { fontSize: 11 } }],
          legend: { top: signalTag ? 48 : 8, textStyle: { fontSize: 10 } },
          grid: [
            { left: '8%', right: '3%', top: signalTag ? '22%' : '15%', height: '45%' },
            { left: '8%', right: '3%', top: '64%', height: '14%' },
            { left: '8%', right: '3%', top: '82%', height: '12%' },
          ],
          dataZoom: [
            { type: 'inside', start: 30, end: 100 },
            { type: 'slider', height: 24, bottom: 0 },
          ],
          series: [
            { markPoint: { symbolSize: 28, label: { fontSize: 9 } } },
            { lineStyle: { width: 1 } },
            { lineStyle: { width: 1 } },
            { lineStyle: { width: 1 } },
            {},
            {},
            {},
          ],
        },
      },
    ],
  };

  return (
    <div style={{ position: 'relative', height: '100%' }}>
      <div
        style={{ position: 'absolute', top: 8, right: 20, zIndex: 10, display: 'flex', gap: '8px' }}
      >
        <button
          onClick={() => setShowSupport(!showSupport)}
          style={{
            padding: '4px 12px',
            fontSize: '12px',
            backgroundColor: showSupport ? '#22c55e' : 'rgba(34, 197, 94, 0.2)',
            color: showSupport ? '#fff' : '#22c55e',
            border: '1px solid #22c55e',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 'bold',
          }}
        >
          支撑
        </button>
        <button
          onClick={() => setShowResistance(!showResistance)}
          style={{
            padding: '4px 12px',
            fontSize: '12px',
            backgroundColor: showResistance ? '#ef4444' : 'rgba(239, 68, 68, 0.2)',
            color: showResistance ? '#fff' : '#ef4444',
            border: '1px solid #ef4444',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 'bold',
          }}
        >
          压力
        </button>
      </div>
      <ReactECharts option={option} style={{ height: '100%' }} />
    </div>
  );
}
