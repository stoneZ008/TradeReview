# 账户体系与权限控制系统

## 概述

为TradeReview构建的完整账户体系，包含：
- JWT身份认证
- RBAC角色权限控制
- 订阅套餐管理
- 试用期机制
- 审计日志

## 技术栈

**后端**: Flask + Flask-JWT-Extended + Flask-Bcrypt + SQLite
**前端**: React + React Router

## 数据库表结构

### 用户与权限
| 表名 | 说明 |
|-----|------|
| users | 用户表（用户名、邮箱、密码哈希、试用期） |
| roles | 角色表（super_admin, admin, user_pro, user_basic, user_free, guest） |
| permissions | 权限表 |
| role_permissions | 角色-权限关联 |
| user_roles | 用户-角色关联 |

### 订阅与计费
| 表名 | 说明 |
|-----|------|
| subscription_plans | 套餐配置（trial, basic, pro, enterprise） |
| subscriptions | 用户订阅记录 |
| backtest_usage | 回测使用量统计 |

### 业务数据
| 表名 | 说明 |
|-----|------|
| user_watchlists | 用户自选股 |
| audit_logs | 审计日志 |

## 预设角色与权限

### super_admin (超级管理员)
- 所有权限
- 用户管理
- 角色管理
- 订阅分配

### admin (管理员)
- 用户管理
- 订阅分配
- 查看审计日志

### user_pro (专业版用户)
- 查看股票数据
- 运行回测（100次/月）
- 管理自选股
- 认知之道页面

### user_basic (基础版用户)
- 查看股票数据
- 运行回测（20次/月）
- 管理自选股

### user_free (免费用户)
- 查看股票数据
- 管理自选股
- 无法运行回测

### guest (访客)
- 查看股票数据
- 公开页面

## 套餐体系

| 套餐 | 月价 | 年价 | 月回测次数 | 技术指标 | 认知之道 |
|-----|-----|-----|-----------|---------|---------|
| 试用 | 免费 | - | 10次 | ✅ | ✅ |
| 基础 | ¥29 | ¥290 | 20次 | ✅ | ❌ |
| 专业 | ¥99 | ¥990 | 100次 | ✅ | ✅ |
| 企业 | ¥299 | ¥2990 | 无限 | ✅ | ✅ |

**试用期规则**: 新用户注册即获得10天专业版试用，试用期结束后自动降级为免费用户。

## API 接口

### 认证接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/refresh` | 刷新Token |
| GET | `/api/auth/profile` | 获取用户信息 |
| PUT | `/api/auth/profile` | 更新用户信息 |
| POST | `/api/auth/change-password` | 修改密码 |

### 订阅接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/billing/plans` | 获取套餐列表 |
| GET | `/api/billing/my-subscription` | 获取当前订阅 |

### 管理接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/admin/users` | 用户列表 |
| PUT | `/api/admin/users/:id/subscription` | 分配用户套餐 |
| PUT | `/api/admin/users/:id/roles` | 分配用户角色 |
| GET | `/api/admin/audit-logs` | 审计日志 |

### 业务接口（已集成权限控制）
| 方法 | 路径 | 说明 | 权限 |
|-----|------|------|------|
| GET | `/api/stock/:symbol` | 获取股票数据 | stock:read |
| POST | `/api/backtest` | 运行回测 | 需要配额 |
| GET | `/api/watchlist` | 获取自选股 | watchlist:read |
| POST | `/api/watchlist` | 添加自选股 | watchlist:write |
| DELETE | `/api/watchlist/:code` | 删除自选股 | watchlist:write |
| GET | `/api/industries` | 行业数据 | industry:read |
| POST | `/api/industries` | 管理行业 | industry:write |

## 前端页面

| 路径 | 页面 | 说明 |
|-----|------|------|
| `/login` | 登录页 | 用户登录 |
| `/register` | 注册页 | 新用户注册 |
| `/profile` | 个人中心 | 用户信息、密码修改、套餐信息 |
| `/admin` | 管理后台 | 用户管理、审计日志（仅管理员） |
| `/` | 首页 | 股票分析主页面 |

## 权限装饰器

### @jwt_required
要求有效的JWT Token，设置全局用户上下文。

### @optional_jwt
可选JWT Token，未登录时默认为guest角色。

### @requires_roles(roles...)
要求用户拥有指定角色之一。

### @requires_permission(permission)
要求用户拥有指定权限。

### @requires_backtest_quota
检查回测配额，超额返回403错误。

## 部署说明

### 后端
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python3 app.py
```

### 环境变量
```env
JWT_SECRET_KEY=your-secret-key-here
```

## 初始化

首次启动时会自动初始化数据库表和默认数据：
- 创建所有表结构
- 初始化默认角色和权限
- 创建套餐配置

## 安全特性

1. **密码加密**: 使用bcrypt加密存储用户密码
2. **JWT认证**: 无状态Token，支持刷新
3. **权限校验**: 所有业务接口均有权限装饰器保护
4. **配额控制**: 回测次数按月统计，超额限制
5. **审计日志**: 记录关键操作（登录、注册、运行回测等）

## 后续扩展

1. 对接支付宝/微信支付
2. 添加邮件通知（注册、续费、到期提醒）
3. 监控指标可视化
4. API限流增强
5. 多因素认证
