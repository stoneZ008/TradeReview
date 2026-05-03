import { useState, useEffect } from 'react';
import { adminGetUsers, adminAssignSubscription, adminGetAuditLogs, getPlans } from '../api';
import { useAuth } from '../context/AuthContext';

export default function AdminPage() {
  const [users, setUsers] = useState([]);
  const [plans, setPlans] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('users');
  const [message, setMessage] = useState({ type: '', text: '' });
  const { hasRole } = useAuth();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [usersData, plansData, logsData] = await Promise.all([
        adminGetUsers(),
        getPlans(),
        adminGetAuditLogs()
      ]);
      setUsers(usersData);
      setPlans(plansData);
      setAuditLogs(logsData);
    } catch (e) {
      setMessage({ type: 'error', text: '加载数据失败' });
    }
  };

  const handleAssignPlan = async (userId, planName) => {
    try {
      await adminAssignSubscription(userId, planName, false);
      setMessage({ type: 'success', text: '套餐分配成功' });
      loadData();
    } catch (e) {
      setMessage({ type: 'error', text: e.message });
    }
  };

  const getPlanName = (user) => {
    if (user.is_trial_active) return '试用版';
    const plan = plans.find(p => p.id === user.subscription?.plan_id);
    return plan?.name || '基础版';
  };

  if (!hasRole('admin') && !hasRole('super_admin')) {
    return (
      <div className="profile-page">
        <div className="profile-container">
          <div className="card">
            <div className="card-body" style={{ textAlign: 'center', padding: '60px' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔒</div>
              <h2 style={{ marginBottom: '8px' }}>无权限访问</h2>
              <p style={{ color: 'var(--text-secondary)' }}>
                您没有管理后台的访问权限
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-container" style={{ maxWidth: '1200px' }}>
        <h1 className="profile-title">管理后台</h1>

        {message.text && (
          <div className={`message-box ${message.type}`}>
            {message.text}
          </div>
        )}

        <div className="tabs">
          <button
            onClick={() => setActiveTab('users')}
            className={`tab ${activeTab === 'users' ? 'active' : ''}`}
          >
            用户管理
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`tab ${activeTab === 'logs' ? 'active' : ''}`}
          >
            审计日志
          </button>
        </div>

        {activeTab === 'users' && (
          <div className="card">
            <div className="card-body" style={{ padding: 0 }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>用户名</th>
                    <th>邮箱</th>
                    <th>角色</th>
                    <th>当前套餐</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td style={{ fontWeight: 500 }}>{user.username}</td>
                      <td>{user.email}</td>
                      <td>
                        <span className="badge">{user.roles?.[0] || 'user'}</span>
                      </td>
                      <td>
                        <span className={`badge ${user.is_trial_active ? 'badge-warning' : 'badge-success'}`}>
                          {getPlanName(user)}
                        </span>
                      </td>
                      <td>
                        <select
                          onChange={(e) => handleAssignPlan(user.id, e.target.value)}
                          className="form-input"
                          style={{ width: '140px', fontSize: '12px', padding: '6px 10px' }}
                          defaultValue=""
                        >
                          <option value="" disabled>分配套餐</option>
                          {plans.map((plan) => (
                            <option key={plan.id} value={plan.name}>{plan.name}</option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="card">
            <div className="card-body" style={{ padding: 0 }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>时间</th>
                    <th>用户</th>
                    <th>操作</th>
                    <th>IP地址</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.id}>
                      <td style={{ fontSize: '12px' }}>
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td>{log.username || '匿名'}</td>
                      <td>
                        <span className="badge">{log.action}</span>
                      </td>
                      <td style={{ fontSize: '12px' }}>{log.ip_address || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
