import { useState } from 'react';

function isUsStock(code) {
  return /^[A-Za-z]/.test(code);
}

export default function Watchlist({ watchlist, onSelect, onRemove }) {
  const [activeTab, setActiveTab] = useState('a');

  const aStockList = watchlist.filter((s) => !isUsStock(s.code));
  const usStockList = watchlist.filter((s) => isUsStock(s.code));
  const displayList = activeTab === 'a' ? aStockList : usStockList;
  const mobileStocks = aStockList.slice(0, 15);

  return (
    <div className="watchlist-sidebar">
      <div className="watchlist-mobile-header">A股自选</div>
      <div className="watchlist-mobile-grid">
        {mobileStocks.map((stock, i) => (
          <button key={i} className="watchlist-mobile-card" onClick={() => onSelect(stock)}>
            <span className="watchlist-mobile-name">{stock.name}</span>
            <span className="watchlist-mobile-code">{stock.code}</span>
          </button>
        ))}
        {mobileStocks.length === 0 && <div className="watchlist-mobile-empty">暂无A股自选</div>}
      </div>
      <div className="watchlist-header">
        <span>⭐ 自选股</span>
      </div>
      <div className="watchlist-tabs">
        <button
          className={`watchlist-tab ${activeTab === 'a' ? 'active' : ''}`}
          onClick={() => setActiveTab('a')}
        >
          A股 ({aStockList.length})
        </button>
        <button
          className={`watchlist-tab ${activeTab === 'us' ? 'active' : ''}`}
          onClick={() => setActiveTab('us')}
        >
          美股 ({usStockList.length})
        </button>
      </div>
      <div className="watchlist-content">
        {displayList.map((stock, i) => (
          <div key={i} className="watchlist-item-card" onClick={() => onSelect(stock)}>
            <div className="watchlist-stock-info">
              <span className="watchlist-code">{stock.code}</span>
              <span className="watchlist-name">{stock.name}</span>
            </div>
            <button className="btn-delete-watchlist" onClick={(e) => onRemove(stock.code, e)}>
              ✕
            </button>
          </div>
        ))}
        {displayList.length === 0 && (
          <div className="watchlist-empty">
            <p>暂无自选股</p>
          </div>
        )}
      </div>
    </div>
  );
}
