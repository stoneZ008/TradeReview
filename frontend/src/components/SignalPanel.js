const STRONG_TREND_LEVELS = new Set(['强势', '极强']);
const WEAK_SELL_SCORE_MAX = 0.30;

function isStrongTrendByMA(d) {
  if (d == null) return false;
  const { close, ma5, ma10, ma20, macd_hist } = d;
  if ([close, ma5, ma10, ma20].some((v) => v == null)) return false;
  const maAligned = close > ma5 && ma5 > ma10 && ma10 > ma20;
  const macdPositive = macd_hist == null ? true : macd_hist > 0;
  return maAligned && macdPositive;
}

function isStrongTrend(d) {
  if (d == null) return false;
  if (d.momentum_level && STRONG_TREND_LEVELS.has(d.momentum_level)) return true;
  return isStrongTrendByMA(d);
}

function isWeakSellInStrongTrend(d) {
  if (!d || d.signal !== -1) return false;
  const score = Number(d.sell_score);
  if (!isFinite(score)) return false;
  return score < WEAK_SELL_SCORE_MAX && isStrongTrend(d);
}

export default function SignalPanel({ stockData }) {
  if (!stockData?.data) return null;

  const signals = stockData.data
    .filter((d) => d.signal !== 0)
    .sort((a, b) => {
      return new Date(b.date) - new Date(a.date);
    });

  if (signals.length === 0) {
    return (
      <div className="empty-state">
        <p>暂无买卖信号</p>
      </div>
    );
  }

  return (
    <div className="signal-list">
      {signals.map((s, i) => {
        const weakSell = isWeakSellInStrongTrend(s);
        return (
          <div key={i} className={`signal-item ${s.signal === 1 ? 'buy' : 'sell'}`}>
            <div className="signal-info">
              <span className="signal-date">{s.date}</span>
              <span className={`signal-type ${s.signal === 1 ? 'buy' : 'sell'}`}>
                {s.signal === 1 ? '买入信号' : '卖出信号'}
              </span>
              <span className="signal-price">¥{s.close}</span>
            </div>
            <div className="signal-score">
              {s.signal === 1
                ? '强度: ' + (s.buy_score * 100).toFixed(0) + '%'
                : '强度: ' + (s.sell_score * 100).toFixed(0) + '%'}
            </div>
            {weakSell && (
              <div className="signal-hint signal-hint-weak-sell" title="动能等级处于强势/极强或均线多头排列，且卖出信号强度较低，建议保留底仓跟随趋势">
                ⚠️ 强趋势中弱卖点，建议减仓 1/3
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
