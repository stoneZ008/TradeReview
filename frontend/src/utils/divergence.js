import THEME from './chartTheme';

const DEFAULT_OPTIONS = {
  lookback: 30,
  leftN: 5,
  rightM: 2,
  minPriceDrop: 0.005,
  minMacdImprove: 0.1,
  zeroAxisTolerance: 0.01,
  cooldownDays: 5,
  weakThreshold: 40,
  strongThreshold: 70,
};

function isPivotLow(data, i, leftN, rightM) {
  const v = data[i].low;
  for (let k = 1; k <= leftN; k++) {
    if (i - k < 0) return false;
    if (data[i - k].low <= v) return false;
  }
  for (let k = 1; k <= rightM; k++) {
    if (i + k >= data.length) return false;
    if (data[i + k].low <= v) return false;
  }
  return true;
}

function isPivotHigh(data, i, leftN, rightM) {
  const v = data[i].high;
  for (let k = 1; k <= leftN; k++) {
    if (i - k < 0) return false;
    if (data[i - k].high >= v) return false;
  }
  for (let k = 1; k <= rightM; k++) {
    if (i + k >= data.length) return false;
    if (data[i + k].high >= v) return false;
  }
  return true;
}

function scoreBottomDivergence(data, i, j, opts) {
  const closeI = data[i].close;
  const lowI = data[i].low;
  const lowJ = data[j].low;
  const histI = data[i].macd_hist;
  const histJ = data[j].macd_hist;

  const priceDrop = (lowJ - lowI) / lowJ;
  const histImprove = (histI - histJ) / (Math.abs(histJ) || 1e-6);
  const closeVsLow = (closeI - lowI) / (lowI || 1e-6);

  const volMA = data.slice(Math.max(0, i - 19), i + 1).reduce((s, d) => s + d.volume, 0) / (i - Math.max(0, i - 19) + 1);
  const volumeFactor = volMA > 0 ? Math.min(data[i].volume / volMA, 3) / 3 : 0;

  let ma5Turning = 0;
  if (i >= 2 && data[i - 1].ma5 != null && data[i - 2].ma5 != null && data[i].ma5 != null) {
    const slope1 = data[i - 1].ma5 - data[i - 2].ma5;
    const slope2 = data[i].ma5 - data[i - 1].ma5;
    if (slope1 < 0 && slope2 > 0) ma5Turning = 1;
  }

  let score = 0;
  score += 25 * Math.min(priceDrop / 0.05, 1);
  score += 25 * Math.min(histImprove / 1.0, 1);
  score += 15 * Math.min(closeVsLow / 0.03, 1);
  score += 15 * Math.min(volumeFactor, 1);
  score += 10 * ma5Turning;

  return Math.round(Math.min(100, Math.max(0, score)));
}

function findThreeWave(data, i, pivots, opts) {
  if (pivots.length < 2) return false;
  for (let a = 0; a < pivots.length; a++) {
    for (let b = a + 1; b < pivots.length; b++) {
      const j1 = pivots[a];
      const j2 = pivots[b];
      if (
        data[j1].low > data[j2].low && data[j2].low > data[i].low &&
        data[j1].macd_hist < data[j2].macd_hist && data[j2].macd_hist < data[i].macd_hist
      ) {
        return true;
      }
    }
  }
  return false;
}

function cooldownFilter(divergences, cooldownDays) {
  if (divergences.length === 0) return divergences;
  const sorted = [...divergences].sort((a, b) => a.dataIndex - b.dataIndex);
  const result = [sorted[0]];
  for (let k = 1; k < sorted.length; k++) {
    if (sorted[k].dataIndex - result[result.length - 1].dataIndex > cooldownDays) {
      result.push(sorted[k]);
    } else if (sorted[k].score > result[result.length - 1].score) {
      result[result.length - 1] = sorted[k];
    }
  }
  return result;
}

export function detectMACDDivergence(data, userOptions = {}) {
  const opts = { ...DEFAULT_OPTIONS, ...userOptions };
  const { lookback, leftN, rightM, minPriceDrop, minMacdImprove, zeroAxisTolerance, cooldownDays, weakThreshold, strongThreshold } = opts;

  const rawBottom = [];
  const rawTop = [];

  for (let i = lookback; i < data.length; i++) {
    if (isPivotLow(data, i, leftN, rightM)) {
      const pivots = [];
      for (let j = i - lookback; j <= i - leftN - rightM; j++) {
        if (isPivotLow(data, j, leftN, rightM)) {
          pivots.push(j);
        }
      }
      if (pivots.length === 0) continue;

      pivots.sort((a, b) => data[a].low - data[b].low);
      let bestJ = -1;
      for (const j of pivots) {
        if (data[j].low < data[i].low) { bestJ = j; break; }
      }
      if (bestJ < 0) continue;

      const priceDrop = (data[bestJ].low - data[i].low) / data[bestJ].low;
      if (priceDrop < minPriceDrop) continue;

      const histImprove = (data[i].macd_hist - data[bestJ].macd_hist) / (Math.abs(data[bestJ].macd_hist) || 1e-6);
      const difImprove = data[i].macd - data[bestJ].macd;
      if (histImprove < minMacdImprove && difImprove <= 0) continue;

      const zeroLimit = zeroAxisTolerance > 0 ? data[i].close * zeroAxisTolerance : 0;
      if (data[i].macd > zeroLimit) continue;

      const isThreeWave = findThreeWave(data, i, pivots.filter(j => j !== bestJ && data[j].low > data[i].low), opts);
      let score = scoreBottomDivergence(data, i, bestJ, opts);
      if (isThreeWave) score = Math.min(100, score + 10);

      if (score < weakThreshold) continue;

      const level = score >= strongThreshold ? 'strong' : 'medium';
      const label = isThreeWave ? '三浪底背离' : '底背离';

      rawBottom.push({
        name: label,
        coord: [data[i].date, data[i].macd],
        symbol: 'arrow',
        symbolSize: Math.round(10 + (score / 100) * 14),
        label: {
          show: true,
          formatter: label + (score >= strongThreshold ? ' ' + score : ''),
          color: THEME.down,
          fontSize: score >= strongThreshold ? 11 : 9,
          fontWeight: score >= strongThreshold ? 'bold' : 'normal',
          position: 'bottom',
        },
        itemStyle: {
          color: score >= strongThreshold ? THEME.down : 'rgba(0, 176, 124, 0.6)',
        },
        score,
        level,
        isThreeWave,
        prevDate: data[bestJ].date,
        dataIndex: i,
      });
    }

    if (isPivotHigh(data, i, leftN, rightM)) {
      const pivots = [];
      for (let j = i - lookback; j <= i - leftN - rightM; j++) {
        if (isPivotHigh(data, j, leftN, rightM)) {
          pivots.push(j);
        }
      }
      if (pivots.length === 0) continue;

      pivots.sort((a, b) => data[b].high - data[a].high);
      let bestJ = -1;
      for (const j of pivots) {
        if (data[j].high > data[i].high) { bestJ = j; break; }
      }
      if (bestJ < 0) continue;

      const priceRise = (data[i].high - data[bestJ].high) / data[bestJ].high;
      if (Math.abs(priceRise) < minPriceDrop) continue;

      const histDecline = (data[bestJ].macd_hist - data[i].macd_hist) / (Math.abs(data[bestJ].macd_hist) || 1e-6);
      const difDecline = data[bestJ].macd - data[i].macd;
      if (histDecline < minMacdImprove && difDecline <= 0) continue;

      const zeroLimit = zeroAxisTolerance > 0 ? data[i].close * zeroAxisTolerance : 0;
      if (data[i].macd < -zeroLimit) continue;

      let score = Math.round(Math.min(100, Math.max(0,
        25 * Math.min(Math.abs(priceRise) / 0.05, 1) +
        25 * Math.min(histDecline / 1.0, 1) +
        25 +
        25 * ((data[i].close < data[i].open ? 1 : 0))
      )));

      if (score < weakThreshold) continue;

      const level = score >= strongThreshold ? 'strong' : 'medium';
      const label = '顶背离';

      rawTop.push({
        name: label,
        coord: [data[i].date, data[i].macd],
        symbol: 'arrow',
        symbolSize: Math.round(10 + (score / 100) * 14),
        label: {
          show: true,
          formatter: label + (score >= strongThreshold ? ' ' + score : ''),
          color: THEME.up,
          fontSize: score >= strongThreshold ? 11 : 9,
          fontWeight: score >= strongThreshold ? 'bold' : 'normal',
          position: 'top',
        },
        itemStyle: {
          color: score >= strongThreshold ? THEME.up : 'rgba(250, 62, 62, 0.6)',
        },
        score,
        level,
        isThreeWave: false,
        dataIndex: i,
      });
    }
  }

  const topDivergence = cooldownFilter(rawTop, cooldownDays);
  const bottomDivergence = cooldownFilter(rawBottom, cooldownDays);

  return { topDivergence, bottomDivergence };
}
