import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getSubscriptionPlans, getActivationInfo } from '../api';

export default function SubscriptionPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState([]);
  const [activation, setActivation] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    try {
      const [planData, actInfo] = await Promise.all([
        getSubscriptionPlans(),
        getActivationInfo()
      ]);
      setPlans(planData);
      setActivation(actInfo);
    } catch (e) {
      console.error('加载失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const formatBacktestLimit = (limit) => {
    if (limit === -1) return '无限制';
    return limit + ' 次/月';
  };

  const isCurrentPlan = (planName) => {
    return user?.subscription?.plan_name === planName;
  };

  const copyContact = () => {
    if (!user?.username) return;
    navigator.clipboard?.writeText(user.username);
    alert('已复制您的账号: ' + user.username);
  };

  return (
    <div className="subscription-page">
      <style>{`
        .subscription-page {
          min-height: 100vh;
          background: var(--bg-primary);
          padding: 40px 20px;
        }
        .subscription-container {
          max-width: 1000px;
          margin: 0 auto;
        }
        .subscription-header {
          text-align: center;
          margin-bottom: 30px;
        }
        .subscription-title {
          font-size: 32px;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: 12px;
        }
        .subscription-subtitle {
          font-size: 16px;
          color: var(--text-secondary);
        }
        .activation-card {
          background: var(--bg-secondary);
          border-radius: 12px;
          padding: 28px;
          margin-bottom: 32px;
          border: 1px solid var(--border-color);
        }
        .activation-title {
          font-size: 20px;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: 12px;
        }
        .activation-desc {
          color: var(--text-secondary);
          font-size: 14px;
          margin-bottom: 16px;
          line-height: 1.6;
        }
        .activation-steps {
          background: var(--bg-tertiary);
          padding: 16px 20px;
          border-radius: 8px;
          margin-bottom: 20px;
        }
        .activation-step {
          display: flex;
          align-items: flex-start;
          padding: 6px 0;
          color: var(--text-primary);
          font-size: 14px;
        }
        .activation-step .step-no {
          flex-shrink: 0;
          width: 22px;
          height: 22px;
          border-radius: 50%;
          background: var(--accent-blue);
          color: white;
          font-size: 12px;
          line-height: 22px;
          text-align: center;
          margin-right: 10px;
          font-weight: 600;
        }
        .activation-actions {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          align-items: center;
        }
        .zsxq-btn {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          padding: 16px 36px;
          border-radius: 12px;
          font-size: 17px;
          font-weight: 700;
          cursor: pointer;
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
          transition: all 0.3s ease;
          animation: pulse-btn 2s infinite;
        }
        .zsxq-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
        }
        @keyframes pulse-btn {
          0%, 100% {
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
          }
          50% {
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.6);
          }
        }
        .copy-btn {
          background: var(--bg-tertiary);
          color: var(--text-primary);
          border: 1px solid var(--border-color);
          padding: 12px 20px;
          border-radius: 8px;
          font-size: 14px;
          cursor: pointer;
        }
        .qr-img {
          margin-top: 16px;
          width: 200px;
          height: 200px;
          background: white;
          padding: 8px;
          border-radius: 8px;
        }
        .plans-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 20px;
          margin-bottom: 32px;
        }
        .plan-card {
          background: var(--bg-secondary);
          border-radius: 12px;
          padding: 24px;
          border: 2px solid transparent;
          position: relative;
        }
        .plan-card.current {
          border-color: var(--accent-green);
        }
        .plan-badge {
          position: absolute;
          top: -10px;
          right: 16px;
          background: var(--accent-green);
          color: white;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
        }
        .plan-name {
          font-size: 18px;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: 8px;
        }
        .plan-description {
          font-size: 13px;
          color: var(--text-secondary);
          margin-bottom: 16px;
          min-height: 36px;
        }
        .plan-features {
          font-size: 13px;
          color: var(--text-primary);
        }
        .feature-item {
          display: flex;
          align-items: center;
          padding: 6px 0;
        }
        .feature-icon {
          color: var(--accent-green);
          margin-right: 8px;
        }
        .info-banner {
          background: var(--bg-secondary);
          border-radius: 12px;
          padding: 20px 24px;
          margin-top: 24px;
        }
        .info-item {
          display: flex;
          justify-content: space-between;
          padding: 10px 0;
          border-bottom: 1px solid var(--border-color);
          font-size: 14px;
        }
        .info-item:last-child { border-bottom: none; }
        .info-value.active { color: var(--accent-green); }
        .info-value.expired { color: var(--accent-red); }
      `}</style>

      <div className="subscription-container">
        <div className="subscription-header">
          <h1 className="subscription-title">开通会员</h1>
          <p className="subscription-subtitle">通过加入知识星球，由管理员后台开通对应账户权限</p>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
            加载中...
          </div>
        ) : (
          <>
            <div className="activation-card">
              <div className="activation-title">📚 加入知识星球开通账号</div>
              <div className="activation-desc">
                请加入「细水长流」知识星球，
                加入后联系管理员，由管理员在后台为您开通对应套餐权限。
              </div>

              <div className="activation-steps">
                {(activation?.instructions || []).map((step, idx) => (
                  <div className="activation-step" key={idx}>
                    <span className="step-no">{idx + 1}</span>
                    <span>{step}</span>
                  </div>
                ))}
              </div>

              <div className="activation-actions">
                {activation?.join_url && (
                  <a
                    className="zsxq-btn"
                    href={activation.join_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    🚀 加入知识星球
                  </a>
                )}
              </div>

              {activation?.qr_url && (
                <div>
                  <img className="qr-img" src={activation.qr_url} alt="知识星球二维码" />
                </div>
              )}

              <div style={{
                marginTop: '16px',
                fontSize: '13px',
                color: 'var(--text-secondary)'
              }}>
                {activation?.contact}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
