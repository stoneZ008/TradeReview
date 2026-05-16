export default function KDJStatus({ stockData }) {
  if (!stockData?.data?.length) return null;

  const latestData = stockData.data[stockData.data.length - 1];
  const k = latestData?.kdj_k;
  const d = latestData?.kdj_d;
  const j = latestData?.kdj_j;

  if (k == null || d == null || j == null) return null;

  const getStatus = () => {
    if (k > 80 && d > 80) return { text: '超买', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' };
    if (k < 20 && d < 20) return { text: '超卖', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.15)' };
    return { text: '中性', color: '#a78bfa', bg: 'rgba(167, 139, 250, 0.15)' };
  };

  const status = getStatus();
  const isMobile = window.innerWidth <= 768;

  const prevData = stockData.data[stockData.data.length - 2];
  let crossStatus = '';
  let crossColor = '';
  if (prevData) {
    if (k > d && prevData.kdj_k <= prevData.kdj_d) {
      crossStatus = '金叉';
      crossColor = '#22c55e';
    } else if (k < d && prevData.kdj_k >= prevData.kdj_d) {
      crossStatus = '死叉';
      crossColor = '#ef4444';
    }
  }

  return (
    <div
      style={{
        padding: isMobile ? '8px 12px' : '12px 16px',
        background: status.bg,
        borderRadius: '8px',
        border: `1px solid ${status.color}30`,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: isMobile ? '8px' : '16px',
        marginBottom: '8px',
      }}
    >
      <div style={{ display: 'flex', gap: '16px' }}>
        <div>
          <div style={{ fontSize: isMobile ? '11px' : '12px', color: '#888', marginBottom: '2px' }}>
            K
          </div>
          <div
            style={{ fontSize: isMobile ? '18px' : '22px', fontWeight: 'bold', color: '#3b82f6' }}
          >
            {k.toFixed(2)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: isMobile ? '11px' : '12px', color: '#888', marginBottom: '2px' }}>
            D
          </div>
          <div
            style={{ fontSize: isMobile ? '18px' : '22px', fontWeight: 'bold', color: '#fbbf24' }}
          >
            {d.toFixed(2)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: isMobile ? '11px' : '12px', color: '#888', marginBottom: '2px' }}>
            J
          </div>
          <div
            style={{ fontSize: isMobile ? '18px' : '22px', fontWeight: 'bold', color: '#a78bfa' }}
          >
            {j.toFixed(2)}
          </div>
        </div>
      </div>

      <div
        style={{
          padding: isMobile ? '3px 10px' : '4px 12px',
          borderRadius: '4px',
          background: status.color,
          color: '#fff',
          fontSize: isMobile ? '13px' : '14px',
          fontWeight: 500,
        }}
      >
        {status.text}
      </div>

      {crossStatus && (
        <div
          style={{
            padding: isMobile ? '3px 10px' : '4px 12px',
            borderRadius: '4px',
            background: crossColor,
            color: '#fff',
            fontSize: isMobile ? '13px' : '14px',
            fontWeight: 500,
          }}
        >
          {crossStatus}
        </div>
      )}

      {!isMobile && (
        <div style={{ flex: 1, textAlign: 'right', fontSize: '12px', color: '#888' }}>
          <div>20以下 = 超卖区</div>
          <div>80以上 = 超买区</div>
        </div>
      )}
    </div>
  );
}
