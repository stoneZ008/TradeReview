import { useState, useEffect } from 'react';
import { adminGetUsers, adminAssignSubscription, adminAssignRole, adminCreateUser, adminGetAuditLogs, getPlans } from '../api';
import { useAuth } from '../context/AuthContext';

export default function AdminPage() {
  const [users, setUsers] = useState([]);
  const [plans, setPlans] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('users');
  const [message, setMessage] = useState({ type: '', text: '' });
  const [showAddUserForm, setShowAddUserForm] = useState(false);
  const [newUser, setNewUser] = useState({ username: '', email: '', password: '' });
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

  const handleAssignRole = async (userId, roleName) => {
    try {
      await adminAssignRole(userId, roleName);
      setMessage({ type: 'success', text: '角色分配成功' });
      loadData();
    } catch (e) {
      setMessage({ type: 'error', text: e.message });
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await adminCreateUser(newUser.username, newUser.email, newUser.password);
      setMessage({ type: 'success', text: '用户创建成功' });
      setNewUser({ username: '', email: '', password: '' });
      setShowAddUserForm(false);
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
              <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ margin: 0, fontSize: '16px' }}>用户列表</h3>
                  <button
                    onClick={() => setShowAddUserForm(!showAddUserForm)}
                    className="btn btn-primary"
                    style={{ padding: '8px 16px', fontSize: '14px' }}
                  >
                    {showAddUserForm ? '取消' : '+ 添加用户'}
                  </button>
                </div>
                {showAddUserForm && (
                  <form onSubmit={handleCreateUser} style={{ marginTop: '16px', display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>用户名</label>
                      <input
                        type="text"
                        className="form-input"
                        value={newUser.username}
                        onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                        required
                        placeholder="输入用户名"
                      />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>邮箱</label>
                      <input
                        type="email"
                        className="form-input"
                        value={newUser.email}
                        onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                        required
                        placeholder="输入邮箱"
                      />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>密码</label>
                      <input
                        type="password"
                        className="form-input"
                        value={newUser.password}
                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                        required
                        placeholder="输入密码"
                        minLength="6"
                      />
                    </div>
                    <button type="submit" className="btn btn-primary">创建</button>
                  </form>
                )}
              </div>
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
                         {hasRole('super_admin') ? (
                           <select
                             onChange={(e) => handleAssignRole(user.id, e.target.value)}
                             className="form-input"
                             style={{ width: '120px', fontSize: '12px', padding: '6px 10px' }}
                             defaultValue={user.roles?.[0] || 'user_free'}
                           >
                             <option value="super_admin">super_admin</option>
                             <option value="admin">admin</option>
                             <option value="user_pro">user_pro</option>
                             <option value="user_basic">user_basic</option>
                             <option value="user_free">user_free</option>
                             <option value="guest">guest</option>
                           </select>
                         ) : (
                           <span className="badge">{user.roles?.[0] || 'user'}</span>
                         )}
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
