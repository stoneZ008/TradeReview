export function detectMACDDivergence(data, lookback = 20) {
  const topDivergence = [];
  const bottomDivergence = [];

  for (let i = lookback; i < data.length; i++) {
    let isPriceHigh = true;
    for (let j = 1; j <= 5; j++) {
      if (i - j >= 0 && data[i - j].close >= data[i].close) { isPriceHigh = false; break; }
      if (i + j < data.length && data[i + j].close >= data[i].close) { isPriceHigh = false; break; }
    }

    let isPriceLow = true;
    for (let j = 1; j <= 5; j++) {
      if (i - j >= 0 && data[i - j].close <= data[i].close) { isPriceLow = false; break; }
      if (i + j < data.length && data[i + j].close <= data[i].close) { isPriceLow = false; break; }
    }

    if (isPriceHigh) {
      for (let j = i - lookback; j < i - 5; j++) {
        let isPrevHigh = true;
        for (let k = 1; k <= 5; k++) {
          if (j - k >= 0 && data[j - k].close >= data[j].close) { isPrevHigh = false; break; }
          if (j + k < data.length && data[j + k].close >= data[j].close) { isPrevHigh = false; break; }
        }
        if (isPrevHigh) {
          if (data[i].close > data[j].close && data[i].macd < data[j].macd && data[i].macd > 0) {
            topDivergence.push({
              name: '顶背离',
              coord: [data[i].date, data[i].macd],
              symbol: 'arrow',
              symbolSize: 14,
              label: { show: true, formatter: '顶背离', color: '#ef4444', fontSize: 10, fontWeight: 'bold', position: 'top' },
              itemStyle: { color: '#ef4444' }
            });
          }
          break;
        }
      }
    }

    if (isPriceLow) {
      for (let j = i - lookback; j < i - 5; j++) {
        let isPrevLow = true;
        for (let k = 1; k <= 5; k++) {
          if (j - k >= 0 && data[j - k].close <= data[j].close) { isPrevLow = false; break; }
          if (j + k < data.length && data[j + k].close <= data[j].close) { isPrevLow = false; break; }
        }
        if (isPrevLow) {
          if (data[i].close < data[j].close && data[i].macd > data[j].macd && data[i].macd < 0) {
            bottomDivergence.push({
              name: '底背离',
              coord: [data[i].date, data[i].macd],
              symbol: 'arrow',
              symbolSize: 14,
              label: { show: true, formatter: '底背离', color: '#22c55e', fontSize: 10, fontWeight: 'bold', position: 'bottom' },
              itemStyle: { color: '#22c55e' }
            });
          }
          break;
        }
      }
    }
  }

  return { topDivergence, bottomDivergence };
}
