export default function Watchlist({ watchlist, onSelect, onRemove }) {
  return (
    <div className="watchlist-sidebar">
      <div className="watchlist-header">
        <span>⭐ 自选股 ({watchlist.length})</span>
      </div>
      <div className="watchlist-content">
        {watchlist.map((stock, i) => (
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
        {watchlist.length === 0 && (
          <div className="watchlist-empty">
            <p>暂无自选股</p>
          </div>
        )}
      </div>
    </div>
  );
}
