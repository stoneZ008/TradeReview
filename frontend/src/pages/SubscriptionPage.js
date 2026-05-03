import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getSubscriptionPlans } from '../api';

export default function SubscriptionPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      const data = await getSubscriptionPlans();
      setPlans(data);
    } catch (e) {
      console.error('加载套餐失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = (plan) => {
    alert('请联系管理员开通订阅\n\n套餐: ' + plan.name_cn + '\n邮箱: admin@example.com');
  };

  const formatBacktestLimit = (limit) => {
    if (limit === -1) return '无限制';
    return limit + ' 次/月';
  };

  const isCurrentPlan = (planName) => {
    return user?.subscription?.plan_name === planName;
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
          margin-bottom: 50px;
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
        .plans-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 24px;
          margin-bottom: 40px;
        }
        .plan-card {
          background: var(--bg-secondary);
          border-radius: 12px;
          padding: 28px 24px;
          border: 2px solid transparent;
          position: relative;
          transition: all 0.3s ease;
        }
        .plan-card:hover {
          border-color: var(--accent-blue);
          transform: translateY(-4px);
        }
        .plan-card.current {
          border-color: var(--accent-green);
        }
        .plan-badge {
          position: absolute;
          top: -10px;
          right: 20px;
          background: var(--accent-green);
          color: white;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
        }
        .plan-name {
          font-size: 20px;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: 8px;
        }
        .plan-description {
          font-size: 14px;
          color: var(--text-secondary);
          margin-bottom: 20px;
        }
        .plan-price {
          margin-bottom: 24px;
        }
        .price-monthly {
          font-size: 36px;
          font-weight: 700;
          color: var(--text-primary);
        }
        .price-monthly span {
          font-size: 16px;
          font-weight: 400;
          color: var(--text-secondary);
        }
        .price-yearly {
          font-size: 14px;
          color: var(--text-secondary);
          margin-top: 4px;
        }
        .price-yearly strong {
          color: var(--accent-green);
        }
        .plan-features {
          margin-bottom: 28px;
        }
        .feature-item {
          display: flex;
          align-items: center;
          padding: 10px 0;
          border-bottom: 1px solid var(--border-color);
          font-size: 14px;
          color: var(--text-primary);
        }
        .feature-item:last-child {
          border-bottom: none;
        }
        .feature-icon {
          color: var(--accent-green);
          margin-right: 10px;
          font-size: 16px;
        }
        .plan-btn {
          width: 100%;
          padding: 12px;
          border: none;
          border-radius: 8px;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }
        .plan-btn.primary {
          background: var(--accent-blue);
          color: white;
        }
        .plan-btn.primary:hover {
          opacity: 0.9;
        }
        .plan-btn.secondary {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }
        .plan-btn.secondary:hover {
          background: var(--hover-bg);
        }
        .subscription-info {
          background: var(--bg-secondary);
          border-radius: 12px;
          padding: 24px;
          margin-top: 32px;
        }
        .info-title {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 16px;
        }
        .info-item {
          display: flex;
          justify-content: space-between;
          padding: 12px 0;
          border-bottom: 1px solid var(--border-color);
        }
        .info-item:last-child {
          border-bottom: none;
        }
        .info-label {
          color: var(--text-secondary);
        }
        .info-value {
          color: var(--text-primary);
          font-weight: 500;
        }
        .info-value.active {
          color: var(--accent-green);
        }
        .info-value.expired {
          color: var(--accent-red);
        }
        .contact-box {
          background: var(--accent-blue);
          border-radius: 12px;
          padding: 24px;
          margin-top: 24px;
          text-align: center;
          color: white;
        }
        .contact-title {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 8px;
        }
        .contact-email {
          font-size: 16px;
          opacity: 0.9;
        }
        .back-btn {
          display: inline-flex;
          align-items: center;
          color: var(--accent-blue);
          text-decoration: none;
          margin-bottom: 24px;
          font-size: 15px;
          cursor: pointer;
        }
        .back-btn:hover {
          text-decoration: underline;
        }
      `}</style>

      <div className="subscription-container">
        <div className="back-btn" onClick={() => window.history.back()}>
          ← 返回
        </div>

        <div className="subscription-header">
          <h1 className="subscription-title">订阅套餐</h1>
          <p className="subscription-subtitle">选择适合您的套餐，解锁更多功能</p>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
            加载中...
          </div>
        ) : (
          <div className="plans-grid">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className={`plan-card ${isCurrentPlan(plan.name) ? 'current' : ''}`}
              >
                {isCurrentPlan(plan.name) && (
                  <div className="plan-badge">当前套餐</div>
                )}

                <div className="plan-name">{plan.name_cn}</div>
                <div className="plan-description">{plan.description}</div>

                <div className="plan-price">
                  <div className="price-monthly">
                    ¥{plan.monthly_price} <span>/月</span>
                  </div>
                  <div className="price-yearly">
                    年付 <strong>¥{plan.yearly_price}</strong>
                  </div>
                </div>

                <div className="plan-features">
                  <div className="feature-item">
                    <span className="feature-icon">✓</span>
                    回测次数: {formatBacktestLimit(plan.max_backtests_monthly)}
                  </div>
                  <div className="feature-item">
                    <span className="feature-icon">✓</span>
                    技术指标分析
                  </div>
                  {plan.features.dao_page && (
                    <div className="feature-item">
                      <span className="feature-icon">✓</span>
                      认知之道页面
                    </div>
                  )}
                  {plan.features.priority_support && (
                    <div className="feature-item">
                      <span className="feature-icon">✓</span>
                      优先技术支持
                    </div>
                  )}
                </div>

                <button
                  className={`plan-btn ${isCurrentPlan(plan.name) ? 'secondary' : 'primary'}`}
                  onClick={() => handleSubscribe(plan)}
                  disabled={isCurrentPlan(plan.name)}
                >
                  {isCurrentPlan(plan.name) ? '当前套餐' : '立即订阅'}
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="subscription-info">
          <div className="info-title">我的订阅状态</div>
          <div className="info-item">
            <span className="info-label">当前套餐</span>
            <span className="info-value">
              {user?.subscription?.plan_name_cn || '免费用户'}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">订阅状态</span>
            <span className={`info-value ${user?.subscription?.status === 'active' ? 'active' : 'expired'}`}>
              {user?.subscription?.status === 'active' ? '有效' : '已过期'}
            </span>
          </div>
          {user?.subscription?.end_date && (
            <div className="info-item">
              <span className="info-label">到期时间</span>
              <span className="info-value">
                {new Date(user.subscription.end_date).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>

        <div className="contact-box">
          <div className="contact-title">需要帮助？</div>
          <div className="contact-email">联系管理员开通订阅: admin@example.com</div>
        </div>
      </div>
    </div>
  );
}
