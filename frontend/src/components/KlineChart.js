import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { detectMACDDivergence } from '../utils/divergence';
import THEME, { getMomentumColor as themeGetMomentumColor, formatVolume } from '../utils/chartTheme';

const STRONG_TREND_LEVELS_KLINE = new Set(['强势', '极强']);
const WEAK_SELL_SCORE_MAX_KLINE = 0.30;

function klineIsStrongTrend(d) {
  if (!d) return false;
  if (d.momentum_level && STRONG_TREND_LEVELS_KLINE.has(d.momentum_level)) return true;
  const { close, ma5, ma10, ma20, macd_hist } = d;
  if ([close, ma5, ma10, ma20].some((v) => v == null)) return false;
  const aligned = close > ma5 && ma5 > ma10 && ma10 > ma20;
  const macdOk = macd_hist == null ? true : macd_hist > 0;
  return aligned && macdOk;
}

function klineIsWeakSell(d) {
  if (!d || d.signal !== -1) return false;
  const score = Number(d.sell_score);
  if (!isFinite(score)) return false;
  return score < WEAK_SELL_SCORE_MAX_KLINE && klineIsStrongTrend(d);
}

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
  const isMinuteData = data.length > 0 && typeof data[0].date === 'string' && data[0].date.includes(' ');
  const dates = data.map((d) => d.date);
  const mobileStartIndex = Math.max(dates.length - (isMinuteData ? 60 : 30), 0);
  const candleData = data.map((d) => [d.open, d.close, d.low, d.high]);

  // 支撑位和压力位 markLine 配置
  const supportLines = (stockData.support_levels || []).map((level) => ({
    yAxis: level.price,
    lineStyle: { color: THEME.support, type: 'dashed', width: 1.5 },
    label: {
      show: true,
      position: 'insideEndTop',
      formatter: `支撑 ${level.price.toFixed(2)}`,
      color: THEME.support,
      fontSize: 11,
      backgroundColor: 'rgba(0, 176, 124, 0.12)',
      padding: [2, 6],
      borderRadius: 3,
    },
  }));

  const resistanceLines = (stockData.resistance_levels || []).map((level) => ({
    yAxis: level.price,
    lineStyle: { color: THEME.resistance, type: 'dashed', width: 1.5 },
    label: {
      show: true,
      position: 'insideEndTop',
      formatter: `压力 ${level.price.toFixed(2)}`,
      color: THEME.resistance,
      fontSize: 11,
      backgroundColor: 'rgba(250, 62, 62, 0.12)',
      padding: [2, 6],
      borderRadius: 3,
    },
  }));

  const activeSupportLines = showSupport ? supportLines : [];
  const activeResistanceLines = showResistance ? resistanceLines : [];

  // 最新收盘价
  const lastClose = data.length > 0 ? data[data.length - 1].close : 0;
  const prevClose = data.length > 1 ? data[data.length - 2].close : 0;
  const isLastUp = lastClose >= prevClose;

  const buyPoints = data
    .filter((d) => d.signal === 1 && d.buy_score >= 0.08)
    .map((d) => {
      const score = d.buy_score || 0;
      const size = isMobile ? Math.max(22, Math.min(30, 18 + score * 48)) : Math.max(12, Math.min(20, 12 + score * 32));
      return {
        name: 'B',
        coord: [d.date, d.low],
        symbol: 'circle',
        symbolSize: size,
        label: { show: true, formatter: 'B', color: '#fff', fontSize: isMobile ? 11 : 9, fontWeight: 'bold' },
        itemStyle: { color: THEME.up, borderColor: '#fff', borderWidth: isMobile ? 2 : 1, shadowBlur: 8, shadowColor: THEME.upShadow },
      };
    });

  const buyAlertPoints = data
    .filter((d) => d.buy_alert === 1)
    .map((d) => {
      const score = d.buy_score || 0;
      const size = isMobile ? Math.max(18, Math.min(24, 14 + score * 40)) : Math.max(10, Math.min(16, 10 + score * 24));
      return {
        name: 'B?',
        coord: [d.date, d.low],
        symbol: 'circle',
        symbolSize: size,
        label: { show: true, formatter: 'B?', color: '#fff', fontSize: isMobile ? 10 : 8, fontWeight: 'bold' },
        itemStyle: {
          color: THEME.warning || '#f59e0b',
          borderColor: '#fff',
          borderWidth: isMobile ? 2 : 1,
          borderType: 'dashed',
          shadowBlur: 8,
          shadowColor: 'rgba(245,158,11,0.6)',
        },
      };
    });

  const sellPoints = data
    .filter((d) => {
      if (d.signal !== -1) return false;
      return d.close < d.ma5;
    })
    .map((d) => {
      const score = d.sell_score || 0;
      const size = isMobile ? Math.max(22, Math.min(30, 18 + score * 48)) : Math.max(12, Math.min(20, 12 + score * 32));
      const weak = klineIsWeakSell(d);
      if (weak) {
        return {
          name: 'S',
          coord: [d.date, d.high],
          symbol: 'circle',
          symbolSize: size,
          label: { show: true, formatter: 'S!', color: '#fff', fontSize: isMobile ? 11 : 9, fontWeight: 'bold' },
          itemStyle: { color: THEME.warning || '#f59e0b', borderColor: '#fff', borderWidth: isMobile ? 2 : 1, shadowBlur: 10, shadowColor: 'rgba(245,158,11,0.7)' },
        };
      }
      return {
        name: 'S',
        coord: [d.date, d.high],
        symbol: 'circle',
        symbolSize: size,
        label: { show: true, formatter: 'S', color: '#fff', fontSize: isMobile ? 11 : 9, fontWeight: 'bold' },
        itemStyle: { color: THEME.sellBlue, borderColor: '#fff', borderWidth: isMobile ? 2 : 1, shadowBlur: 8, shadowColor: 'rgba(58,142,255,0.6)' },
      };
    });

  const { topDivergence, bottomDivergence } = detectMACDDivergence(data);
  const bottomDivByDate = {};
  bottomDivergence.forEach((d) => { bottomDivByDate[d.coord[0]] = d; });
  const topDivByDate = {};
  topDivergence.forEach((d) => { topDivByDate[d.coord[0]] = d; });
  const lastDate = data.length > 0 ? data[data.length - 1].date : '';
  const latestBottomDiv = lastDate ? bottomDivByDate[lastDate] : null;
  const latestTopDiv = lastDate ? topDivByDate[lastDate] : null;
  const latestDivText = [
    latestBottomDiv ? `今日底背离 分值${latestBottomDiv.score}` : '',
    latestTopDiv ? `今日顶背离 分值${latestTopDiv.score}` : '',
  ].filter(Boolean).join(' / ');
  const latestDivColor = latestBottomDiv ? THEME.down : THEME.up;
  const latestDataItem = data.length > 0 ? data[data.length - 1] : null;
  const latestDivergencePoints = isMobile && latestDataItem ? [
    latestBottomDiv ? {
      name: '底背离',
      coord: [lastDate, latestDataItem.low],
      symbol: 'roundRect',
      symbolSize: [34, 18],
      label: { show: true, formatter: '底背', color: '#fff', fontSize: 10, fontWeight: 'bold' },
      itemStyle: { color: THEME.down, borderColor: '#fff', borderWidth: 1, shadowBlur: 8, shadowColor: 'rgba(0,176,124,0.6)' },
    } : null,
    latestTopDiv ? {
      name: '顶背离',
      coord: [lastDate, latestDataItem.high],
      symbol: 'roundRect',
      symbolSize: [34, 18],
      label: { show: true, formatter: '顶背', color: '#fff', fontSize: 10, fontWeight: 'bold' },
      itemStyle: { color: THEME.up, borderColor: '#fff', borderWidth: 1, shadowBlur: 8, shadowColor: 'rgba(250,62,62,0.6)' },
    } : null,
  ].filter(Boolean) : [];

  const latestMomentum = stockData.summary?.latest_momentum || null;

  const getMomentumIcon = (score) => {
    if (score === null || score === undefined) return '📊';
    if (score >= 80) return '🔥';
    if (score >= 60) return '💪';
    if (score >= 40) return '⚖️';
    if (score >= 20) return '📉';
    return '❄️';
  };

  const stockNameWithSymbol = stockData.name ? stockData.name + ' (' + symbol + ')' : symbol;
  const latestPctChange = prevClose > 0 ? ((lastClose - prevClose) / prevClose * 100) : 0;
  const latestInfoText = showLatestInfo
    ? `${lastClose.toFixed(2)} ${latestPctChange >= 0 ? '+' : ''}${latestPctChange.toFixed(2)}%`
    : '';
  const titleText = stockNameWithSymbol + (titleSuffix || '') + (latestInfoText ? `  ${latestInfoText}` : '');

  let signalTag = '';
  let signalColor = '';
  let signalBg = '';
  let weakSellTag = '';
  let alertTag = '';
  let alertColor = '';
  const adviceText = stockData.trade_advice
    ? ` | 止损 ${stockData.trade_advice.stop_loss} 止盈 ${stockData.trade_advice.take_profit} 加仓 ${stockData.trade_advice.add_price}`
    : '';
  for (let i = data.length - 1; i >= 0; i--) {
    if (data[i].signal !== 0) {
      const dateStr = data[i].date.replace(/-/g, '.');
      if (data[i].signal === 1) {
        signalTag = isMobile ? `${dateStr} 买点 强度${((data[i].buy_score || 0) * 100).toFixed(0)}%` : dateStr + ' 出现买点' + adviceText;
        signalColor = '#fff';
        signalBg = THEME.up;
      } else {
        signalTag = isMobile ? `${dateStr} 卖点 强度${((data[i].sell_score || 0) * 100).toFixed(0)}%` : dateStr + ' 出现卖点';
        signalColor = '#fff';
        signalBg = THEME.sellBlue;
        if (klineIsWeakSell(data[i])) {
          weakSellTag = '⚠️ 强趋势中弱卖点，建议减仓 1/3';
        }
      }
      break;
    }
    if (data[i].buy_alert === 1 && !alertTag) {
      const dateStr = data[i].date.replace(/-/g, '.');
      alertTag = isMobile ? `${dateStr} 买入预警` : dateStr + ' 买入预警（待二次确认）';
      alertColor = THEME.warning || '#f59e0b';
    }
  }

  const titleItems = [
    {
      text: titleText,
      left: isMobile ? 8 : 12,
      top: isMobile ? 6 : 6,
      textStyle: {
        color: THEME.titleGold,
        fontSize: isMobile ? 13 : 15,
        fontWeight: 'bold',
        width: isMobile ? 260 : null,
        overflow: 'truncate',
      },
    },
  ];
  const lineH = isMobile ? 26 : 26;
  let nextTop = isMobile ? 30 : 32;
  if (signalTag) {
    const titleItem = {
      left: isMobile ? 8 : 12,
      top: nextTop,
    };
    if (weakSellTag && !isMobile) {
      titleItem.text = '{tag|' + signalTag + '}  {warn|' + weakSellTag + '}';
      titleItem.textStyle = {
        rich: {
          tag: {
            backgroundColor: signalBg,
            color: signalColor,
            fontSize: 12,
            fontWeight: 'bold',
            padding: [3, 9],
            borderRadius: 3,
          },
          warn: {
            backgroundColor: 'rgba(245, 158, 11, 0.18)',
            color: '#f59e0b',
            fontSize: 12,
            fontWeight: 'bold',
            padding: [3, 9],
            borderRadius: 3,
            borderColor: '#f59e0b',
            borderWidth: 1,
          },
        },
      };
    } else {
      titleItem.text = '{tag|' + signalTag + '}';
      titleItem.textStyle = {
        rich: {
          tag: {
            backgroundColor: signalBg,
            color: signalColor,
            fontSize: isMobile ? 12 : 12,
            fontWeight: 'bold',
            padding: isMobile ? [4, 9] : [3, 9],
            borderRadius: 3,
          },
        },
      };
    }
    titleItems.push(titleItem);
    nextTop += lineH;
  }
  if (alertTag) {
    titleItems.push({
      left: isMobile ? 8 : 12,
      top: nextTop,
      text: '{alert|' + alertTag + '}',
      textStyle: {
        rich: {
          alert: {
            backgroundColor: 'rgba(245, 158, 11, 0.18)',
            color: alertColor,
            fontSize: isMobile ? 12 : 12,
            fontWeight: 'bold',
            padding: isMobile ? [4, 9] : [3, 9],
            borderRadius: 3,
            borderColor: alertColor,
            borderWidth: 1,
          },
        },
      },
    });
    nextTop += lineH;
  }
  if (latestDivText && isMobile) {
    titleItems.push({
      left: 8,
      top: nextTop,
      text: '{div|' + latestDivText + '}',
      textStyle: {
        rich: {
          div: {
            backgroundColor: latestDivColor,
            color: '#fff',
            fontSize: 10,
            fontWeight: 'bold',
            padding: [3, 7],
            borderRadius: 3,
          },
        },
      },
    });
    nextTop += lineH;
  }
  if (weakSellTag && isMobile) {
    titleItems.push({
      left: 8,
      top: nextTop,
      text: '{warn|' + weakSellTag + '}',
      textStyle: {
        rich: {
          warn: {
            backgroundColor: 'rgba(245, 158, 11, 0.18)',
            color: '#f59e0b',
            fontSize: 10,
            fontWeight: 'bold',
            padding: [3, 7],
            borderRadius: 3,
            borderColor: '#f59e0b',
            borderWidth: 1,
          },
        },
      },
    });
  }

  const volMa5 = data.map((_, i) => {
    if (i < 4) return null;
    let sum = 0;
    for (let j = i - 4; j <= i; j++) sum += data[j].volume;
    return sum / 5;
  });
  const volMa10 = data.map((_, i) => {
    if (i < 9) return null;
    let sum = 0;
    for (let j = i - 9; j <= i; j++) sum += data[j].volume;
    return sum / 10;
  });

  const macdHistData = data.map((d, i) => {
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
  });

  const legendData = ['K线', 'MA5', 'MA10', 'MA20', 'DIF', 'DEA', 'MACD柱', '布林上轨', '布林中轨', '布林下轨', 'VOL_MA5', 'VOL_MA10'].filter((item) => !hideLegendItems.includes(item));

  const option = {
    backgroundColor: THEME.bg,
    title: titleItems,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', crossStyle: { color: THEME.textWeak } },
      backgroundColor: 'rgba(17, 23, 34, 0.95)',
      borderColor: THEME.border,
      borderWidth: 1,
      textStyle: { color: THEME.textPrimary, fontSize: 12, lineHeight: 18 },
      extraCssText: 'border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);',
      formatter: function (params) {
        const date = params[0]?.axisValue;
        const dataItem = data.find((d) => d.date === date);
        let html = `<div style="padding:8px 10px;min-width:180px">`;
        html += `<div style="font-weight:bold;margin-bottom:4px;color:${THEME.titleGold}">${stockData.name || ''} (${symbol})</div>`;
        html += `<div style="font-size:11px;color:${THEME.textSecondary};margin-bottom:6px">${date || ''}</div>`;
        if (dataItem) {
          const idx = data.indexOf(dataItem);
          const prev = idx > 0 ? data[idx - 1].close : null;
          const pChange = prev && prev > 0 ? ((dataItem.close - prev) / prev * 100) : null;
          const pColor = pChange !== null ? (pChange >= 0 ? THEME.up : THEME.down) : THEME.textSecondary;
          html += `<div style="display:grid;grid-template-columns:auto 1fr;gap:2px 12px;font-size:12px">`;
          html += `<span style="color:${THEME.textSecondary}">开盘</span><span>${dataItem.open.toFixed(2)}</span>`;
          html += `<span style="color:${THEME.textSecondary}">收盘</span><span style="color:${pColor};font-weight:bold">${dataItem.close.toFixed(2)}${pChange !== null ? ` ${pChange >= 0 ? '+' : ''}${pChange.toFixed(2)}%` : ''}</span>`;
          html += `<span style="color:${THEME.textSecondary}">最高</span><span>${dataItem.high.toFixed(2)}</span>`;
          html += `<span style="color:${THEME.textSecondary}">最低</span><span>${dataItem.low.toFixed(2)}</span>`;
          html += `<span style="color:${THEME.textSecondary}">成交量</span><span>${formatVolume(dataItem.volume)}</span>`;
          html += `</div>`;
        }
        params.forEach((p) => {
          if (p.componentType === 'markPoint') return;
          if (p.seriesType === 'line' && ['MA5', 'MA10', 'MA20', 'DIF', 'DEA', 'VOL_MA5', 'VOL_MA10'].includes(p.seriesName)) {
            const val = typeof p.data === 'number' ? p.data : null;
            if (val !== null) html += `<div style="font-size:11px;color:${THEME.textSecondary};margin-top:2px">${p.seriesName}: <span style="color:${THEME.textPrimary}">${val.toFixed(2)}</span></div>`;
          }
        });
        if (dataItem && dataItem.signal !== 0) {
          if (dataItem.signal === 1) {
            html += `<div style="color:${THEME.up};margin-top:4px;font-weight:bold">买入信号 强度: ${(dataItem.buy_score * 100).toFixed(1)}%</div>`;
          } else if (dataItem.signal === -1) {
            html += `<div style="color:${THEME.sellBlue};margin-top:4px;font-weight:bold">卖出信号 强度: ${(dataItem.sell_score * 100).toFixed(1)}%</div>`;
            if (klineIsWeakSell(dataItem)) {
              html += `<div style="color:#f59e0b;margin-top:4px;font-weight:bold;padding:3px 6px;background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.5);border-radius:4px">⚠️ 强趋势中弱卖点，建议减仓 1/3</div>`;
            }
          }
        }
        if (dataItem && dataItem.buy_alert === 1) {
          html += `<div style="color:#f59e0b;margin-top:4px;font-weight:bold;padding:3px 6px;background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.5);border-radius:4px">⚠️ 买入预警（下跌趋势首次信号，需等待二次确认）</div>`;
        }
        if (dataItem && dataItem.momentum_score !== null && dataItem.momentum_score !== undefined) {
          const momColor = themeGetMomentumColor(dataItem.momentum_score);
          html += `<div style="color:${momColor};margin-top:4px;font-weight:bold">动能: ${dataItem.momentum_score.toFixed(1)} (${dataItem.momentum_level || ''})</div>`;
        }
        if (date && bottomDivByDate[date]) {
          const dv = bottomDivByDate[date];
          html += `<div style="color:${THEME.down};margin-top:4px;font-weight:bold">${dv.name} 分值 ${dv.score} (对比前低 ${dv.prevDate})</div>`;
        }
        if (date && topDivByDate[date]) {
          const dv = topDivByDate[date];
          html += `<div style="color:${THEME.up};margin-top:4px;font-weight:bold">${dv.name} 分值 ${dv.score}</div>`;
        }
        html += '</div>';
        return html;
      },
    },
    legend: {
      data: legendData,
      textStyle: { color: THEME.textSecondary, fontSize: 11 },
      top: nextTop,
      right: 10,
      itemWidth: 14,
      itemHeight: 2,
    },
    grid: [
      { left: '8%', right: '8%', top: nextTop > 57 ? '22%' : nextTop > 33 ? '18%' : '14%', height: '46%' },
      { left: '8%', right: '8%', top: '66%', height: '15%' },
      { left: '8%', right: '8%', top: '84%', height: '12%' },
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLine: { lineStyle: { color: THEME.border } },
        axisLabel: { show: false },
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLine: { lineStyle: { color: THEME.border } },
        axisLabel: { show: false },
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 2,
        axisLine: { lineStyle: { color: THEME.border } },
        axisLabel: {
          color: THEME.textSecondary,
          fontSize: 10,
          interval: isMinuteData ? Math.max(0, Math.floor(data.length / 10) - 1) : 0,
          formatter: isMinuteData
            ? (value) => {
                const parts = value.split(' ');
                if (parts.length === 2) return parts[0].substring(5) + '\n' + parts[1];
                return value;
              }
            : undefined,
        },
      },
    ],
    yAxis: [
      {
        scale: true,
        position: 'right',
        gridIndex: 0,
        splitLine: { lineStyle: { color: THEME.grid, type: 'dashed', opacity: 0.5 } },
        axisLabel: { color: THEME.textSecondary, fontSize: 10 },
      },
      {
        scale: true,
        position: 'right',
        gridIndex: 1,
        splitLine: { show: false },
        axisLabel: { show: false },
      },
      {
        scale: true,
        position: 'right',
        gridIndex: 2,
        splitLine: { show: false },
        axisLabel: { color: THEME.textSecondary, fontSize: 10, formatter: (v) => formatVolume(v) },
      },
    ],
    dataZoom: isMobile ? [] : [
      { type: 'inside', xAxisIndex: [0, 1, 2], start: 0, end: 100 },
      {
        type: 'slider',
        xAxisIndex: [0, 1, 2],
        bottom: 0,
        height: 18,
        borderColor: THEME.border,
        backgroundColor: 'rgba(17, 23, 34, 0.6)',
        fillerColor: 'rgba(228, 185, 106, 0.15)',
        handleStyle: { color: THEME.titleGold, borderColor: THEME.titleGold },
        textStyle: { color: THEME.textSecondary, fontSize: 10 },
      },
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: candleData,
        xAxisIndex: 0,
        yAxisIndex: 0,
        barMaxWidth: 14,
        barMinWidth: 2,
        itemStyle: {
          color: 'transparent',
          color0: THEME.down,
          borderColor: THEME.up,
          borderColor0: THEME.down,
          borderWidth: 1,
        },
        markPoint: { data: [...buyPoints, ...buyAlertPoints, ...sellPoints, ...latestDivergencePoints] },
        markLine: {
          symbol: 'none',
          data: [
            ...activeSupportLines,
            ...activeResistanceLines,
            {
              yAxis: lastClose,
              lineStyle: { color: isLastUp ? THEME.up : THEME.down, type: 'dashed', width: 1, opacity: 0.55 },
              label: {
                show: true,
                position: 'insideEndTop',
                formatter: lastClose.toFixed(2),
                color: '#fff',
                fontSize: 10,
                fontWeight: 'bold',
                backgroundColor: isLastUp ? THEME.up : THEME.down,
                padding: [2, 6],
                borderRadius: 3,
              },
            },
          ],
          label: { distance: [10, 0] },
        },
      },
      {
        name: 'MA5',
        type: 'line',
        data: data.map((d) => d.ma5),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: THEME.ma5, width: 1.2 },
        symbol: 'none',
        connectNulls: true,
      },
      {
        name: 'MA10',
        type: 'line',
        data: data.map((d) => d.ma10),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: THEME.ma10, width: 1.2 },
        symbol: 'none',
        connectNulls: true,
      },
      {
        name: 'MA20',
        type: 'line',
        data: data.map((d) => d.ma20),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: THEME.ma20, width: 1.2 },
        symbol: 'none',
        connectNulls: true,
      },
      {
        name: '布林上轨',
        type: 'line',
        data: data.map((d) => d.boll_upper),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: THEME.boll, width: 0.8, type: [4, 4], opacity: 0.7 },
        symbol: 'none',
        areaStyle: { color: THEME.bollArea },
      },
      {
        name: '布林中轨',
        type: 'line',
        data: data.map((d) => d.boll_middle),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: THEME.boll, width: 0.8, opacity: 0.6 },
        symbol: 'none',
      },
      {
        name: '布林下轨',
        type: 'line',
        data: data.map((d) => d.boll_lower),
        xAxisIndex: 0,
        yAxisIndex: 0,
        lineStyle: { color: THEME.boll, width: 0.8, type: [4, 4], opacity: 0.7 },
        symbol: 'none',
      },
      {
        name: 'DIF',
        type: 'line',
        data: data.map((d) => d.macd),
        xAxisIndex: 1,
        yAxisIndex: 1,
        lineStyle: { color: THEME.dif, width: 1.5 },
        symbol: 'none',
        markPoint: { data: [...topDivergence, ...bottomDivergence] },
      },
      {
        name: 'DEA',
        type: 'line',
        data: data.map((d) => d.macd_signal),
        xAxisIndex: 1,
        yAxisIndex: 1,
        lineStyle: { color: THEME.dea, width: 1.5 },
        symbol: 'none',
      },
      {
        name: 'MACD柱',
        type: 'bar',
        data: macdHistData,
        xAxisIndex: 1,
        yAxisIndex: 1,
        barMaxWidth: 6,
      },
      {
        name: '成交量',
        type: 'bar',
        data: data.map((d) => ({
          value: d.volume,
          itemStyle: { color: d.close >= d.open ? THEME.up : THEME.down, opacity: 0.75 },
        })),
        xAxisIndex: 2,
        yAxisIndex: 2,
        barMaxWidth: 14,
      },
      {
        name: 'VOL_MA5',
        type: 'line',
        data: volMa5,
        xAxisIndex: 2,
        yAxisIndex: 2,
        lineStyle: { color: THEME.ma5, width: 1 },
        symbol: 'none',
        connectNulls: true,
      },
      {
        name: 'VOL_MA10',
        type: 'line',
        data: volMa10,
        xAxisIndex: 2,
        yAxisIndex: 2,
        lineStyle: { color: THEME.ma20, width: 1 },
        symbol: 'none',
        connectNulls: true,
      },
    ],
    media: [
      {
        query: { maxWidth: 768 },
        option: {
          title: [{ textStyle: { fontSize: 13 } }],
          legend: { show: false },
          grid: [
            { left: 8, right: 44, top: 36 + (titleItems.length - 1) * 24, height: `${Math.max(50, 74 - (titleItems.length - 1) * 6)}%` },
            { left: 8, right: 44, top: 0, height: 0 },
            { left: 8, right: 44, top: 0, height: 0 },
          ],
          xAxis: [
            { min: mobileStartIndex, max: dates.length - 1, axisLabel: { show: true, color: THEME.textSecondary, fontSize: 10, interval: isMinuteData ? Math.max(0, Math.floor((dates.length - mobileStartIndex) / 6) - 1) : 0, formatter: isMinuteData ? (value) => { const p = value.split(' '); return p.length === 2 ? p[0].substring(5) + ' ' + p[1] : value; } : undefined } },
            { show: false },
            { show: false },
          ],
          yAxis: [
            { axisLabel: { color: THEME.textSecondary, fontSize: 10 } },
            { show: false },
            { show: false },
          ],
          dataZoom: [],
          series: [
            { markPoint: { symbolSize: 26, label: { fontSize: 11 } } },
            { lineStyle: { width: 1.2 } },
            { lineStyle: { width: 1.2 } },
            { lineStyle: { width: 1.2 } },
            { lineStyle: { width: 0 }, areaStyle: { opacity: 0 }, emphasis: { disabled: true } },
            { lineStyle: { width: 0 }, emphasis: { disabled: true } },
            { lineStyle: { width: 0 }, emphasis: { disabled: true } },
            { lineStyle: { width: 0 }, emphasis: { disabled: true } },
            { lineStyle: { width: 0 }, emphasis: { disabled: true } },
            { itemStyle: { opacity: 0 }, emphasis: { disabled: true } },
            { itemStyle: { opacity: 0 }, emphasis: { disabled: true } },
            { lineStyle: { width: 0 }, emphasis: { disabled: true } },
            { lineStyle: { width: 0 }, emphasis: { disabled: true } },
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
                padding: isMobile ? '2px 6px' : '4px 12px',
                fontSize: isMobile ? '10px' : '12px',
                backgroundColor: themeGetMomentumColor(latestMomentum.score),
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                gap: isMobile ? '3px' : '4px',
              }}
            >
              <span>{getMomentumIcon(latestMomentum.score)}</span>
              <span>{isMobile ? latestMomentum.score.toFixed(0) : `动能 ${latestMomentum.score.toFixed(0)}`}</span>
              <span>{latestMomentum.level}</span>
            </button>
            {showMomentumDetail && (
              <div
                style={{
                  position: 'absolute',
                  top: '110%',
                  right: 0,
                  background: 'rgba(17, 23, 34, 0.97)',
                  border: `1px solid ${themeGetMomentumColor(latestMomentum.score)}`,
                  borderRadius: '6px',
                  padding: '10px 12px',
                  fontSize: '12px',
                  color: '#fff',
                  zIndex: 20,
                  minWidth: '200px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '6px', color: themeGetMomentumColor(latestMomentum.score) }}>
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
                  const barColor = ratio >= 0.7 ? THEME.up : ratio >= 0.4 ? '#fbbf24' : '#6b7280';
                  return (
                    <div key={item.key} style={{ marginBottom: '4px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                        <span style={{ color: THEME.textSecondary }}>{item.label}</span>
                        <span style={{ color: '#fff', fontWeight: 'bold' }}>
                          {val.toFixed(1)} / {item.max}
                        </span>
                      </div>
                      <div style={{ height: '4px', background: THEME.border, borderRadius: '2px', overflow: 'hidden' }}>
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
            backgroundColor: showSupport ? THEME.support : 'rgba(0, 176, 124, 0.2)',
            color: showSupport ? '#fff' : THEME.support,
            border: `1px solid ${THEME.support}`,
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
            backgroundColor: showResistance ? THEME.resistance : 'rgba(250, 62, 62, 0.2)',
            color: showResistance ? '#fff' : THEME.resistance,
            border: `1px solid ${THEME.resistance}`,
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
