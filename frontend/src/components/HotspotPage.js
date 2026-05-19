import React, { useState, useEffect, useCallback } from 'react';
import ReactECharts from 'echarts-for-react';
import './HotspotPage.css';
import {
  fetchHotspotSectors,
  fetchSectorDetail,
  fetchHotspotStocks,
  fetchStockAttribution,
  fetchFundFlow,
  fetchMarketOverview,
  refreshHotspotCache
} from '../api';

function HotspotPage({ onStockSelect }) {
  const [activeTab, setActiveTab] = useState('sectors');
  const [sectorType, setSectorType] = useState('concept');
  const [sectors, setSectors] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [fundFlow, setFundFlow] = useState([]);
  const [marketOverview, setMarketOverview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSector, setSelectedSector] = useState(null);
  const [sectorStocks, setSectorStocks] = useState([]);
  const [sectorAttribution, setSectorAttribution] = useState(null);
  const [stockAttribution, setStockAttribution] = useState(null);
  const [showAttributionModal, setShowAttributionModal] = useState(false);

  useEffect(() => {
    loadMarketOverview();
  }, []);

  useEffect(() => {
    if (activeTab === 'sectors') loadSectors();
    else if (activeTab === 'stocks') loadHotStocks();
    else if (activeTab === 'fundflow') loadFundFlow();
  }, [activeTab, sectorType]);

  const loadMarketOverview = async () => {
    try {
      const data = await fetchMarketOverview();
      setMarketOverview(data);
    } catch (e) { console.error('加载市场概览失败:', e); }
  };

  const loadSectors = async () => {
    setLoading(true);
    try {
      const data = await fetchHotspotSectors(sectorType, 30);
      setSectors(data);
    } catch (e) { console.error('加载热点板块失败:', e); }
    setLoading(false);
  };

  const loadHotStocks = async () => {
    setLoading(true);
    try {
      const data = await fetchHotspotStocks(30);
      setStocks(data);
    } catch (e) { console.error('加载热门个股失败:', e); }
    setLoading(false);
  };

  const loadFundFlow = async () => {
    setLoading(true);
    try {
      const data = await fetchFundFlow();
      setFundFlow(data);
    } catch (e) { console.error('加载资金流向失败:', e); }
    setLoading(false);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshHotspotCache();
      await loadData();
    } catch (e) { console.error('刷新失败:', e); }
    setRefreshing(false);
  };

  const loadData = useCallback(() => {
    if (activeTab === 'sectors') loadSectors();
    else if (activeTab === 'stocks') loadHotStocks();
    else if (activeTab === 'fundflow') loadFundFlow();
  }, [activeTab, sectorType]);

  const handleSectorClick = async (sector) => {
    setSelectedSector(sector);
    setLoading(true);
    try {
      const data = await fetchSectorDetail(sector.name, sectorType);
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

  const formatFundFlow = (value) => {
    if (!value) return '0';
    const absValue = Math.abs(value);
    if (absValue >= 100000000) return `${(value / 100000000).toFixed(2)}亿`;
    if (absValue >= 10000) return `${(value / 10000).toFixed(2)}万`;
    return value.toFixed(0);
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
                来源: {sectors[0].source === 'ths' ? '同花顺' : sectors[0].source === 'em' ? '东方财富' : '同花顺概念'}
              </span>
            </div>
          </div>
          <div className="hot-topic">
            <span>📊 共 {sectors.length} 个板块 | 更新: {sectors[0].update_time?.split(' ')[1] || '--:--'}</span>
            {marketOverview && (
              <span className="market-status">
                市场状态: <span className={`status-${marketOverview.market_status === '强势' ? 'hot' : marketOverview.market_status === '震荡' ? 'normal' : 'cold'}`}>
                  {marketOverview.market_status}
                </span>
              </span>
            )}
            {sectors[0].is_mock && (
              <span className="mock-tip">💡 Linux服务器部署可启用真实同花顺API</span>
            )}
          </div>
         </div>
       )}

      <div className="tabs">
        <button className={`tab ${activeTab === 'sectors' ? 'active' : ''}`} onClick={() => setActiveTab('sectors')}>热点板块</button>
        <button className={`tab ${activeTab === 'stocks' ? 'active' : ''}`} onClick={() => setActiveTab('stocks')}>热门个股</button>
        <button className={`tab ${activeTab === 'fundflow' ? 'active' : ''}`} onClick={() => setActiveTab('fundflow')}>资金流向</button>
      </div>

      {activeTab === 'sectors' && (
        <div className="sub-tabs">
          <button className={`sub-tab ${sectorType === 'concept' ? 'active' : ''}`} onClick={() => setSectorType('concept')}>概念板块</button>
          <button className={`sub-tab ${sectorType === 'industry' ? 'active' : ''}`} onClick={() => setSectorType('industry')}>行业板块</button>
        </div>
      )}

      <div className="content-grid">
        {activeTab === 'sectors' && (
          <div className="panel">
            <div className="panel-header"><div className="panel-title">🔥 热点板块排行</div></div>
            <div className="panel-content">
              {loading ? <div className="loading-spinner"><div className="spinner"></div></div> : sectors.length === 0 ? <div className="empty-state">暂无数据</div> : (
                <table className="table">
                  <thead><tr><th>排名</th><th>板块名称</th><th>涨跌幅</th><th>涨跌家数</th></tr></thead>
                  <tbody>
                    {sectors.map((sector, idx) => (
                      <tr key={idx} onClick={() => handleSectorClick(sector)}>
                        <td><div className={getRankBadgeClass(sector.rank)}>{sector.rank}</div></td>
                        <td><div className="stock-name">{sector.name}</div></td>
                        <td><span className="change-pct" style={{ color: getChangeColor(sector.change_pct) }}>{sector.change_pct > 0 ? '+' : ''}{sector.change_pct}%</span></td>
                        <td><span style={{ color: '#ef4444' }}>{sector.up_count}涨</span> / <span style={{ color: '#22c55e' }}>{sector.down_count}跌</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {activeTab === 'stocks' && (
          <div className="panel">
            <div className="panel-header"><div className="panel-title">🔥 热门个股排行</div></div>
            <div className="panel-content">
              {loading ? <div className="loading-spinner"><div className="spinner"></div></div> : stocks.length === 0 ? <div className="empty-state">暂无数据</div> : (
                <table className="table">
                  <thead><tr><th>排名</th><th>股票</th><th>涨跌幅</th><th>现价</th></tr></thead>
                  <tbody>
                    {stocks.map((stock, idx) => (
                      <tr key={idx} onClick={() => handleStockClick(stock)}>
                        <td><div className={getRankBadgeClass(stock.rank)}>{stock.rank}</div></td>
                        <td><div className="stock-name">{stock.name}</div><div className="stock-code">{stock.code}</div></td>
                        <td><span className="change-pct" style={{ color: getChangeColor(stock.change_pct) }}>{stock.change_pct > 0 ? '+' : ''}{stock.change_pct}%</span></td>
                        <td>{stock.price}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {activeTab === 'fundflow' && (
          <>
            <div className="panel chart-panel">
              <div className="panel-header"><div className="panel-title">📊 资金流向分布</div></div>
              <div className="chart-container">
                {fundFlow.length > 0 && (
                  <ReactECharts
                    option={{
                      tooltip: { trigger: 'item' },
                      legend: { orient: 'vertical', left: 'left', top: 'center' },
                      series: [{
                        name: '资金构成',
                        type: 'pie',
                        radius: ['40%', '70%'],
                        center: ['60%', '50%'],
                        avoidLabelOverlap: false,
                        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
                        label: { show: false },
                        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
                        labelLine: { show: false },
                        data: [
                          { value: Math.abs(fundFlow.reduce((a, b) => a + b.super_large_net_inflow, 0)), name: '超大单', itemStyle: { color: '#ef4444' } },
                          { value: Math.abs(fundFlow.reduce((a, b) => a + b.large_net_inflow, 0)), name: '大单', itemStyle: { color: '#f97316' } },
                          { value: Math.abs(fundFlow.reduce((a, b) => a + b.medium_net_inflow, 0)), name: '中单', itemStyle: { color: '#eab308' } },
                          { value: Math.abs(fundFlow.reduce((a, b) => a + b.small_net_inflow, 0)), name: '小单', itemStyle: { color: '#22c55e' } },
                        ]
                      }]
                    }}
                    style={{ height: '300px', width: '100%' }}
                  />
                )}
              </div>
            </div>

            <div className="panel chart-panel">
              <div className="panel-header"><div className="panel-title">🔥 Top10 主力净流入</div></div>
              <div className="chart-container">
                {fundFlow.length > 0 && (
                  <ReactECharts
                    option={{
                      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
                      xAxis: { type: 'value', axisLabel: { formatter: (v) => (v / 100000000).toFixed(1) + '亿' } },
                      yAxis: { type: 'category', data: fundFlow.slice(0, 10).map(f => f.name).reverse() },
                      series: [{
                        name: '主力净流入',
                        type: 'bar',
                        data: fundFlow.slice(0, 10).map(f => f.main_net_inflow).reverse(),
                        itemStyle: {
                          color: (params) => params.value >= 0 ? '#ef4444' : '#22c55e',
                          borderRadius: [0, 4, 4, 0]
                        },
                        label: { show: true, position: 'right', formatter: (p) => (p.value / 100000000).toFixed(2) + '亿' }
                      }]
                    }}
                    style={{ height: '350px', width: '100%' }}
                  />
                )}
              </div>
            </div>

            <div className="panel">
              <div className="panel-header"><div className="panel-title">💰 主力资金流向排行</div></div>
              <div className="panel-content">
                {loading ? <div className="loading-spinner"><div className="spinner"></div></div> : fundFlow.length === 0 ? <div className="empty-state">暂无数据</div> : (
                  <table className="table">
                    <thead><tr><th>排名</th><th>股票</th><th>涨跌幅</th><th>主力净流入</th></tr></thead>
                    <tbody>
                      {fundFlow.map((stock, idx) => (
                        <tr key={idx} onClick={() => handleStockClick(stock)}>
                          <td><div className={getRankBadgeClass(stock.rank)}>{stock.rank}</div></td>
                          <td><div className="stock-name">{stock.name}</div><div className="stock-code">{stock.code}</div></td>
                          <td><span className="change-pct" style={{ color: getChangeColor(stock.change_pct) }}>{stock.change_pct > 0 ? '+' : ''}{stock.change_pct}%</span></td>
                          <td style={{ color: getChangeColor(stock.main_net_inflow / 1000000) }}>{formatFundFlow(stock.main_net_inflow)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </>
        )}

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

              <div className="section">
                <div className="section-title">资金流向</div>
                <div className="attribution-item">
                  <span>主力净流入</span>
                  <span style={{ color: getChangeColor(stockAttribution.fund_flow?.main_net_inflow / 1000000) }}>
                    {formatFundFlow(stockAttribution.fund_flow?.main_net_inflow || 0)}
                  </span>
                </div>
                <div className="attribution-item">
                  <span>超大单净流入</span>
                  <span style={{ color: getChangeColor(stockAttribution.fund_flow?.super_large_net_inflow / 1000000) }}>
                    {formatFundFlow(stockAttribution.fund_flow?.super_large_net_inflow || 0)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default HotspotPage;
