import React, { useState, useCallback, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import HotspotPage from './components/HotspotPage';
import DaoPage from './components/DaoPage';
import KlineChart from './components/KlineChart';
import MACDChart from './components/MACDChart';
import RSIChart from './components/RSIChart';
import RSIStatus from './components/RSIStatus';
import KDJChart from './components/KDJChart';
import KDJStatus from './components/KDJStatus';
import EquityChart from './components/EquityChart';
import Watchlist from './components/Watchlist';
import WatchlistSignals from './components/WatchlistSignals';
import BatchSignalScanner from './components/BatchSignalScanner';
import SignalPanel from './components/SignalPanel';
import BacktestPanel from './components/BacktestPanel';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import AdminPage from './pages/AdminPage';
import SubscriptionPage from './pages/SubscriptionPage';
import MobileTestPage from './pages/MobileTestPage';
import { fetchStockData as apiFetchStockData, fetchExperimentalStock as apiFetchExperimentalStock, runBacktest as apiRunBacktest, loadWatchlist as apiLoadWatchlist, addToWatchlist as apiAddToWatchlist, removeFromWatchlist as apiRemoveFromWatchlist } from './api';

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-primary)'
    }}>
      <div style={{ color: 'var(--text-primary)' }}>加载中...</div>
    </div>
  );
  return isAuthenticated ? children : <Navigate to="/login" />;
}

function HomePage() {
  const { user, logout, isAuthenticated, hasRole, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [symbol, setSymbol] = useState('');
  const [inputSymbol, setInputSymbol] = useState('');
  const [activePage, setActivePage] = useState('shu');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [scanResults, setScanResults] = useState([]);
  const [scanJsonText, setScanJsonText] = useState('');

  const hasDaoAccess = React.useMemo(() => {
    if (!user) return false;
    const roles = user.roles || [];
    if (roles.includes('admin') || roles.includes('super_admin')) return true;
    const userRole = roles[0];
    return userRole === 'user_pro';
  }, [user]);

  const hasKline2Access = true;

  const hasHotspotAccess = React.useMemo(() => {
    if (!user) return false;
    const roles = user.roles || [];
    return roles.includes('admin') || roles.includes('super_admin');
  }, [user]);

  const hasScanAccess = React.useMemo(() => {
    if (!user) return false;
    const roles = user.roles || [];
    return roles.includes('admin') || roles.includes('super_admin');
  }, [user]);

  React.useEffect(() => {
    if (!hasDaoAccess && activePage === 'dao') {
      setActivePage('shu');
    }
    if (!hasHotspotAccess && activePage === 'hotspot') {
      setActivePage('shu');
    }
    if (!hasScanAccess && activePage === 'scan') {
      setActivePage('shu');
    }
  }, [hasDaoAccess, hasHotspotAccess, hasScanAccess, activePage]);

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
  const [stockDataV2, setStockDataV2] = useState(null);
  const [activeChart, setActiveChart] = useState('kline');
  const [activeTab, setActiveTab] = useState('signals');
  const [backtestResult, setBacktestResult] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [rsiPeriod, setRsiPeriod] = useState(14);
  const userMenuRef = useRef(null);

  React.useEffect(() => {
    if (isAuthenticated) {
      handleLoadWatchlist();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    };
    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);



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
    setInputSymbol(stock.code);
    fetchDataForCode(stock.code);
  };

  const handleStockSelectFromDao = (code) => {
    setSymbol(code);
    setInputSymbol(code);
    setActivePage('shu');
    fetchDataForCode(code);
  };

  const handleAddToWatchlist = async () => {
    if (!isAuthenticated) {
      alert('请先登录');
      return;
    }
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

  const isMobileView = () => window.innerWidth <= 768;

  const trimDataForMobile = (data) => {
    if (!data?.data || !isMobileView()) return data;
    if (data.data.length > 40) {
      return { ...data, data: data.data.slice(-40) };
    }
    return data;
  };

  const fetchDataForCode = async (code) => {
    if (!code) return;
    setLoading(true);
    try {
      const [defaultResult, aggressiveResult] = await Promise.allSettled([
        apiFetchStockData(code, startDate, endDate, rsiPeriod),
        apiFetchExperimentalStock(code, startDate, endDate, rsiPeriod),
      ]);
      if (defaultResult.status === 'fulfilled') {
        setStockData(trimDataForMobile(defaultResult.value));
      } else {
        throw defaultResult.reason;
      }
      if (aggressiveResult.status === 'fulfilled') {
        setStockDataV2(trimDataForMobile(aggressiveResult.value));
      } else {
        setStockDataV2(null);
        console.error('激进策略数据加载失败:', aggressiveResult.reason);
      }
    } catch (e) {
      alert(e.message || '获取数据失败，请确保后端服务已启动');
    }
    setLoading(false);
  };

  const fetchData = useCallback(async (code) => {
    const targetCode = code || symbol;
    if (!targetCode) {
      alert('请输入股票代码');
      return;
    }
    setSymbol(targetCode);
    setLoading(true);
    try {
      const data = await apiFetchStockData(targetCode, startDate, endDate, rsiPeriod);
      setStockData(trimDataForMobile(data));
      setStockDataV2(null);
    } catch (e) {
      alert(e.message || '获取数据失败，请确保后端服务已启动');
    }
    setLoading(false);
  }, [symbol, startDate, endDate, rsiPeriod]);

  const fetchV2Data = async (code = symbol) => {
    if (!code) {
      alert('请先获取股票数据');
      return;
    }
    if (stockDataV2) return;
    setLoading(true);
    try {
      const data = await apiFetchExperimentalStock(code, startDate, endDate, rsiPeriod);
      setStockDataV2(trimDataForMobile(data));
    } catch (e) {
      alert(e.message || '获取K线图2数据失败');
    }
    setLoading(false);
  };

  const handleChartChange = (chart) => {
    setActiveChart(chart);
    if (chart === 'kline2') {
      fetchV2Data();
    }
  };

  const getActiveStockData = () => activeChart === 'kline2' ? stockDataV2 : stockData;

  const runBacktest = async () => {
    if (!isAuthenticated) {
      alert('请先登录');
      return;
    }
    if (!symbol) {
      alert('请先获取股票数据');
      return;
    }
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
      case 'rsi': return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <RSIStatus stockData={stockData} rsiPeriod={rsiPeriod} onRsiPeriodChange={setRsiPeriod} />
          <div style={{ flex: 1, minHeight: 0 }}>
            <RSIChart stockData={stockData} symbol={symbol} rsiPeriod={rsiPeriod} />
          </div>
        </div>
      );
      case 'kdj': return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <KDJStatus stockData={stockData} />
          <div style={{ flex: 1, minHeight: 0 }}>
            <KDJChart stockData={stockData} symbol={symbol} />
          </div>
        </div>
      );
      case 'signals': return <WatchlistSignals onStockSelect={handleStockSelectFromDao} />;
      case 'backtest': return <EquityChart backtestResult={backtestResult} stockData={stockData} symbol={symbol} />;
      case 'kline2': return <KlineChart stockData={stockDataV2} symbol={symbol} titleSuffix="（激进策略）" showLatestInfo hideLegendItems={['K线', 'MACD柱']} />;
      default: return <KlineChart stockData={stockData} symbol={symbol} hideLegendItems={['K线', 'MACD柱']} />;
    }
  };

  const activeStockData = getActiveStockData();

  if (authLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-primary)'
      }}>
        <div style={{ color: 'var(--text-primary)' }}>加载中...</div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-icon">📈</div>
          <span className="logo-text">禅动参考</span>
        </div>

        <div className="nav-tabs">
          {hasDaoAccess && (
            <button
              className={`nav-tab ${activePage === 'dao' ? 'active' : ''}`}
              onClick={() => setActivePage('dao')}
            >
              认知之道
            </button>
          )}
          {hasHotspotAccess && (
            <button
              className={`nav-tab ${activePage === 'hotspot' ? 'active' : ''}`}
              onClick={() => setActivePage('hotspot')}
            >
              热点洞察
            </button>
          )}
          {hasScanAccess && (
            <button
              className={`nav-tab ${activePage === 'scan' ? 'active' : ''}`}
              onClick={() => setActivePage('scan')}
            >
              个股洞察
            </button>
          )}
          <button
            className={`nav-tab ${activePage === 'shu' ? 'active' : ''}`}
            onClick={() => setActivePage('shu')}
          >
            执行之术
          </button>
        </div>

        {activePage === 'shu' && (
          <div className="controls">
            <div className="input-group" style={{ position: 'relative' }}>
              <label>股票代码</label>
              <input
                className="input"
                value={inputSymbol}
                onChange={(e) => setInputSymbol(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    fetchData(inputSymbol);
                  }
                }}
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

            <button className="btn btn-primary" onClick={() => fetchData(inputSymbol)} disabled={loading}>
              {loading ? '加载中...' : '获取数据'}
            </button>

            <button className="btn btn-watchlist-add" onClick={handleAddToWatchlist} disabled={loading || !stockData}>
              ⭐ 加入自选
            </button>

            <button className="btn btn-secondary mobile-hidden" onClick={runBacktest} disabled={loading || !stockData}>
              运行回测
            </button>
          </div>
        )}

        <div className="user-menu-wrapper">
          {isAuthenticated ? (
            <div ref={userMenuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="user-menu-btn"
              >
                <span>{user?.username}</span>
                <span>▼</span>
              </button>
               {showUserMenu && (
                 <div className="user-dropdown">
                   <Link
                     to="/profile"
                     className="user-dropdown-item"
                     onClick={() => setShowUserMenu(false)}
                   >
                     个人中心
                   </Link>
                   <Link
                     to="/subscription"
                     className="user-dropdown-item"
                     onClick={() => setShowUserMenu(false)}
                   >
                     开通会员
                   </Link>
                    {(hasRole('admin') || hasRole('super_admin')) && (
                      <>
                        <Link
                          to="/admin"
                          className="user-dropdown-item"
                          onClick={() => setShowUserMenu(false)}
                        >
                          管理后台
                        </Link>
                      </>
                    )}

                   <button
                      onClick={() => { logout(); setShowUserMenu(false); navigate('/login'); }}
                      className="user-dropdown-item text-danger"
                    >
                      退出登录
                    </button>
                 </div>
               )}
            </div>
          ) : (
            <div style={{ display: 'flex', gap: '8px' }}>
              <Link to="/login" className="btn" style={{ background: 'transparent', color: 'var(--text-primary)' }}>
                登录
              </Link>
            </div>
          )}
        </div>
      </header>

      {activePage === 'dao' ? (
        <DaoPage onStockSelect={handleStockSelectFromDao} />
      ) : activePage === 'hotspot' ? (
        <HotspotPage onStockSelect={handleStockSelectFromDao} />
      ) : activePage === 'scan' ? (
        <BatchSignalScanner onStockSelect={handleStockSelectFromDao} results={scanResults} setResults={setScanResults} jsonText={scanJsonText} setJsonText={setScanJsonText} />
      ) : (
        <div className="main-content">
          <Watchlist watchlist={watchlist} onSelect={selectWatchStock} onRemove={handleRemoveFromWatchlist} />

          <div className="chart-section">
            <div className="chart-tabs">
              <button className={`tab ${activeChart === 'kline' ? 'active' : ''}`} onClick={() => handleChartChange('kline')}>
                默认策略
              </button>
              <button className={`tab ${activeChart === 'kline2' ? 'active' : ''}`} onClick={() => handleChartChange('kline2')}>
                激进策略
              </button>
              <button className={`tab mobile-hidden ${activeChart === 'rsi' ? 'active' : ''}`} onClick={() => handleChartChange('rsi')}>
                RSI
              </button>
              <button className={`tab mobile-hidden ${activeChart === 'kdj' ? 'active' : ''}`} onClick={() => handleChartChange('kdj')}>
                KDJ
              </button>
              <button className={`tab mobile-hidden ${activeChart === 'signals' ? 'active' : ''}`} onClick={() => handleChartChange('signals')}>
                信号扫描
              </button>
              {backtestResult && (
                <button className={`tab mobile-hidden ${activeChart === 'backtest' ? 'active' : ''}`} onClick={() => handleChartChange('backtest')}>
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
              {activeChart === 'signals' ? (
                renderChart()
              ) : !activeStockData ? (
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
                买卖信号 ({activeStockData?.summary?.buy_signals || 0}/{activeStockData?.summary?.sell_signals || 0})
              </button>
              <button className={`sidebar-tab ${activeTab === 'backtest' ? 'active' : ''}`} onClick={() => setActiveTab('backtest')}>
                回测结果
              </button>
            </div>

            <div className="sidebar-content">
              {activeTab === 'signals' ? <SignalPanel stockData={activeStockData} /> : <BacktestPanel backtestResult={backtestResult} />}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
         <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/profile" element={<PrivateRoute><ProfilePage /></PrivateRoute>} />
            <Route path="/subscription" element={<PrivateRoute><SubscriptionPage /></PrivateRoute>} />
             <Route path="/admin" element={<PrivateRoute><AdminPage /></PrivateRoute>} />
             <Route path="/mobile-test" element={<MobileTestPage />} />
             <Route path="/" element={<HomePage />} />
         </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
