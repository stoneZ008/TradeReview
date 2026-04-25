const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:5000/api';

export { API_BASE };

function authHeaders() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: 'Bearer ' + token } : {};
}

export async function fetchStockData(symbol, startDate, endDate) {
  const res = await fetch(`${API_BASE}/stock/${symbol}?start_date=${startDate}&end_date=${endDate}`, {
    headers: authHeaders()
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

export async function runBacktest(symbol, startDate, endDate, config = {}) {
  const body = {
    symbol,
    start_date: startDate,
    end_date: endDate,
    config: {
      initial_capital: 100000,
      commission_rate: 0.001,
      buy_threshold: 0.08,
      sell_threshold: 0.12,
      ...config
    }
  };
  const res = await fetch(`${API_BASE}/backtest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

export async function loadWatchlist() {
  const res = await fetch(`${API_BASE}/watchlist`, { headers: authHeaders() });
  const data = await res.json();
  return data.data || [];
}

export async function addToWatchlist(code, name) {
  const res = await fetch(`${API_BASE}/watchlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ code, name })
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.message);
  return data.data;
}

export async function removeFromWatchlist(code) {
  const res = await fetch(`${API_BASE}/watchlist/${code}`, {
    method: 'DELETE',
    headers: authHeaders()
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.message);
  return data.data;
}
