import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  getStrategyTemplates,
  getStrategyDefault,
  getStrategyPresets,
  getStrategyPresetDetail,
  getStockStrategyConfigs,
  saveStockStrategyConfig,
  deleteStockStrategyConfig,
  strategyPreview,
  strategyBacktest,
} from '../api';

const UP = '#fa3e3e';
const DOWN = '#00b07c';
const ACCENT = '#c98a2a';

export default function StrategyConfigPanel({ symbol, startDate, endDate, rsiPeriod, stockName }) {
  const [templates, setTemplates] = useState([]);
  const [presets, setPresets] = useState([]);
  const [activePreset, setActivePreset] = useState('balanced');
  const [config, setConfig] = useState(null);
  const [savedConfigs, setSavedConfigs] = useState([]);
  const [configName, setConfigName] = useState('默认');
  const [previewResult, setPreviewResult] = useState(null);
  const [backtestResult, setBacktestResult] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [error, setError] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const autoPreviewRef = useRef(null);

  // 初始化：加载模板和预设
  useEffect(() => {
    (async () => {
      try {
        const [tmpls, psets, defCfg] = await Promise.all([
          getStrategyTemplates(),
          getStrategyPresets(),
          getStrategyDefault(),
        ]);
        setTemplates(tmpls);
        setPresets(psets);
        setConfig(defCfg);
      } catch (e) {
        setError(e.message);
      }
    })();
  }, []);

  // 加载已保存配置
  const loadSavedConfigs = useCallback(async () => {
    if (!symbol) return;
    try {
      const configs = await getStockStrategyConfigs(symbol);
      setSavedConfigs(configs);
      const defaultCfg = configs.find((c) => c.is_default);
      if (defaultCfg) {
        setConfig(defaultCfg.config);
        setConfigName(defaultCfg.config_name);
        setActivePreset('custom');
      }
    } catch (e) {
      console.error('加载已保存配置失败:', e);
    }
  }, [symbol]);

  useEffect(() => {
    if (symbol && config) loadSavedConfigs();
  }, [symbol]); // eslint-disable-line react-hooks/exhaustive-deps

  // 预设切换
  const handlePresetSelect = async (key) => {
    setActivePreset(key);
    setError(null);
    try {
      const cfg = await getStrategyPresetDetail(key);
      setConfig(cfg);
      setPreviewResult(null);
      setBacktestResult(null);
      // 自动预览
      if (symbol) {
        autoPreview(cfg);
      }
    } catch (e) {
      setError(e.message);
    }
  };

  // 自动预览（防抖）
  const autoPreview = useCallback(
    (cfg) => {
    if (autoPreviewRef.current) clearTimeout(autoPreviewRef.current);
    autoPreviewRef.current = setTimeout(async () => {
      if (!symbol || !cfg) return;
      setActionLoading('preview');
      try {
        const result = await strategyPreview(symbol, startDate, endDate, cfg, rsiPeriod);
        setPreviewResult(result);
        setBacktestResult(null);
      } catch (e) {
        // 静默失败，不打扰用户
      }
      setActionLoading(null);
    }, 600);
  },
  [symbol, startDate, endDate, rsiPeriod]
  );

  const updateStrategy = (key, field, value) => {
    setConfig((prev) => {
      const next = {
        ...prev,
        strategies: {
          ...prev.strategies,
          [key]: { ...prev.strategies[key], [field]: value },
        },
      };
      setActivePreset('custom');
      return next;
    });
  };

  const updateStrategyParam = (key, paramKey, value) => {
    setConfig((prev) => {
      const next = {
        ...prev,
        strategies: {
          ...prev.strategies,
          [key]: {
            ...prev.strategies[key],
            params: { ...prev.strategies[key].params, [paramKey]: value },
          },
        },
      };
      setActivePreset('custom');
      return next;
    });
  };

  const handleBacktest = async () => {
    if (!symbol || !config) return;
    setActionLoading('backtest');
    setError(null);
    try {
      const result = await strategyBacktest(symbol, startDate, endDate, config, rsiPeriod);
      setBacktestResult(result);
      setPreviewResult(null);
    } catch (e) {
      setError(e.message);
    }
    setActionLoading(null);
  };

  const handleSave = async () => {
    if (!symbol || !config) return;
    setActionLoading('save');
    setError(null);
    try {
      await saveStockStrategyConfig(symbol, config, configName, stockName || '', true);
      await loadSavedConfigs();
      setError(null);
    } catch (e) {
      setError(e.message);
    }
    setActionLoading(null);
  };

  const handleDelete = async () => {
    if (!symbol) return;
    setActionLoading('delete');
    setError(null);
    try {
      await deleteStockStrategyConfig(symbol, configName);
      const defCfg = await getStrategyDefault();
      setConfig(defCfg);
      setConfigName('默认');
      setActivePreset('balanced');
      await loadSavedConfigs();
    } catch (e) {
      setError(e.message);
    }
    setActionLoading(null);
  };

  const handleLoadSaved = async (cfgName) => {
    const found = savedConfigs.find((c) => c.config_name === cfgName);
    if (found) {
      setConfig(found.config);
      setConfigName(found.config_name);
      setActivePreset('custom');
      setPreviewResult(null);
      setBacktestResult(null);
    }
  };

  if (!config) {
    return (
      <div className="empty-state">
        <div className="spinner" style={{ margin: '20px auto' }}></div>
        <p className="empty-state-text">加载中...</p>
      </div>
    );
  }

  const buyTemplates = templates.filter((t) => t.type === 'buy');
  const sellTemplates = templates.filter((t) => t.type === 'sell');
  const enabledBuyCount = buyTemplates.filter((t) => config.strategies[t.key]?.enabled).length;
  const enabledSellCount = sellTemplates.filter((t) => config.strategies[t.key]?.enabled).length;
  const activePresetInfo = presets.find((p) => p.key === activePreset);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '4px 0' }}>
      {/* 预设方案选择 */}
      <div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>预设方案</div>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {presets.map((p) => (
            <button
              key={p.key}
              onClick={() => handlePresetSelect(p.key)}
              disabled={actionLoading !== null}
              style={{
                padding: '5px 12px',
                fontSize: 12,
                borderRadius: 6,
                cursor: 'pointer',
                border: activePreset === p.key ? '1px solid ' + ACCENT : '1px solid var(--border)',
                background: activePreset === p.key ? ACCENT : 'var(--bg-card)',
                color: activePreset === p.key ? '#fff' : 'var(--text-primary)',
                fontWeight: activePreset === p.key ? 600 : 400,
                transition: 'all 0.15s',
              }}
            >
              {p.name}
            </button>
          ))}
        </div>
        {activePresetInfo && activePreset !== 'custom' && (
          <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.5 }}>
            {activePresetInfo.description}
          </div>
        )}
        {activePreset === 'custom' && (
          <div style={{ fontSize: 11, color: ACCENT, marginTop: 4 }}>自定义配置（已脱离预设）</div>
        )}
      </div>

      {/* 阈值 */}
      <div style={{ display: 'flex', gap: 12 }}>
        <ThresholdControl
          label="买入阈值"
          value={config.buy_threshold}
          onChange={(v) => {
            setConfig({ ...config, buy_threshold: v });
            setActivePreset('custom');
          }}
          color={UP}
        />
        <ThresholdControl
          label="卖出阈值"
          value={config.sell_threshold}
          onChange={(v) => {
            setConfig({ ...config, sell_threshold: v });
            setActivePreset('custom');
          }}
          color={DOWN}
        />
      </div>

      {/* 策略开关 - 精简列表 */}
      <StrategyToggleList
        title="买入策略"
        count={enabledBuyCount}
        total={buyTemplates.length}
        color={UP}
        templates={buyTemplates}
        config={config}
        onToggle={(key) => updateStrategy(key, 'enabled', !config.strategies[key]?.enabled)}
      />
      <StrategyToggleList
        title="卖出策略"
        count={enabledSellCount}
        total={sellTemplates.length}
        color={DOWN}
        templates={sellTemplates}
        config={config}
        onToggle={(key) => updateStrategy(key, 'enabled', !config.strategies[key]?.enabled)}
      />

      {/* 高级设置 */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        style={{
          background: 'transparent',
          border: '1px solid var(--border)',
          borderRadius: 6,
          padding: '6px 12px',
          fontSize: 12,
          color: 'var(--text-secondary)',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        {showAdvanced ? '▼' : '▶'} 高级设置（权重与参数微调）
      </button>

      {showAdvanced && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {buyTemplates.map((t) => (
            <StrategyDetailRow
              key={t.key}
              template={t}
              strategy={config.strategies[t.key]}
              onUpdate={updateStrategy}
              onUpdateParam={updateStrategyParam}
            />
          ))}
          {sellTemplates.map((t) => (
            <StrategyDetailRow
              key={t.key}
              template={t}
              strategy={config.strategies[t.key]}
              onUpdate={updateStrategy}
              onUpdateParam={updateStrategyParam}
            />
          ))}
        </div>
      )}

      {/* 配置名称 & 保存 */}
      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        <input
          className="input"
          style={{ flex: '1 1 80px', minWidth: 70, padding: '4px 8px', fontSize: 12 }}
          value={configName}
          onChange={(e) => setConfigName(e.target.value)}
          placeholder="配置名"
        />
        {savedConfigs.length > 0 && (
          <select
            className="input"
            style={{ padding: '4px 8px', fontSize: 12, minWidth: 80 }}
            value=""
            onChange={(e) => e.target.value && handleLoadSaved(e.target.value)}
          >
            <option value="">加载...</option>
            {savedConfigs.map((c) => (
              <option key={c.config_name} value={c.config_name}>
                {c.config_name}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* 操作按钮 */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        <button
          onClick={handleBacktest}
          disabled={actionLoading !== null || !symbol}
          style={btnStyle(ACCENT)}
        >
          {actionLoading === 'backtest' ? '⏳ 回测中...' : '📊 运行回测'}
        </button>
        <button
          onClick={handleSave}
          disabled={actionLoading !== null || !symbol}
          style={btnStyle('var(--bg-card)')}
        >
          {actionLoading === 'save' ? '⏳' : '💾 保存'}
        </button>
        {savedConfigs.find((c) => c.config_name === configName) && (
          <button
            onClick={handleDelete}
            disabled={actionLoading !== null}
            style={{ ...btnStyle('transparent'), color: 'var(--warning)', border: '1px solid var(--border)' }}
          >
            🗑 删除
          </button>
        )}
      </div>

      {error && (
        <div style={{ color: 'var(--warning)', fontSize: 12, padding: '2px 0' }}>{error}</div>
      )}

      {/* 预览结果 - 紧凑 */}
      {previewResult && (
        <div style={resultBoxStyle}>
          <div style={{ display: 'flex', gap: 12, fontSize: 12, alignItems: 'center' }}>
            <span style={{ color: 'var(--text-secondary)' }}>
              预览: {previewResult.summary.total}天
            </span>
            <span style={{ color: UP, fontWeight: 600 }}>
              ▲ 买入 {previewResult.summary.buy_signals}
            </span>
            <span style={{ color: DOWN, fontWeight: 600 }}>
              ▼ 卖出 {previewResult.summary.sell_signals}
            </span>
            {actionLoading === 'preview' && (
              <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>更新中...</span>
            )}
          </div>
        </div>
      )}

      {/* 回测结果 */}
      {backtestResult && (
        <div style={resultBoxStyle}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'var(--text-primary)' }}>
            回测结果
          </div>
          <BacktestMetrics metrics={backtestResult.metrics} />
        </div>
      )}

      {!symbol && (
        <div style={{ color: 'var(--text-secondary)', fontSize: 12, textAlign: 'center', padding: 4 }}>
          请先选择股票
        </div>
      )}
    </div>
  );
}

function btnStyle(bg) {
  return {
    fontSize: 12,
    padding: '6px 14px',
    background: bg,
    border: '1px solid var(--border)',
    color: 'var(--text-primary)',
    borderRadius: 6,
    cursor: 'pointer',
    fontWeight: 500,
  };
}

const resultBoxStyle = {
  background: 'var(--bg-card)',
  borderRadius: 8,
  padding: 10,
  border: '1px solid var(--border)',
};

function ThresholdControl({ label, value, onChange, color }) {
  return (
    <div style={{ flex: 1 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
        <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{label}</span>
        <span style={{ fontSize: 11, color, fontWeight: 600 }}>{(value * 100).toFixed(0)}%</span>
      </div>
      <input
        type="range"
        min="0"
        max="0.3"
        step="0.01"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        style={{ width: '100%', accentColor: color, cursor: 'pointer' }}
      />
    </div>
  );
}

function StrategyToggleList({ title, count, total, color, templates, config, onToggle }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div
      style={{
        background: 'var(--bg-card)',
        borderRadius: 8,
        border: '1px solid var(--border)',
        overflow: 'hidden',
      }}
    >
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '6px 10px',
          cursor: 'pointer',
        }}
      >
        <span style={{ fontSize: 12, fontWeight: 600, color }}>
          {title} ({count}/{total})
        </span>
        <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>{expanded ? '收起' : '展开'}</span>
      </div>
      {expanded && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '2px 8px',
            padding: '2px 10px 6px',
          }}
        >
          {templates.map((t) => {
            const enabled = config.strategies[t.key]?.enabled;
            return (
              <label
                key={t.key}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  fontSize: 11,
                  cursor: 'pointer',
                  color: enabled ? 'var(--text-primary)' : 'var(--text-secondary)',
                  opacity: enabled ? 1 : 0.6,
                }}
              >
                <input
                  type="checkbox"
                  checked={enabled || false}
                  onChange={() => onToggle(t.key)}
                  style={{ accentColor: ACCENT, cursor: 'pointer', width: 12, height: 12 }}
                />
                {t.name}
              </label>
            );
          })}
        </div>
      )}
    </div>
  );
}

function StrategyDetailRow({ template, strategy, onUpdate, onUpdateParam }) {
  if (!strategy) return null;
  const enabled = strategy.enabled;
  return (
    <div
      style={{
        padding: '4px 8px',
        background: 'var(--bg-card)',
        borderRadius: 6,
        opacity: enabled ? 1 : 0.5,
        fontSize: 11,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ color: 'var(--text-primary)', flex: 1, fontWeight: 500 }}>{template.name}</span>
        <span style={{ color: 'var(--text-secondary)' }}>权重</span>
        <input
          type="range"
          min="0"
          max="3"
          step="0.1"
          value={strategy.weight}
          onChange={(e) => onUpdate(template.key, 'weight', parseFloat(e.target.value))}
          style={{ width: 50, accentColor: ACCENT, cursor: 'pointer' }}
          disabled={!enabled}
        />
        <span style={{ color: 'var(--text-secondary)', width: 24 }}>{strategy.weight.toFixed(1)}</span>
      </div>
      {enabled && template.params && template.params.length > 0 && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', paddingLeft: 4, marginTop: 2 }}>
          {template.params.map((p) => (
            <div key={p.key} style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{p.label}</span>
              <input
                type="number"
                min={p.min}
                max={p.max}
                step={p.step}
                value={strategy.params[p.key] ?? p.default}
                onChange={(e) => onUpdateParam(template.key, p.key, parseFloat(e.target.value))}
                style={{
                  width: 44,
                  padding: '1px 3px',
                  fontSize: 10,
                  background: 'var(--bg-primary)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border)',
                  borderRadius: 4,
                }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BacktestMetrics({ metrics }) {
  if (!metrics) return null;
  const m = metrics;
  const items = [
    { label: '总收益率', value: (m.total_return || 0) + '%', positive: (m.total_return || 0) > 0 },
    { label: '年化收益', value: (m.annual_return || 0) + '%', positive: (m.annual_return || 0) > 0 },
    { label: '最大回撤', value: (m.max_drawdown || 0) + '%', negative: true },
    { label: '胜率', value: (m.win_rate || 0) + '%', positive: (m.win_rate || 0) > 50 },
    { label: '交易次数', value: m.total_trades || 0 },
    { label: '盈亏比', value: m.profit_loss_ratio || 0 },
  ];
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
      {items.map((item, i) => (
        <div key={i} style={{ textAlign: 'center', padding: '2px 0' }}>
          <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>{item.label}</div>
          <div
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: item.positive ? UP : item.negative ? DOWN : 'var(--text-primary)',
            }}
          >
            {item.value}
          </div>
        </div>
      ))}
    </div>
  );
}
