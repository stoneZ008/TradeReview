import React, { useState, useMemo } from 'react';
import { batchScanSignals } from '../api';

const SAMPLE_JSON = JSON.stringify({
  "AI光通信产业链": {
    "光模块": [
      {"公司名称": "中际旭创", "股票代码": "300308"},
      {"公司名称": "新易盛", "股票代码": "300502"},
      {"公司名称": "天孚通信", "股票代码": "300394"}
    ],
    "光芯片": [
      {"公司名称": "源杰科技", "股票代码": "688498"},
      {"公司名称": "长光华芯", "股票代码": "688048"}
    ]
  },
  "芯片与存储产业链": {
    "AI芯片（GPU/ASIC）": [
      {"公司名称": "寒武纪", "股票代码": "688256"},
      {"公司名称": "海光信息", "股票代码": "688041"}
    ],
    "存储（含HBM）": [
      {"公司名称": "兆易创新", "股票代码": "603986"},
      {"公司名称": "江波龙", "股票代码": "301308"}
    ]
  }
}, null, 2);

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

function extractStocks(jsonObj) {
  const stocks = [];
  function walk(obj, industry, subIndustry) {
    if (!obj || typeof obj !== 'object') return;
    if (Array.isArray(obj)) {
      for (const item of obj) {
        if (item && typeof item === 'object' && '股票代码' in item) {
          stocks.push({
            code: String(item['股票代码'] || '').trim(),
            name: String(item['公司名称'] || '').trim(),
            industry: industry || '',
            sub_industry: subIndustry || '',
          });
        }
      }
      return;
    }
    for (const key of Object.keys(obj)) {
      const val = obj[key];
      if (typeof val === 'object' && val !== null) {
        if (Array.isArray(val)) {
          walk(val, industry || key, subIndustry);
        } else {
          const nextIndustry = industry || key;
          walk(val, nextIndustry, '');
        }
      }
    }
  }
  walk(jsonObj, '', '');
  return stocks;
}

function parseNestedStocks(jsonObj) {
  const stocks = [];

  function walk(obj, industry, subIndustry) {
    if (!obj || typeof obj !== 'object') return;

    if (Array.isArray(obj)) {
      for (const item of obj) {
        if (item && typeof item === 'object' && '股票代码' in item) {
          stocks.push({
            code: String(item['股票代码'] || '').trim(),
            name: String(item['公司名称'] || '').trim(),
            industry,
            sub_industry: subIndustry,
          });
        }
      }
      return;
    }

    for (const key of Object.keys(obj)) {
      const val = obj[key];
      if (typeof val !== 'object' || val === null) continue;

      if (Array.isArray(val)) {
        walk(val, industry || key, subIndustry);
      } else {
        const nextIndustry = industry || key;
        for (const subKey of Object.keys(val)) {
          const subVal = val[subKey];
          if (Array.isArray(subVal)) {
            walk(subVal, nextIndustry, subKey);
          } else if (typeof subVal === 'object') {
            walk(subVal, nextIndustry, subKey);
          }
        }
      }
    }
  }

  walk(jsonObj, '', '');
  return stocks;
}

function groupByIndustry(results) {
  const groups = {};
  for (const r of results) {
    const ind = r.industry || '未分类';
    const sub = r.sub_industry || '未分类';
    if (!groups[ind]) groups[ind] = {};
    if (!groups[ind][sub]) groups[ind][sub] = [];
    groups[ind][sub].push(r);
  }
  return groups;
}

const thStyle = {
  padding: '10px 12px',
  textAlign: 'left',
  fontWeight: 600,
  color: 'var(--text-primary)',
  borderBottom: '1px solid var(--border-color)',
  whiteSpace: 'nowrap',
};

const tdStyle = {
  padding: '10px 12px',
  whiteSpace: 'nowrap',
};

export default function BatchSignalScanner({ onStockSelect, results, setResults, jsonText, setJsonText }) {
  const effectiveJsonText = jsonText || SAMPLE_JSON;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [collapsedGroups, setCollapsedGroups] = useState({});

  const grouped = useMemo(() => groupByIndustry(results), [results]);

  const signalCount = useMemo(() => results.filter(r => r.has_signal_today).length, [results]);

  const toggleGroup = (key) => {
    setCollapsedGroups(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleScan = async () => {
    setError('');
    setResults([]);

    let parsed;
    try {
      parsed = JSON.parse(effectiveJsonText);
    } catch (e) {
      setError('JSON 格式错误：' + e.message);
      return;
    }

    const stocks = parseNestedStocks(parsed);
    if (stocks.length === 0) {
      setError('未从 JSON 中提取到有效的股票数据，请确保包含"公司名称"和"股票代码"字段');
      return;
    }

    const validStocks = stocks.filter(s => {
      const code = s.code;
      return code && /^\d+$/.test(code) && /^[036]/.test(code);
    });

    if (validStocks.length === 0) {
      setError('没有有效的A股代码（需以0/3/6开头的纯数字）');
      return;
    }

    const uniqueMap = new Map();
    for (const s of validStocks) {
      if (!uniqueMap.has(s.code)) {
        uniqueMap.set(s.code, s);
      }
    }
    const uniqueStocks = Array.from(uniqueMap.values());

    setLoading(true);
    try {
      const res = await batchScanSignals(uniqueStocks);
      setResults(res.data || []);
    } catch (e) {
      setError(e.message || '扫描失败');
    }
    setLoading(false);
  };

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      gap: '16px',
      padding: '16px',
      overflow: 'hidden',
    }}>
      <div style={{
        width: '38%',
        minWidth: '320px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>📋 产业链JSON</h3>
          <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
            支持嵌套结构，自动提取"公司名称"+"股票代码"
          </span>
        </div>
        <textarea
          value={effectiveJsonText}
          onChange={(e) => setJsonText(e.target.value)}
          style={{
            flex: 1,
            width: '100%',
            resize: 'none',
            padding: '12px',
            borderRadius: '6px',
            border: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            fontFamily: "'SF Mono', 'Fira Code', 'Cascadia Code', monospace",
            fontSize: '13px',
            lineHeight: '1.5',
            outline: 'none',
          }}
          spellCheck={false}
          placeholder='粘贴包含"公司名称"和"股票代码"的JSON数据...'
        />
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            className="btn btn-primary"
            onClick={handleScan}
            disabled={loading}
            style={{ minWidth: '120px' }}
          >
            {loading ? '扫描中...' : '🔍 扫描信号'}
          </button>
          {loading && (
            <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              正在逐只扫描，约1秒/只，请耐心等待...
            </span>
          )}
        </div>
        {error && (
          <div style={{
            padding: '8px 12px',
            background: 'rgba(239,68,68,0.1)',
            color: '#ef4444',
            borderRadius: '4px',
            fontSize: '13px',
          }}>{error}</div>
        )}
      </div>

      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        border: '1px solid var(--border-color)',
        borderRadius: '6px',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 16px',
          borderBottom: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)',
        }}>
          <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>📊 扫描结果</h3>
          {results.length > 0 && (
            <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
              <span>共 {results.length} 只</span>
              <span style={{ color: '#fbbf24', fontWeight: 600 }}>⭐ 今日信号 {signalCount} 只</span>
            </div>
          )}
        </div>

        <div style={{ flex: 1, overflow: 'auto' }}>
          {results.length === 0 && !loading && (
            <div style={{
              textAlign: 'center',
              padding: '60px 20px',
              color: 'var(--text-secondary)',
            }}>
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>📋</div>
              <p>在左侧输入JSON数据，点击"扫描信号"查看结果</p>
            </div>
          )}

          {loading && results.length === 0 && (
            <div style={{
              textAlign: 'center',
              padding: '60px 20px',
              color: 'var(--text-secondary)',
            }}>
              <div className="spinner" style={{ margin: '0 auto 16px' }}></div>
              <p>正在扫描，请稍候...</p>
            </div>
          )}

          {Object.entries(grouped).map(([industry, subGroups]) => (
            <div key={industry}>
              {Object.entries(subGroups).map(([subIndustry, rows]) => {
                const groupKey = `${industry}|||${subIndustry}`;
                const collapsed = collapsedGroups[groupKey];
                const groupSignalCount = rows.filter(r => r.has_signal_today).length;
                return (
                  <div key={groupKey}>
                    <div
                      onClick={() => toggleGroup(groupKey)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '10px 16px',
                        background: 'var(--bg-secondary)',
                        borderBottom: '1px solid var(--border-color)',
                        cursor: 'pointer',
                        userSelect: 'none',
                      }}
                    >
                      <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                        {collapsed ? '▶' : '▼'}
                      </span>
                      <span style={{
                        color: 'var(--text-primary)',
                        fontWeight: 600,
                        fontSize: '14px',
                      }}>
                        {industry}
                        {subIndustry !== '未分类' && (
                          <span style={{ color: 'var(--text-secondary)', fontWeight: 400, marginLeft: '8px' }}>
                            / {subIndustry}
                          </span>
                        )}
                      </span>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '12px', marginLeft: 'auto' }}>
                        {rows.length} 只
                        {groupSignalCount > 0 && (
                          <span style={{ color: '#fbbf24', marginLeft: '8px' }}>⭐ {groupSignalCount}</span>
                        )}
                      </span>
                    </div>

                    {!collapsed && (
                      <table style={{
                        width: '100%',
                        borderCollapse: 'collapse',
                        fontSize: '13px',
                        color: 'var(--text-primary)',
                      }}>
                        <thead style={{
                          position: 'sticky',
                          top: 0,
                          background: 'var(--bg-primary)',
                          zIndex: 1,
                        }}>
                          <tr>
                            <th style={thStyle}>代码</th>
                            <th style={thStyle}>名称</th>
                            <th style={{ ...thStyle, textAlign: 'right' }}>收盘价</th>
                            <th style={{ ...thStyle, textAlign: 'right' }}>涨跌幅</th>
                            <th style={thStyle}>最近信号</th>
                            <th style={thStyle}>信号日期</th>
                            <th style={{ ...thStyle, textAlign: 'center' }}>今日触发</th>
                          </tr>
                        </thead>
                        <tbody>
                          {rows.map((row) => (
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
                              <td style={tdStyle}>{row.stock_code}</td>
                              <td style={tdStyle}>{row.stock_name}</td>
                              <td style={{ ...tdStyle, textAlign: 'right' }}>
                                {row.close_price !== null && row.close_price !== undefined
                                  ? Number(row.close_price).toFixed(2) : '-'}
                              </td>
                              <td style={{
                                ...tdStyle,
                                textAlign: 'right',
                                color: pctColor(row.pct_change),
                                fontWeight: 600,
                              }}>
                                {formatPct(row.pct_change)}
                              </td>
                              <td style={tdStyle}>{signalBadge(row.last_signal)}</td>
                              <td style={tdStyle}>{row.last_signal_date || '-'}</td>
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
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
