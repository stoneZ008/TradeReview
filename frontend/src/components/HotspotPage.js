import React, { useState, useEffect } from 'react';
import './HotspotPage.css';
import {
  fetchHotspotSectors,
  fetchSectorDetail,
  fetchStockAttribution,
  fetchMarketOverview,
  refreshHotspotCache
} from '../api';

function HotspotPage({ onStockSelect }) {
  const [sectors, setSectors] = useState([]);
  const [marketOverview, setMarketOverview] = useState(null);
  const [sectorsLoading, setSectorsLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [sectorType, setSectorType] = useState('industry');
  const [selectedSector, setSelectedSector] = useState(null);
  const [sectorStocks, setSectorStocks] = useState([]);
  const [sectorAttribution, setSectorAttribution] = useState(null);
  const [stockAttribution, setStockAttribution] = useState(null);
  const [showAttributionModal, setShowAttributionModal] = useState(false);
  const [stockSearch, setStockSearch] = useState('');
  const [showAllStocks, setShowAllStocks] = useState(false);

  useEffect(() => {
    loadMarketOverview();
    loadSectors(sectorType);
  }, []);

  const loadMarketOverview = async () => {
    try {
      const data = await fetchMarketOverview();
      setMarketOverview(data);
    } catch (e) { console.error('加载市场概览失败:', e); }
  };

  const loadSectors = async (type) => {
    setSectorsLoading(true);
    try {
      const data = await fetchHotspotSectors(type, 30);
      setSectors(data);
    } catch (e) { console.error('加载热点板块失败:', e); }
    setSectorsLoading(false);
  };

  const handleSectorTypeChange = (type) => {
    if (type === sectorType) return;
    setSectorType(type);
    setSelectedSector(null);
    setSectorStocks([]);
    setSectorAttribution(null);
    loadSectors(type);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshHotspotCache();
      await loadSectors(sectorType);
      await loadMarketOverview();
    } catch (e) { console.error('刷新失败:', e); }
    setRefreshing(false);
  };

  const handleSectorClick = async (sector) => {
    setSelectedSector(sector);
    setShowAllStocks(false);
    setStockSearch('');
    setDetailLoading(true);
    try {
      const data = await fetchSectorDetail(sector.name, sectorType);
      setSectorStocks(data.stocks || []);
      setSectorAttribution(data.attribution || null);
    } catch (e) { console.error('加载板块详情失败:', e); }
    setDetailLoading(false);
  };

  const handleStockClick = async (stock) => {
    setDetailLoading(true);
    try {
      const data = await fetchStockAttribution(stock.code, stock.name);
      setStockAttribution(data);
      setShowAttributionModal(true);
    } catch (e) { console.error('加载个股归因失败:', e); }
    setDetailLoading(false);
  };

  const handleViewKline = () => {
    if (stockAttribution && onStockSelect) {
      onStockSelect(stockAttribution.code);
      setShowAttributionModal(false);
    }
  };

  const getChangeColor = (pct) => pct > 0 ? '#ef4444' : pct < 0 ? '#22c55e' : '#6b7280';

  const filteredStocks = sectorStocks.filter(s => {
    if (!stockSearch) return true;
    const q = stockSearch.toLowerCase();
    return s.name.toLowerCase().includes(q) || s.code.includes(stockSearch);
  });
  const displayStocks = showAllStocks ? filteredStocks : filteredStocks.slice(0, 15);

  return (
    <div className="hotspot-page">
      {sectors.length > 0 && (
        <div className="market-overview" style={{
          border: sectors[0].is_mock ? '2px solid #1976d2' : '1px solid var(--border-color)',
          background: sectors[0].is_mock ? 'rgba(25, 118, 210, 0.05)' : 'var(--bg-secondary)'
        }}>
          <div className="overview-header">
            <div className="overview-title">
              🔥 {sectors[0].trading_day || '今日'} 热点洞察
              {sectors[0].is_mock && (
                <span className="mock-badge">📊 示例数据</span>
              )}
            </div>
            <div className="overview-actions">
              <button
                className={`refresh-btn ${refreshing ? 'loading' : ''}`}
                onClick={handleRefresh}
                disabled={refreshing}
              >
                {refreshing ? '刷新中...' : '🔄 刷新数据'}
              </button>
              <span className="source-label">
                来源: {sectors[0].source === 'ths' ? '同花顺' : sectors[0].source === 'ths_concept' ? '同花顺概念' : sectors[0].source === 'em' ? '东方财富' : '模拟数据'}
              </span>
            </div>
          </div>
          <div className="hot-topic">
            <span>📊 共 {sectors.length} 个{sectorType === 'concept' ? '概念' : '行业'}板块 | 更新: {sectors[0].update_time?.split(' ')[1] || '--:--'}</span>
            {marketOverview && (
              <span className="market-status">
                市场状态: <span className={`status-${marketOverview.market_status === '强势' ? 'hot' : marketOverview.market_status === '震荡' ? 'normal' : 'cold'}`}>
                  {marketOverview.market_status}
                </span>
              </span>
            )}
            {marketOverview && marketOverview.total_turnover_text && (
              <span className="turnover-tag">
                💰 今日成交: <strong>{marketOverview.total_turnover_text}</strong>
                {marketOverview.turnover_source === 'mock' && (
                  <span style={{ color: '#f59e0b', fontSize: '12px', marginLeft: '4px' }}>(示例)</span>
                )}
              </span>
            )}
          </div>
        </div>
      )}

      <div className="content-grid">
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">🔥 板块排行</div>
            <div className="sector-type-tabs">
              <button className={`sector-type-tab ${sectorType === 'industry' ? 'active' : ''}`} onClick={() => handleSectorTypeChange('industry')}>行业</button>
              <button className={`sector-type-tab ${sectorType === 'concept' ? 'active' : ''}`} onClick={() => handleSectorTypeChange('concept')}>概念</button>
            </div>
          </div>
          <div className="panel-content sector-grid-content">
            {sectorsLoading ? <div className="loading-spinner"><div className="spinner"></div></div> : sectors.length === 0 ? <div className="empty-state">暂无数据</div> : (
              <div className="sector-grid">
                {sectors.map((sector, idx) => {
                  const pct = sector.change_pct;
                  const tone = pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat';
                  const intensity = Math.min(Math.abs(pct) / 5, 1);
                  const isActive = selectedSector?.name === sector.name;
                  return (
                    <div
                      key={idx}
                      className={`sector-tile ${tone}${isActive ? ' active' : ''}`}
                      style={{ '--tile-intensity': intensity }}
                      onClick={() => handleSectorClick(sector)}
                      title={`${sector.name}  ${pct > 0 ? '+' : ''}${pct}%  |  ${sector.up_count}涨 / ${sector.down_count}跌`}
                    >
                      <div className="tile-name">{sector.name}</div>
                      <div className="tile-pct">{pct > 0 ? '+' : ''}{pct}%</div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {selectedSector && (
          <div className="panel">
            <div className="panel-header">
              <div className="panel-title">📊 {selectedSector.name} - 板块详情</div>
              <button className="modal-close" onClick={() => { setSelectedSector(null); setSectorStocks([]); setSectorAttribution(null); }}>×</button>
            </div>
            <div className="panel-content">
              {detailLoading ? (
                <div className="loading-spinner"><div className="spinner"></div></div>
              ) : (
                <>
                  {sectorAttribution && (
                    <div className="sector-attribution">
                      <div className="attribution-summary">
                        <div className="summary-item">
                          <span className="label">平均涨幅</span>
                          <span className="value" style={{ color: getChangeColor(sectorAttribution.change_pct) }}>
                            {sectorAttribution.change_pct > 0 ? '+' : ''}{sectorAttribution.change_pct}%
                          </span>
                        </div>
                        <div className="summary-item">
                          <span className="label">上涨家数</span>
                          <span className="value up">{sectorAttribution.up_count}</span>
                        </div>
                        <div className="summary-item">
                          <span className="label">下跌家数</span>
                          <span className="value down">{sectorAttribution.down_count}</span>
                        </div>
                      </div>

                      {sectorAttribution.driving_factors && (
                        <div className="driving-factors">
                          <div className="factors-title">驱动因素</div>
                          <div className="factors-list">
                            {sectorAttribution.driving_factors.map((f, i) => (
                              <div key={i} className="factor-item">
                                <div className="factor-header">
                                  <span className="factor-type">{f.type}</span>
                                  <span className="factor-weight">{Math.round(f.weight * 100)}%</span>
                                </div>
                                <div className="factor-bar">
                                  <div className="factor-progress" style={{ width: `${f.weight * 100}%` }}></div>
                                </div>
                                <div className="factor-desc">{f.description}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {sectorAttribution.lead_stocks && sectorAttribution.lead_stocks.length > 0 && (
                        <div className="lead-stocks">
                          <div className="stocks-title">🔥 领涨个股</div>
                          <div className="stocks-grid">
                            {sectorAttribution.lead_stocks.slice(0, 3).map((s, i) => (
                              <div key={i} className="stock-card" onClick={() => handleStockClick(s)}>
                                <div className="stock-card-name">{s.name}</div>
                                <div className="stock-card-change" style={{ color: getChangeColor(s.change_pct) }}>
                                  {s.change_pct > 0 ? '+' : ''}{s.change_pct}%
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="stocks-table-header">
                    <span className="stocks-table-title">成分股列表</span>
                    <input
                      className="stock-search-input"
                      type="text"
                      placeholder="搜索代码/名称"
                      value={stockSearch}
                      onChange={(e) => { setStockSearch(e.target.value); setShowAllStocks(false); }}
                    />
                  </div>
                  <table className="table">
                    <thead><tr><th>股票</th><th>涨跌幅</th><th>现价</th><th>换手率</th></tr></thead>
                    <tbody>
                      {displayStocks.map((stock, idx) => (
                        <tr key={idx} onClick={() => handleStockClick(stock)}>
                          <td><div className="stock-name">{stock.name}</div><div className="stock-code">{stock.code}</div></td>
                          <td><span className="change-pct" style={{ color: getChangeColor(stock.change_pct) }}>{stock.change_pct > 0 ? '+' : ''}{stock.change_pct}%</span></td>
                          <td>{stock.price}</td>
                          <td>{stock.turnover_rate || '-'}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {filteredStocks.length > 15 && (
                    <div className="show-more-row" onClick={() => setShowAllStocks(v => !v)}>
                      {showAllStocks ? '收起' : `展开全部 (${filteredStocks.length} 只)`}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {showAttributionModal && stockAttribution && (
        <div className="modal-overlay" onClick={() => setShowAttributionModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">📊 {stockAttribution.name} - 归因分析</div>
              <button className="modal-close" onClick={() => setShowAttributionModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="section">
                <div className="section-title">基本信息</div>
                <div className="attribution-item">
                  <span>当前价格</span>
                  <span style={{ color: getChangeColor(stockAttribution.change_pct), fontWeight: 600 }}>
                    {stockAttribution.price} ({stockAttribution.change_pct > 0 ? '+' : ''}{stockAttribution.change_pct}%)
                  </span>
                </div>
              </div>

              {stockAttribution.attribution?.concepts && stockAttribution.attribution.concepts.length > 0 && (
                <div className="section">
                  <div className="section-title">概念标签</div>
                  <div className="signals">
                    {stockAttribution.attribution.concepts.map((c, i) => (
                      <span key={i} className="signal-tag">{c.name}</span>
                    ))}
                  </div>
                </div>
              )}

              {stockAttribution.technical_signals && stockAttribution.technical_signals.length > 0 && (
                <div className="section">
                  <div className="section-title">技术信号</div>
                  <div className="signals">
                    {stockAttribution.technical_signals.map((s, i) => (
                      <span key={i} className="signal-tag">{s}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="modal-footer-actions">
                <button className="btn-view-kline" onClick={handleViewKline}>
                  📈 查看 K 线分析
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default HotspotPage;
