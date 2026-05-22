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
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSector, setSelectedSector] = useState(null);
  const [sectorStocks, setSectorStocks] = useState([]);
  const [sectorAttribution, setSectorAttribution] = useState(null);
  const [stockAttribution, setStockAttribution] = useState(null);
  const [showAttributionModal, setShowAttributionModal] = useState(false);
  const [showBullReasons, setShowBullReasons] = useState(false);

  useEffect(() => {
    loadMarketOverview();
    loadSectors();
  }, []);

  const loadMarketOverview = async () => {
    try {
      const data = await fetchMarketOverview();
      setMarketOverview(data);
    } catch (e) { console.error('加载市场概览失败:', e); }
  };

  const loadSectors = async () => {
    setLoading(true);
    try {
      const data = await fetchHotspotSectors('industry', 30);
      setSectors(data);
    } catch (e) { console.error('加载热点板块失败:', e); }
    setLoading(false);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshHotspotCache();
      await loadSectors();
      await loadMarketOverview();
    } catch (e) { console.error('刷新失败:', e); }
    setRefreshing(false);
  };

  const handleSectorClick = async (sector) => {
    setSelectedSector(sector);
    setLoading(true);
    try {
      const data = await fetchSectorDetail(sector.name, 'industry');
      setSectorStocks(data.stocks || []);
      setSectorAttribution(data.attribution || null);
    } catch (e) { console.error('加载板块详情失败:', e); }
    setLoading(false);
  };

  const handleStockClick = async (stock) => {
    setLoading(true);
    try {
      const data = await fetchStockAttribution(stock.code, stock.name);
      setStockAttribution(data);
      setShowAttributionModal(true);
    } catch (e) { console.error('加载个股归因失败:', e); }
    setLoading(false);
  };

  const getChangeColor = (pct) => pct > 0 ? '#ef4444' : pct < 0 ? '#22c55e' : '#6b7280';
  const getRankBadgeClass = (rank) => rank === 1 ? 'rank-badge top1' : rank === 2 ? 'rank-badge top2' : rank === 3 ? 'rank-badge top3' : 'rank-badge other';

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
                来源: {sectors[0].source === 'ths' ? '同花顺' : sectors[0].source === 'em' ? '东方财富' : '模拟数据'}
              </span>
            </div>
          </div>
          <div className="hot-topic">
            <span>📊 共 {sectors.length} 个行业板块 | 更新: {sectors[0].update_time?.split(' ')[1] || '--:--'}</span>
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
              </span>
            )}
            {sectors[0].is_mock && (
              <span className="mock-tip">💡 Linux服务器部署可启用真实同花顺API</span>
            )}
          </div>

          {marketOverview && typeof marketOverview.is_bull_market !== 'undefined' && (
            <div className="bull-market-row">
              <span className={marketOverview.is_bull_market ? 'bull-badge' : 'bear-badge'}>
                {marketOverview.is_bull_market ? '🐂 牛市' : '🐻 非牛市'}
                {typeof marketOverview.bull_market_score === 'number' && (
                  <span className="bull-score"> · 评分 {marketOverview.bull_market_score}</span>
                )}
              </span>
              {marketOverview.bull_market_summary && (
                <span className="bull-summary">{marketOverview.bull_market_summary}</span>
              )}
              {Array.isArray(marketOverview.bull_market_reasons) && marketOverview.bull_market_reasons.length > 0 && (
                <button
                  className="reasons-toggle"
                  onClick={() => setShowBullReasons(v => !v)}
                >
                  判断依据 {showBullReasons ? '▴' : '▾'}
                </button>
              )}
            </div>
          )}

          {showBullReasons && marketOverview && Array.isArray(marketOverview.bull_market_reasons) && (
            <div className="bull-reasons">
              {marketOverview.bull_market_reasons.map((r, i) => (
                <div key={i} className={`reason-item ${r.hit ? 'hit' : 'miss'}`}>
                  <span className="reason-mark">{r.hit ? '✓' : '✗'}</span>
                  <span className="reason-label">{r.label}</span>
                  {typeof r.weight === 'number' && (
                    <span className="reason-weight">{r.weight}分</span>
                  )}
                  {r.detail && <span className="reason-detail">{r.detail}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="content-grid">
        <div className="panel">
          <div className="panel-header"><div className="panel-title">🔥 行业板块排行</div></div>
          <div className="panel-content sector-grid-content">
            {loading ? <div className="loading-spinner"><div className="spinner"></div></div> : sectors.length === 0 ? <div className="empty-state">暂无数据</div> : (
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

        {selectedSector && sectorStocks.length > 0 && (
          <div className="panel">
            <div className="panel-header">
              <div className="panel-title">📊 {selectedSector.name} - 板块详情</div>
              <button className="modal-close" onClick={() => { setSelectedSector(null); setSectorStocks([]); setSectorAttribution(null); }}>×</button>
            </div>
            <div className="panel-content">
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

                  {sectorAttribution.lead_stocks && (
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

              <div className="stocks-table-title">成分股列表</div>
              <table className="table">
                <thead><tr><th>股票</th><th>涨跌幅</th><th>现价</th><th>换手率</th></tr></thead>
                <tbody>
                  {sectorStocks.slice(0, 15).map((stock, idx) => (
                    <tr key={idx} onClick={() => handleStockClick(stock)}>
                      <td><div className="stock-name">{stock.name}</div><div className="stock-code">{stock.code}</div></td>
                      <td><span className="change-pct" style={{ color: getChangeColor(stock.change_pct) }}>{stock.change_pct > 0 ? '+' : ''}{stock.change_pct}%</span></td>
                      <td>{stock.price}</td>
                      <td>{stock.turnover_rate || '-'}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default HotspotPage;
