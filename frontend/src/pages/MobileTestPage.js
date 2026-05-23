import React, { useState } from 'react';
import KlineChart from '../components/KlineChart';
import Watchlist from '../components/Watchlist';

const sampleWatchlist = [
  { code: '600519', name: '贵州茅台' },
  { code: '000001', name: '平安银行' },
  { code: '300750', name: '宁德时代' },
  { code: '601318', name: '中国平安' },
  { code: '600036', name: '招商银行' },
  { code: '000858', name: '五粮液' },
  { code: '002594', name: '比亚迪' },
  { code: '600030', name: '中信证券' },
  { code: '601888', name: '中国中免' },
  { code: '600276', name: '恒瑞医药' },
  { code: '300059', name: '东方财富' },
  { code: '600887', name: '伊利股份' },
  { code: '002415', name: '海康威视' },
  { code: '601398', name: '工商银行' },
  { code: '600900', name: '长江电力' },
  { code: 'AAPL', name: 'Apple' },
];

const sampleData = Array.from({ length: 60 }, (_, i) => {
  const base = 18 + Math.sin(i / 5) * 2 + i * 0.03;
  const open = Number((base + Math.sin(i) * 0.5).toFixed(2));
  const close = Number((base + Math.cos(i) * 0.5).toFixed(2));
  const high = Number((Math.max(open, close) + 0.8).toFixed(2));
  const low = Number((Math.min(open, close) - 0.8).toFixed(2));
  return {
    date: `2025-${String(Math.floor(i / 20) + 1).padStart(2, '0')}-${String((i % 20) + 1).padStart(2, '0')}`,
    open,
    close,
    high,
    low,
    volume: 800000 + i * 12000,
    ma5: Number((base + 0.2).toFixed(2)),
    ma10: Number((base - 0.1).toFixed(2)),
    ma20: Number((base - 0.35).toFixed(2)),
    boll_upper: Number((base + 2).toFixed(2)),
    boll_middle: Number(base.toFixed(2)),
    boll_lower: Number((base - 2).toFixed(2)),
    macd: Number((Math.sin(i / 6) * 0.5).toFixed(3)),
    macd_signal: Number((Math.sin(i / 6 - 0.4) * 0.35).toFixed(3)),
    macd_hist: Number((Math.sin(i / 4) * 0.25).toFixed(3)),
    signal: i === 45 ? 1 : i === 55 ? -1 : 0,
    buy_score: i === 45 ? 0.72 : 0,
    sell_score: i === 55 ? 0.66 : 0,
  };
});

export default function MobileTestPage() {
  const [stock, setStock] = useState(sampleWatchlist[0]);
  const stockData = {
    name: stock.name,
    data: sampleData,
    support_levels: [{ price: 17.2 }],
    resistance_levels: [{ price: 22.6 }],
    trade_advice: { stop_loss: 16.8, take_profit: 23.5, add_price: 19.6 },
  };

  return (
    <div className="app mobile-test-page">
      <header className="header">
        <div className="logo">
          <div className="logo-icon">📈</div>
          <span className="logo-text">移动端测试</span>
        </div>
        <div className="controls">
          <div className="input-group">
            <label>股票代码</label>
            <input className="input" value={stock.code} readOnly />
          </div>
          <button className="btn btn-primary">获取数据</button>
          <button className="btn btn-watchlist-add">加入自选</button>
        </div>
      </header>
      <div className="main-content">
        <Watchlist watchlist={sampleWatchlist} onSelect={setStock} onRemove={(code, e) => e.stopPropagation()} />
        <div className="chart-section">
          <div className="chart-tabs">
            <button className="tab active">默认策略</button>
            <button className="tab">激进策略</button>
            <button className="tab mobile-hidden">RSI</button>
            <button className="tab mobile-hidden">KDJ</button>
            <button className="tab mobile-hidden">信号扫描</button>
          </div>
          <div className="chart-legend">
            <div className="legend-item"><div className="legend-dot" style={{ background: '#ef4444' }}></div><span>B 买入</span></div>
            <div className="legend-item"><div className="legend-dot" style={{ background: '#3b82f6' }}></div><span>S 卖出</span></div>
          </div>
          <div className="chart-container">
            <KlineChart stockData={stockData} symbol={stock.code} hideLegendItems={['K线', 'MACD柱']} forceMobile />
          </div>
        </div>
        <div className="sidebar">
          <div className="sidebar-tabs">
            <button className="sidebar-tab active">买卖信号</button>
            <button className="sidebar-tab">回测结果</button>
          </div>
        </div>
      </div>
    </div>
  );
}
