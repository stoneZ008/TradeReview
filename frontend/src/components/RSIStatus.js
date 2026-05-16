export default function RSIStatus({ stockData, rsiPeriod, onRsiPeriodChange }) {
  if (!stockData?.data?.length) return null;

  const latestData = stockData.data[stockData.data.length - 1];
  const rsi = latestData?.rsi;

  if (rsi == null) return null;

  const getStatus = (value) => {
    if (value >= 70) return { text: '超买', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' };
    if (value <= 30) return { text: '超卖', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.15)' };
    return { text: '中性', color: '#a78bfa', bg: 'rgba(167, 139, 250, 0.15)' };
  };

  const status = getStatus(rsi);
  const periodOptions = [6, 9, 12, 14, 20, 24];

  const isMobile = window.innerWidth <= 768;
  
  return (
    <div style={{
      padding: isMobile ? '8px 12px' : '12px 16px',
      background: status.bg,
      borderRadius: '8px',
      border: `1px solid ${status.color}30`,
      display: 'flex',
      flexWrap: 'wrap',
      alignItems: 'center',
      gap: isMobile ? '8px' : '12px',
      marginBottom: '8px'
    }}>
      <div>
        <div style={{ fontSize: isMobile ? '11px' : '12px', color: '#888', marginBottom: '2px' }}>RSI ({rsiPeriod})</div>
        <div style={{ fontSize: isMobile ? '20px' : '24px', fontWeight: 'bold', color: status.color }}>
          {rsi.toFixed(2)}
        </div>
      </div>
      <div style={{
        padding: isMobile ? '3px 10px' : '4px 12px',
        borderRadius: '4px',
        background: status.color,
        color: '#fff',
        fontSize: isMobile ? '13px' : '14px',
        fontWeight: 500
      }}>
        {status.text}
      </div>
      {!isMobile && (
        <div style={{ flex: 1, textAlign: 'right', fontSize: '12px', color: '#888' }}>
          <div>30以下 = 超卖区 (看多)</div>
          <div>70以上 = 超买区 (看空)</div>
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: isMobile ? 'auto' : 0 }}>
        <span style={{ fontSize: '12px', color: '#888' }}>周期:</span>
        <select
          value={rsiPeriod}
          onChange={(e) => onRsiPeriodChange && onRsiPeriodChange(Number(e.target.value))}
          style={{
            padding: isMobile ? '6px 10px' : '4px 8px',
            borderRadius: '4px',
            border: '1px solid #444',
            background: '#1a1a2e',
            color: '#fff',
            fontSize: isMobile ? '13px' : '12px',
            cursor: 'pointer',
            minHeight: isMobile ? '36px' : 'auto'
          }}
        >
          {periodOptions.map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
