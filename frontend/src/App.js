import React, { useState, useCallback } from 'react';
import LoginPage from './components/LoginPage';
import DaoPage from './components/DaoPage';
import KlineChart from './components/KlineChart';
import MACDChart from './components/MACDChart';
import RSIChart from './components/RSIChart';
import KDJChart from './components/KDJChart';
import EquityChart from './components/EquityChart';
import Watchlist from './components/Watchlist';
import SignalPanel from './components/SignalPanel';
import BacktestPanel from './components/BacktestPanel';
import { API_BASE, fetchStockData as apiFetchStockData, runBacktest as apiRunBacktest, loadWatchlist as apiLoadWatchlist, addToWatchlist as apiAddToWatchlist, removeFromWatchlist as apiRemoveFromWatchlist } from './api';

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [symbol, setSymbol] = useState('600519');
  const [activePage, setActivePage] = useState('shu');

  React.useEffect(() => {
    if (token) {
      fetch(`${API_BASE}/auth/me`, { headers: { Authorization: 'Bearer ' + token } })
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(d => { setUser(d.user); })
        .catch(() => { localStorage.removeItem('token'); localStorage.removeItem('user'); setToken(null); });
    }
  }, []);

  const handleLogin = (userData, userToken) => {
    setUser(userData);
    setToken(userToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setToken(null);
  };

  const getCurrentDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}${month}${day}`;
  };

  const [startDate, setStartDate] = useState('20250101');
  const [endDate, setEndDate] = useState(getCurrentDate());
  const [loading, setLoading] = useState(false);
  const [stockData, setStockData] = useState(null);
  const [activeChart, setActiveChart] = useState('kline');
  const [activeTab, setActiveTab] = useState('signals');
  const [backtestResult, setBacktestResult] = useState(null);
  const [watchlist, setWatchlist] = useState([]);

  React.useEffect(() => {
    handleLoadWatchlist();
  }, []);

  const handleLoadWatchlist = async () => {
    try {
      const data = await apiLoadWatchlist();
      setWatchlist(data);
    } catch (e) {
      console.error('加载自选股失败:', e);
    }
  };

  const selectWatchStock = (stock) => {
    setSymbol(stock.code);
    fetchDataForCode(stock.code);
  };

  const handleStockSelectFromDao = (code) => {
    setSymbol(code);
    setActivePage('shu');
    fetchDataForCode(code);
  };

  const handleAddToWatchlist = async () => {
    if (!stockData?.name || !symbol) {
      alert('请先获取股票数据');
      return;
    }
    try {
      const data = await apiAddToWatchlist(symbol, stockData.name);
      setWatchlist(data);
    } catch (e) {
      alert(e.message || '添加失败');
    }
  };

  const handleRemoveFromWatchlist = async (code, e) => {
    e.stopPropagation();
    try {
      const data = await apiRemoveFromWatchlist(code);
      setWatchlist(data);
    } catch (e) {
      console.error('删除自选股失败:', e);
    }
  };

  const fetchDataForCode = async (code) => {
    if (!code) return;
    setLoading(true);
    try {
      const data = await apiFetchStockData(code, startDate, endDate);
      setStockData(data);
    } catch (e) {
      alert(e.message || '获取数据失败，请确保后端服务已启动');
    }
    setLoading(false);
  };

  const fetchData = useCallback(async () => {
    if (!symbol) return;
    setLoading(true);
    try {
      const data = await apiFetchStockData(symbol, startDate, endDate);
      setStockData(data);
    } catch (e) {
      alert(e.message || '获取数据失败，请确保后端服务已启动');
    }
    setLoading(false);
  }, [symbol, startDate, endDate]);

  const runBacktest = async () => {
    if (!symbol) return;
    setLoading(true);
    try {
      const data = await apiRunBacktest(symbol, startDate, endDate);
      setBacktestResult(data);
      setActiveTab('backtest');
    } catch (e) {
      alert(e.message || '回测失败');
    }
    setLoading(false);
  };

  const renderChart = () => {
    switch (activeChart) {
      case 'macd': return <MACDChart stockData={stockData} symbol={symbol} />;
      case 'rsi': return <RSIChart stockData={stockData} symbol={symbol} />;
      case 'kdj': return <KDJChart stockData={stockData} symbol={symbol} />;
      case 'backtest': return <EquityChart backtestResult={backtestResult} stockData={stockData} symbol={symbol} />;
      default: return <KlineChart stockData={stockData} symbol={symbol} />;
    }
  };

  if (!user) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-icon">📈</div>
          <span className="logo-text">ATradeReview</span>
        </div>

        <div className="nav-tabs">
          <button
            className={`nav-tab ${activePage === 'dao' ? 'active' : ''}`}
            onClick={() => setActivePage('dao')}
          >
            认知之道
          </button>
          <button
            className={`nav-tab ${activePage === 'shu' ? 'active' : ''}`}
            onClick={() => setActivePage('shu')}
          >
            执行之术
          </button>
        </div>

        <div className="user-info">
          <span className="user-email">{user.email}</span>
          <button className="btn btn-logout" onClick={handleLogout}>退出</button>
        </div>

        {activePage === 'shu' && (
          <div className="controls">
            <div className="input-group" style={{ position: 'relative' }}>
              <label>股票代码</label>
              <input
                className="input"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="输入代码"
              />
            </div>

            <div className="input-group">
              <label>开始日期</label>
              <input
                className="input input-sm"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                placeholder="YYYYMMDD"
              />
            </div>

            <div className="input-group">
              <label>结束日期</label>
              <input
                className="input input-sm"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                placeholder="YYYYMMDD"
              />
            </div>

            <button className="btn btn-primary" onClick={fetchData} disabled={loading}>
              {loading ? '加载中...' : '获取数据'}
            </button>

            <button className="btn btn-watchlist-add" onClick={handleAddToWatchlist} disabled={loading || !stockData}>
              ⭐ 加入自选
            </button>

            <button className="btn btn-secondary" onClick={runBacktest} disabled={loading || !stockData}>
              运行回测
            </button>
          </div>
        )}
      </header>

      {activePage === 'dao' ? (
        <DaoPage onStockSelect={handleStockSelectFromDao} />
      ) : (
        <div className="main-content">
          <Watchlist watchlist={watchlist} onSelect={selectWatchStock} onRemove={handleRemoveFromWatchlist} />

          <div className="chart-section">
            <div className="chart-tabs">
              <button className={`tab ${activeChart === 'kline' ? 'active' : ''}`} onClick={() => setActiveChart('kline')}>
                K线图
              </button>
              <button className={`tab ${activeChart === 'rsi' ? 'active' : ''}`} onClick={() => setActiveChart('rsi')}>
                RSI
              </button>
              <button className={`tab ${activeChart === 'kdj' ? 'active' : ''}`} onClick={() => setActiveChart('kdj')}>
                KDJ
              </button>
              {backtestResult && (
                <button className={`tab ${activeChart === 'backtest' ? 'active' : ''}`} onClick={() => setActiveChart('backtest')}>
                  权益曲线
                </button>
              )}
            </div>

            <div className="chart-legend">
              <div className="legend-item">
                <div className="legend-dot" style={{ background: '#ef4444' }}></div>
                <span>B 买入</span>
              </div>
              <div className="legend-item">
                <div className="legend-dot" style={{ background: '#3b82f6' }}></div>
                <span>S 卖出</span>
              </div>
            </div>

            <div className="chart-container">
              {!stockData ? (
                <div className="empty-state">
                  <div className="empty-state-icon">📊</div>
                  <p className="empty-state-text">等待数据加载</p>
                  <p className="empty-state-hint">输入股票代码并点击"获取数据"</p>
                </div>
              ) : loading ? (
                <div className="loading">
                  <div className="spinner"></div>
                </div>
              ) : (
                renderChart()
              )}
            </div>
          </div>

          <div className="sidebar">
            <div className="sidebar-tabs">
              <button className={`sidebar-tab ${activeTab === 'signals' ? 'active' : ''}`} onClick={() => setActiveTab('signals')}>
                买卖信号 ({stockData?.summary?.buy_signals || 0}/{stockData?.summary?.sell_signals || 0})
              </button>
              <button className={`sidebar-tab ${activeTab === 'backtest' ? 'active' : ''}`} onClick={() => setActiveTab('backtest')}>
                回测结果
              </button>
            </div>

            <div className="sidebar-content">
              {activeTab === 'signals' ? <SignalPanel stockData={stockData} /> : <BacktestPanel backtestResult={backtestResult} />}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
