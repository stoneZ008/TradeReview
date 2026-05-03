const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:5000/api';

export { API_BASE };

export function getAuthToken() {
  return localStorage.getItem('auth_token');
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
}

function getAuthHeaders() {
  const token = getAuthToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function fetchWithAuth(url, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...options.headers
  };
  const res = await fetch(url, { ...options, headers });
  if (res.status === 401 || res.status === 403) {
    const data = await res.json().catch(() => ({}));
    if (!getAuthToken()) {
      alert('请先登录后再使用此功能');
      window.location.href = '/login';
    } else if (data.error) {
      alert(data.error);
    }
  }
  return res;
}

export async function register(username, email, password) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

export async function getProfile() {
  const res = await fetchWithAuth(`${API_BASE}/auth/profile`);
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

export async function updateProfile(username, email) {
  const res = await fetchWithAuth(`${API_BASE}/auth/profile`, {
    method: 'PUT',
    body: JSON.stringify({ username, email })
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

export async function changePassword(oldPassword, newPassword) {
  const res = await fetchWithAuth(`${API_BASE}/auth/change-password`, {
    method: 'POST',
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

export async function getPlans() {
  const res = await fetch(`${API_BASE}/billing/plans`);
  const data = await res.json();
  return data.data || [];
}

export async function getMySubscription() {
  const res = await fetchWithAuth(`${API_BASE}/billing/my-subscription`);
  const data = await res.json();
  return data;
}

export async function adminGetUsers() {
  const res = await fetchWithAuth(`${API_BASE}/admin/users`);
  const data = await res.json();
  return data.data || [];
}

export async function adminAssignSubscription(userId, planName, isYearly = false) {
  const res = await fetchWithAuth(`${API_BASE}/admin/users/${userId}/subscription`, {
    method: 'PUT',
    body: JSON.stringify({ plan_name: planName, is_yearly: isYearly })
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

export async function adminGetAuditLogs() {
  const res = await fetchWithAuth(`${API_BASE}/admin/audit-logs`);
  const data = await res.json();
  return data.data || [];
}

export async function fetchStockData(symbol, startDate, endDate) {
  const res = await fetchWithAuth(`${API_BASE}/stock/${symbol}?start_date=${startDate}&end_date=${endDate}`);
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
  const res = await fetchWithAuth(`${API_BASE}/backtest`, {
    method: 'POST',
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

export async function loadWatchlist() {
  const res = await fetchWithAuth(`${API_BASE}/watchlist`);
  const data = await res.json();
  return data.data || [];
}

export async function addToWatchlist(code, name) {
  const res = await fetchWithAuth(`${API_BASE}/watchlist`, {
    method: 'POST',
    body: JSON.stringify({ code, name })
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.message);
  return data.data;
}

export async function removeFromWatchlist(code) {
  const res = await fetchWithAuth(`${API_BASE}/watchlist/${code}`, {
    method: 'DELETE'
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.message);
  return data.data;
}
