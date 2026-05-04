import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { updateProfile, changePassword, getMySubscription, getPlans } from '../api';

export default function ProfilePage() {
  const { user, refreshProfile } = useAuth();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [subscription, setSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setUsername(user.username);
      setEmail(user.email);
    }
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      const [subData, plansData] = await Promise.all([
        getMySubscription(),
        getPlans()
      ]);
      setSubscription(subData);
      setPlans(plansData);
    } catch (e) {
      console.error('Failed to load data:', e);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });
    setLoading(true);
    try {
      await updateProfile(username, email);
      await refreshProfile();
      setMessage({ type: 'success', text: '资料更新成功' });
    } catch (e) {
      setMessage({ type: 'error', text: e.message });
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });

    if (newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: '两次密码输入不一致' });
      return;
    }

    if (newPassword.length < 6) {
      setMessage({ type: 'error', text: '新密码长度至少6位' });
      return;
    }

    setLoading(true);
    try {
      await changePassword(oldPassword, newPassword);
      setMessage({ type: 'success', text: '密码修改成功' });
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (e) {
      setMessage({ type: 'error', text: e.message });
    } finally {
      setLoading(false);
    }
  };

  const getCurrentPlan = () => {
    if (user?.is_trial_active) {
      return { name: '试用版', is_trial: true };
    }
    const plan = plans.find(p => p.id === subscription?.subscription?.plan_id);
    if (plan) return plan;
    return plans.find(p => p.name === 'basic') || { name: '基础版' };
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  return (
    <div className="profile-page">
      <div className="profile-container">
        <h1 className="profile-title">个人中心</h1>

        {message.text && (
          <div className={`message-box ${message.type}`}>
            {message.text}
          </div>
        )}

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">当前套餐</h2>
          </div>
          <div className="card-body">
            <div className="plan-info" style={{ marginBottom: '16px' }}>
              <span className="plan-name" style={{ fontSize: '24px', fontWeight: 600 }}>
                {getCurrentPlan()?.name === 'basic' ? '基础版' : 
                 getCurrentPlan()?.name === 'pro' ? '专业版' : 
                 getCurrentPlan()?.name === 'enterprise' ? '企业版' : 
                 getCurrentPlan()?.name || '基础版'}
              </span>
              {user?.is_trial_active && (
                <span className="trial-badge" style={{ 
                  background: '#fef3c7', 
                  color: '#d97706',
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: 500,
                  marginLeft: '12px'
                }}>
                  试用中
                </span>
              )}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {subscription?.subscription?.start_date && (
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    生效日期
                  </div>
                  <div style={{ fontWeight: 500 }}>
                    {formatDate(subscription.subscription.start_date)}
                  </div>
                </div>
              )}
              {subscription?.subscription?.end_date && (
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    到期日期
                  </div>
                  <div style={{ fontWeight: 500 }}>
                    {formatDate(subscription.subscription.end_date)}
                  </div>
                </div>
              )}
              {subscription?.backtest_quota && (
                <div style={{ gridColumn: '1 / -1' }}>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    本月回测配额
                  </div>
                  <div style={{ fontWeight: 500 }}>
                    {subscription.backtest_quota.used} / {
                      subscription.backtest_quota.max === -1 ? '无限' : subscription.backtest_quota.max
                    }
                    {subscription.backtest_quota.max !== -1 && (
                      <span style={{ 
                        marginLeft: '8px', 
                        color: subscription.backtest_quota.remaining < 3 ? 'var(--danger)' : 'var(--text-secondary)'
                      }}>
                        (剩余: {subscription.backtest_quota.remaining})
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">账号信息</h2>
          </div>
          <div className="card-body">
            <form onSubmit={handleUpdateProfile} className="profile-form">
              <div className="form-group">
                <label className="form-label">用户名</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label className="form-label">邮箱</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="form-input"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary"
              >
                保存修改
              </button>
            </form>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">修改密码</h2>
          </div>
          <div className="card-body">
            <form onSubmit={handleChangePassword} className="profile-form">
              <div className="form-group">
                <label className="form-label">原密码</label>
                <input
                  type="password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label className="form-label">新密码</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label className="form-label">确认新密码</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="form-input"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary"
              >
                修改密码
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
