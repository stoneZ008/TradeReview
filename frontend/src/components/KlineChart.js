import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { detectMACDDivergence } from '../utils/divergence';

export default function KlineChart({ stockData, symbol, titleSuffix = '', showLatestInfo = false, hideLegendItems = [], forceMobile = false }) {
  const [showSupport, setShowSupport] = useState(false);
  const [showResistance, setShowResistance] = useState(false);
  const [showMomentumDetail, setShowMomentumDetail] = useState(false);
  const [isMobile, setIsMobile] = useState(() => forceMobile || window.innerWidth <= 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(forceMobile || window.innerWidth <= 768);
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [forceMobile]);

  if (!stockData?.data) return null;

  const data = stockData.data;
  const dates = data.map((d) => d.date);
  const mobileStartIndex = Math.max(dates.length - 30, 0);
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
  const prevClose = data.length > 1 ? data[data.length - 2].close : 0;
  const latestPctChange = prevClose > 0 ? ((lastClose - prevClose) / prevClose * 100) : 0;
  const latestInfoText = showLatestInfo
    ? `收盘 ${lastClose.toFixed(2)} ${latestPctChange >= 0 ? '+' : ''}${latestPctChange.toFixed(2)}%`
    : '';

  const buyPoints = data
    .filter((d) => d.signal === 1 && d.buy_score >= 0.08)
    .map((d) => ({
      name: 'B',
      coord: [d.date, d.low],
      symbol: 'circle',
      symbolSize: isMobile ? 34 : 20,
      label: { show: true, formatter: 'B', color: '#fff', fontSize: isMobile ? 15 : 12, fontWeight: 'bold' },
      itemStyle: { color: '#ef4444', borderColor: '#fff', borderWidth: isMobile ? 2 : 1 },
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
      symbolSize: isMobile ? 34 : 20,
      label: { show: true, formatter: 'S', color: '#fff', fontSize: isMobile ? 15 : 12, fontWeight: 'bold' },
      itemStyle: { color: '#3b82f6', borderColor: '#fff', borderWidth: isMobile ? 2 : 1 },
    }));

  const { topDivergence, bottomDivergence } = detectMACDDivergence(data);

  const latestMomentum = stockData.summary?.latest_momentum || null;
  const getMomentumColor = (score) => {
    if (score === null || score === undefined) return '#6b7280';
    if (score >= 80) return '#ef4444';
    if (score >= 60) return '#f97316';
    if (score >= 40) return '#fbbf24';
    if (score >= 20) return '#06b6d4';
    return '#22c55e';
  };
  const getMomentumIcon = (score) => {
    if (score === null || score === undefined) return '📊';
    if (score >= 80) return '🔥';
    if (score >= 60) return '💪';
    if (score >= 40) return '⚖️';
    if (score >= 20) return '📉';
    return '❄️';
  };

  const stockNameWithSymbol = stockData.name ? stockData.name + ' (' + symbol + ')' : symbol;
  const titleText = stockNameWithSymbol + (latestInfoText ? ` (${latestInfoText})` : '');

  let signalTag = '';
  let signalColor = '';
  let signalBg = '';
  const adviceText = stockData.trade_advice
    ? ` | 止损 ${stockData.trade_advice.stop_loss} 止盈 ${stockData.trade_advice.take_profit} 加仓 ${stockData.trade_advice.add_price}`
    : '';
  for (let i = data.length - 1; i >= 0; i--) {
    if (data[i].signal !== 0) {
      const dateStr = data[i].date.replace(/-/g, '.');
      if (data[i].signal === 1) {
        signalTag = isMobile ? `${dateStr} 买点 强度${((data[i].buy_score || 0) * 100).toFixed(0)}%` : dateStr + ' 出现买点' + adviceText;
        signalColor = '#fff';
        signalBg = '#ef4444';
      } else {
        signalTag = isMobile ? `${dateStr} 卖点 强度${((data[i].sell_score || 0) * 100).toFixed(0)}%` : dateStr + ' 出现卖点';
        signalColor = '#fff';
        signalBg = '#3b82f6';
      }
      break;
    }
  }

  const titleItems = [
    {
      text: `买卖信号参考${titleSuffix}`,
      left: 'center',
      top: isMobile ? 4 : 2,
      textStyle: { color: '#a78bfa', fontSize: isMobile ? 14 : 20, fontWeight: 'bold' },
    },
    {
      text: titleText,
      left: isMobile ? 8 : '10%',
      top: signalTag ? (isMobile ? 28 : 34) : (isMobile ? 28 : 36),
      textStyle: { color: '#fff', fontSize: isMobile ? 11 : 14, fontWeight: 'bold', width: isMobile ? 260 : null, overflow: 'truncate' },
    },
  ];
  if (signalTag) {
      titleItems.push({
      text: '{tag|' + signalTag + '}',
      left: isMobile ? 8 : '10%',
      top: isMobile ? 48 : 58,
      textStyle: {
        rich: {
          tag: {
            backgroundColor: signalBg,
            color: signalColor,
            fontSize: isMobile ? 14 : 14,
            fontWeight: 'bold',
            padding: isMobile ? [5, 10] : [4, 10],
            borderRadius: 4,
          },
        },
      },
    });
  }

  const legendData = ['K线', 'MA5', 'MA10', 'MA20', 'DIF', 'DEA', 'MACD柱'].filter((item) => !hideLegendItems.includes(item));

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
        if (dataItem && dataItem.momentum_score !== null && dataItem.momentum_score !== undefined) {
          const momColor = getMomentumColor(dataItem.momentum_score);
          html += `<div style="color: ${momColor}; margin-top: 4px; font-weight: bold">动能: ${dataItem.momentum_score.toFixed(1)} (${dataItem.momentum_level || ''})</div>`;
        }
        html += '</div>';
        return html;
      },
    },
    legend: {
      data: legendData,
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
    dataZoom: isMobile ? [] : [
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
          title: [{ textStyle: { fontSize: 14 } }, { textStyle: { fontSize: 11 } }],
          legend: { show: false },
          grid: [
            { left: 42, right: 12, top: signalTag ? 66 : 48, height: 292 },
            { left: 42, right: 12, top: 0, height: 0 },
            { left: 42, right: 12, top: 0, height: 0 },
          ],
          xAxis: [
            { min: mobileStartIndex, max: dates.length - 1, axisLabel: { show: true, color: '#a0a0a0', fontSize: 10 } },
            { show: false },
            { show: false },
          ],
          yAxis: [
            { axisLabel: { color: '#a0a0a0', fontSize: 10 } },
            { show: false },
            { show: false },
          ],
          dataZoom: [],
          series: [
            { markPoint: { symbolSize: 34, label: { fontSize: 15 } } },
            { lineStyle: { width: 1 } },
            { lineStyle: { width: 1 } },
            { lineStyle: { width: 1 } },
            { lineStyle: { width: 0 }, itemStyle: { opacity: 0 }, emphasis: { disabled: true } },
            { lineStyle: { width: 0 }, itemStyle: { opacity: 0 }, emphasis: { disabled: true } },
            { lineStyle: { width: 0 }, itemStyle: { opacity: 0 }, emphasis: { disabled: true } },
            { lineStyle: { width: 0 }, itemStyle: { opacity: 0 }, emphasis: { disabled: true } },
            { itemStyle: { opacity: 0 }, emphasis: { disabled: true } },
            { itemStyle: { opacity: 0 }, emphasis: { disabled: true } },
          ],
        },
      },
    ],
  };

  return (
    <div style={{ position: 'relative', height: '100%' }}>
      <div
        style={{ position: 'absolute', top: isMobile ? 30 : 8, right: isMobile ? 8 : 20, zIndex: 10, display: 'flex', gap: isMobile ? '4px' : '8px', alignItems: 'center' }}
      >
        {latestMomentum && (
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowMomentumDetail(!showMomentumDetail)}
              title="点击查看动能分项明细"
              style={{
                padding: isMobile ? '3px 8px' : '4px 12px',
                fontSize: isMobile ? '11px' : '12px',
                backgroundColor: getMomentumColor(latestMomentum.score),
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <span>{getMomentumIcon(latestMomentum.score)}</span>
              <span>动能 {latestMomentum.score.toFixed(0)}</span>
              <span>{latestMomentum.level}</span>
            </button>
            {showMomentumDetail && (
              <div
                style={{
                  position: 'absolute',
                  top: '110%',
                  right: 0,
                  background: 'rgba(15, 15, 26, 0.97)',
                  border: `1px solid ${getMomentumColor(latestMomentum.score)}`,
                  borderRadius: '6px',
                  padding: '10px 12px',
                  fontSize: '12px',
                  color: '#fff',
                  zIndex: 20,
                  minWidth: '200px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '6px', color: getMomentumColor(latestMomentum.score) }}>
                  动能分项 (总分 {latestMomentum.score.toFixed(1)} / 100)
                </div>
                {[
                  { key: 'price_trend', label: '价格趋势', max: 25 },
                  { key: 'ma_slope', label: '均线斜率', max: 15 },
                  { key: 'price_change', label: '涨幅强度', max: 20 },
                  { key: 'macd_momentum', label: 'MACD动能', max: 15 },
                  { key: 'rsi', label: 'RSI强度', max: 10 },
                  { key: 'volume', label: '成交量', max: 10 },
                  { key: 'position_52w', label: '52周位置', max: 5 },
                ].map((item) => {
                  const val = latestMomentum.factors?.[item.key] ?? 0;
                  const ratio = val / item.max;
                  const barColor = ratio >= 0.7 ? '#ef4444' : ratio >= 0.4 ? '#fbbf24' : '#6b7280';
                  return (
                    <div key={item.key} style={{ marginBottom: '4px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                        <span style={{ color: '#a0a0a0' }}>{item.label}</span>
                        <span style={{ color: '#fff', fontWeight: 'bold' }}>
                          {val.toFixed(1)} / {item.max}
                        </span>
                      </div>
                      <div style={{ height: '4px', background: '#2a2a4a', borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{ width: `${ratio * 100}%`, height: '100%', background: barColor }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
        <button
          onClick={() => setShowSupport(!showSupport)}
          style={{
            padding: isMobile ? '3px 8px' : '4px 12px',
            fontSize: isMobile ? '11px' : '12px',
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
            padding: isMobile ? '3px 8px' : '4px 12px',
            fontSize: isMobile ? '11px' : '12px',
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
