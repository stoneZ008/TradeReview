function renderMetrics(metrics) {
  if (!metrics) return null;
  const m = metrics;

  const items = [
    { label: '总收益率', value: (m.total_return || 0) + '%', positive: (m.total_return || 0) > 0 },
    {
      label: '年化收益率',
      value: (m.annual_return || 0) + '%',
      positive: (m.annual_return || 0) > 0,
    },
    { label: '最大回撤', value: (m.max_drawdown || 0) + '%', negative: true },
    { label: '胜率', value: (m.win_rate || 0) + '%', positive: (m.win_rate || 0) > 50 },
    { label: '总交易次数', value: m.total_trades || 0 },
    { label: '盈亏比', value: m.profit_loss_ratio || 0 },
    { label: '初始资金', value: '¥' + (m.initial_capital || 0).toLocaleString() },
    {
      label: '最终资金',
      value: '¥' + (m.final_equity || 0).toLocaleString(),
      positive: (m.final_equity || 0) > (m.initial_capital || 0),
    },
  ];

  return (
    <div className="metrics-grid">
      {items.map((item, i) => (
        <div key={i} className="metric-card">
          <div className="metric-label">{item.label}</div>
          <div
            className={
              'metric-value' + (item.positive ? ' positive' : item.negative ? ' negative' : '')
            }
          >
            {item.value}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function BacktestPanel({ backtestResult }) {
  if (!backtestResult) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📊</div>
        <p className="empty-state-text">尚未运行回测</p>
        <p className="empty-state-hint">点击"运行回测"按钮开始</p>
      </div>
    );
  }

  return (
    <div>
      <h3 style={{ marginBottom: 16 }}>回测指标</h3>
      {renderMetrics(backtestResult.metrics)}

      <h3
        style={{
          margin: '24px 0 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <span>交易记录</span>
        {backtestResult.trades.length > 0 && (
          <span style={{ fontSize: 13, color: '#a0a0a0', fontWeight: 'normal' }}>
            共 {backtestResult.trades.length} 笔 （买入{' '}
            {backtestResult.trades.filter((t) => t.type === 'buy').length} 笔， 卖出{' '}
            {backtestResult.trades.filter((t) => t.type === 'sell').length} 笔）
          </span>
        )}
      </h3>
      <div className="trade-list">
        {backtestResult.trades.length === 0 ? (
          <div className="empty-state">
            <p>暂无交易记录</p>
          </div>
        ) : (
          backtestResult.trades
            .slice()
            .reverse()
            .map((t, i) => (
              <div key={i} className="trade-item">
                <span className={'trade-type ' + t.type}>{t.type === 'buy' ? '买入' : '卖出'}</span>
                <div className="trade-info">
                  <span>{t.date}</span>
                  <span>¥{(t.price || 0).toFixed(2)}</span>
                  <span>{t.shares || 0}股</span>
                  {t.type === 'sell' && t.profit_pct != null && (
                    <span
                      className={'trade-profit ' + ((t.profit || 0) > 0 ? 'positive' : 'negative')}
                    >
                      {(t.profit || 0) > 0 ? '+' : ''}
                      {(t.profit_pct || 0).toFixed(2)}%
                    </span>
                  )}
                </div>
              </div>
            ))
        )}
      </div>
    </div>
  );
}
