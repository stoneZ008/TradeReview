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
      {signals.map((s, i) => (
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
        </div>
      ))}
    </div>
  );
}
