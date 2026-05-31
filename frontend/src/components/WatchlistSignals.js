import React, { useEffect, useState } from 'react';
import { fetchWatchlistSignals, refreshWatchlistSignals } from '../api';

function formatPct(v) {
  if (v === null || v === undefined) return '-';
  const sign = v > 0 ? '+' : '';
  return `${sign}${Number(v).toFixed(2)}%`;
}

function pctColor(v) {
  if (v === null || v === undefined) return 'var(--text-secondary)';
  if (v > 0) return '#ef4444';
  if (v < 0) return '#22c55e';
  return 'var(--text-secondary)';
}

function signalBadge(sig) {
  if (sig === 1) {
    return (
      <span style={{
        display: 'inline-block', padding: '2px 8px', borderRadius: '4px',
        background: '#ef4444', color: '#fff', fontSize: '12px', fontWeight: 600,
      }}>B 买入</span>
    );
  }
  if (sig === -1) {
    return (
      <span style={{
        display: 'inline-block', padding: '2px 8px', borderRadius: '4px',
        background: '#3b82f6', color: '#fff', fontSize: '12px', fontWeight: 600,
      }}>S 卖出</span>
    );
  }
  return <span style={{ color: 'var(--text-secondary)' }}>-</span>;
}

export default function WatchlistSignals({ onStockSelect }) {
  const [snapshots, setSnapshots] = useState([]);
  const [snapshotDate, setSnapshotDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetchWatchlistSignals();
      setSnapshots(res.data || []);
      setSnapshotDate(res.snapshot_date || '');
    } catch (e) {
      setError(e.message || '加载失败');
    }
    setLoading(false);
  };

  const handleRefresh = async () => {
    if (!window.confirm('确认重新扫描？将覆盖当日快照（耗时较长）')) return;
    setLoading(true);
    setError('');
    try {
      const res = await refreshWatchlistSignals();
      setSnapshots(res.data || []);
      setSnapshotDate(res.snapshot_date || '');
    } catch (e) {
      setError(e.message || '刷新失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const formatDate = (d) => {
    if (!d || d.length !== 8) return d;
    return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`;
  };

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      padding: '16px',
      overflow: 'hidden',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '12px',
        gap: '12px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h3 className="watchlist-signals-title" style={{ margin: 0, color: 'var(--text-primary)' }}>📊 自选股信号扫描</h3>
          {snapshotDate && (
            <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              快照日期：{formatDate(snapshotDate)}
            </span>
          )}
          <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            共 {snapshots.length} 只 A 股
          </span>
        </div>
        <button
          className="btn btn-secondary"
          onClick={handleRefresh}
          disabled={loading}
          style={{ fontSize: '13px' }}
        >
          {loading ? '加载中...' : '🔄 刷新'}
        </button>
      </div>

      {error && (
        <div style={{
          padding: '8px 12px',
          background: 'rgba(239,68,68,0.1)',
          color: '#ef4444',
          borderRadius: '4px',
          marginBottom: '12px',
          fontSize: '13px',
        }}>{error}</div>
      )}

      <div style={{ flex: 1, overflow: 'auto', border: '1px solid var(--border-color)', borderRadius: '4px' }}>
        <table className="watchlist-signals-table" style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '13px',
          color: 'var(--text-primary)',
        }}>
          <thead style={{
            position: 'sticky',
            top: 0,
            background: 'var(--bg-secondary)',
            zIndex: 1,
          }}>
            <tr>
              <th className="col-code" style={thStyle}>代码</th>
              <th style={thStyle}>名称</th>
              <th className="col-close" style={{ ...thStyle, textAlign: 'right' }}>最近收盘价</th>
              <th style={{ ...thStyle, textAlign: 'right' }}>涨跌幅</th>
              <th style={thStyle}>最近信号</th>
              <th className="col-date" style={thStyle}>信号日期</th>
              <th style={{ ...thStyle, textAlign: 'center' }}>今日触发</th>
            </tr>
          </thead>
          <tbody>
            {snapshots.length === 0 && !loading && (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '32px', color: 'var(--text-secondary)' }}>
                  暂无数据。请先添加 A 股到自选股。
                </td>
              </tr>
            )}
            {snapshots.map((row) => (
              <tr
                key={row.stock_code}
                onClick={() => onStockSelect && onStockSelect(row.stock_code)}
                style={{
                  cursor: 'pointer',
                  borderTop: '1px solid var(--border-color)',
                  background: row.has_signal_today ? 'rgba(251, 191, 36, 0.08)' : 'transparent',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(59,130,246,0.08)'}
                onMouseLeave={(e) => e.currentTarget.style.background = row.has_signal_today ? 'rgba(251, 191, 36, 0.08)' : 'transparent'}
              >
                <td className="col-code" style={tdStyle}>{row.stock_code}</td>
                <td style={tdStyle}>{row.stock_name}</td>
                <td className="col-close" style={{ ...tdStyle, textAlign: 'right' }}>
                  {row.close_price !== null ? row.close_price.toFixed(2) : '-'}
                </td>
                <td style={{ ...tdStyle, textAlign: 'right', color: pctColor(row.pct_change), fontWeight: 600 }}>
                  {formatPct(row.pct_change)}
                </td>
                <td style={tdStyle}>{signalBadge(row.last_signal)}</td>
                <td className="col-date" style={tdStyle}>{row.last_signal_date || '-'}</td>
                <td style={{ ...tdStyle, textAlign: 'center' }}>
                  {row.has_signal_today ? (
                    <span style={{ color: '#fbbf24', fontSize: '16px' }}>⭐</span>
                  ) : (
                    <span style={{ color: 'var(--text-secondary)' }}>-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {loading && snapshots.length === 0 && (
        <div style={{ textAlign: 'center', padding: '16px', color: 'var(--text-secondary)' }}>
          首次加载需要扫描所有自选股，请稍候...
        </div>
      )}
    </div>
  );
}

const thStyle = {
  padding: '10px 12px',
  textAlign: 'left',
  fontWeight: 600,
  color: 'var(--text-primary)',
  borderBottom: '1px solid var(--border-color)',
};

const tdStyle = {
  padding: '10px 12px',
};
