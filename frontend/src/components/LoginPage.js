import React, { useState } from 'react';

const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:5000/api';

export default function LoginPage({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!email || !password) {
      setError('请输入邮箱和密码');
      return;
    }
    setLoading(true);
    try {
      const url = isRegister ? `${API_BASE}/auth/register` : `${API_BASE}/auth/login`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (data.success) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onLogin(data.user, data.token);
      } else {
        setError(data.error || '操作失败');
      }
    } catch (e) {
      setError('网络错误，请确认后端服务已启动');
    }
    setLoading(false);
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-logo">
          <div className="logo-icon" style={{ fontSize: 48 }}>📈</div>
          <h1 className="login-title">ATradeReview</h1>
          <p className="login-subtitle">A股技术分析与回测工具</p>
        </div>

        <div className="login-tabs">
          <button
            className={`login-tab ${!isRegister ? 'active' : ''}`}
            onClick={() => { setIsRegister(false); setError(''); }}
          >
            登录
          </button>
          <button
            className={`login-tab ${isRegister ? 'active' : ''}`}
            onClick={() => { setIsRegister(true); setError(''); }}
          >
            注册
          </button>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>邮箱</label>
            <input
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="请输入邮箱地址"
              autoComplete="email"
            />
          </div>
          <div className="form-group">
            <label>密码</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isRegister ? '至少6位，不能纯数字' : '请输入密码'}
              autoComplete={isRegister ? 'new-password' : 'current-password'}
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="btn btn-primary login-btn" disabled={loading}>
            {loading ? '处理中...' : (isRegister ? '注册' : '登录')}
          </button>
        </form>

        <div className="login-hint">
          {isRegister
            ? '已有账号？点击上方"登录"'
            : '没有账号？点击上方"注册"'}
        </div>
      </div>
    </div>
  );
}
