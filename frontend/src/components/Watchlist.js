import { useState, useRef } from 'react';

function isUsStock(code) {
  return /^[A-Za-z]/.test(code);
}

export default function Watchlist({ watchlist, onSelect, onRemove, onReorder }) {
  const [activeTab, setActiveTab] = useState('a');
  const [dragIndex, setDragIndex] = useState(null);
  const [overIndex, setOverIndex] = useState(null);
  const dragNode = useRef(null);

  const aStockList = watchlist.filter((s) => !isUsStock(s.code));
  const usStockList = watchlist.filter((s) => isUsStock(s.code));
  const displayList = activeTab === 'a' ? aStockList : usStockList;
  const mobileStocks = aStockList.slice(0, 15);

  const handleDragStart = (e, index) => {
    dragNode.current = e.target;
    setDragIndex(index);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', String(index));
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (dragIndex !== null && index !== dragIndex) {
      setOverIndex(index);
    }
  };

  const handleDragLeave = () => {
    setOverIndex(null);
  };

  const handleDrop = (e, index) => {
    e.preventDefault();
    e.stopPropagation();
    if (dragIndex === null || dragIndex === index) {
      setDragIndex(null);
      setOverIndex(null);
      return;
    }
    const newList = [...displayList];
    const [moved] = newList.splice(dragIndex, 1);
    newList.splice(index, 0, moved);
    setDragIndex(null);
    setOverIndex(null);
    if (onReorder) onReorder(newList.map((s) => s.code));
  };

  const handleDragEnd = () => {
    setDragIndex(null);
    setOverIndex(null);
    dragNode.current = null;
  };

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
        <span className="watchlist-drag-hint">拖拽排序</span>
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
          <div
            key={stock.code}
            className={`watchlist-item-card${dragIndex === i ? ' dragging' : ''}${overIndex === i && dragIndex !== null ? ' drag-over' : ''}`}
            draggable
            onDragStart={(e) => handleDragStart(e, i)}
            onDragOver={(e) => handleDragOver(e, i)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, i)}
            onDragEnd={handleDragEnd}
            onClick={() => onSelect(stock)}
          >
            <div className="watchlist-drag-handle">⠿</div>
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
