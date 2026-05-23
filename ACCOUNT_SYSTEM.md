# 账户体系与权限控制系统

## 概述

为TradeReview构建的账户体系，包含：
- JWT 身份认证
- RBAC 角色权限控制
- 套餐管理（仅作为权限分组，**不提供在线支付能力**）
- 试用期机制
- 审计日志
- **通过加入知识星球的方式，由管理员后台手动开通账户权限**

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

### 订阅
| 表名 | 说明 |
|-----|------|
| subscription_plans | 套餐配置（trial, basic, pro, enterprise） |
| subscriptions | 用户订阅记录（由管理员后台分配） |
| backtest_usage | 回测使用量统计 |

### 业务数据
| 表名 | 说明 |
|-----|------|
| user_watchlists | 用户自选股 |
| audit_logs | 审计日志 |

> 已移除 `orders` 与 `payment_callbacks` 两张支付相关表。

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

| 套餐 | 月回测次数 | 技术指标 | 认知之道 | 开通方式 |
|-----|-----------|---------|---------|---------|
| 试用 | 10次 | ✅ | ✅ | 注册自动开通 10 天 |
| 基础 | 20次 | ✅ | ❌ | **加入知识星球，管理员后台开通** |
| 专业 | 100次 | ✅ | ✅ | **加入知识星球，管理员后台开通** |
| 企业 | 无限 | ✅ | ✅ | **加入知识星球，管理员后台开通** |

**试用期规则**: 新用户注册即获得 10 天专业版试用，试用期结束后自动降级为免费用户。

**开通流程**:
1. 用户加入知识星球
2. 用户将自己的账号告知管理员
3. 管理员在后台 `/admin` 用户管理中为该用户分配相应套餐
4. 用户立即获得对应权限

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
| GET | `/api/subscription/plans` | 获取套餐详细列表（含权益） |
| GET | `/api/activation/info` | 获取知识星球开通指引 |

> 已移除：`/api/orders/*`、`/api/payment/*`、`/api/admin/orders/*` 等支付相关接口。

### 管理接口
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/admin/users` | 用户列表 |
| POST | `/api/admin/users` | 创建用户 |
| PUT | `/api/admin/users/:id/subscription` | **手动分配用户套餐（核心开通方式）** |
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
| `/subscription` | 开通会员 | 知识星球开通指引 + 套餐权益对比 |
| `/admin` | 管理后台 | 用户管理、套餐分配、审计日志（仅管理员） |
| `/` | 首页 | 股票分析主页面 |

> 已移除：`/payment/:orderNo`、`/payment/success`、`/orders` 等支付相关页面。

## 知识星球配置

通过环境变量配置：

```env
ZSXQ_GROUP_NAME=TradeReview 交易复盘
ZSXQ_JOIN_URL=https://t.zsxq.com/fPcnb
ZSXQ_QR_URL=
ZSXQ_CONTACT=加入知识星球后，请将昵称/星球账号发送给管理员开通账户权限
```

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
# JWT 密钥
JWT_SECRET_KEY=your-secret-key-here

# 默认管理员账号（首次启动自动创建）
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@tradereview.local
ADMIN_PASSWORD=admin123

# 知识星球配置
ZSXQ_JOIN_URL=https://t.zsxq.com/your-invite-code
ZSXQ_QR_URL=https://your-cdn.com/zsxq-qr.png
```

## 初始化

首次启动时会自动初始化数据库表和默认数据：
- 创建所有表结构
- 初始化默认角色和权限（super_admin、admin、user_pro、user_basic、user_free、guest）
- 创建套餐配置（trial、basic、pro、enterprise）
- **自动创建默认超级管理员账号**：
  - 用户名：`admin`（可通过环境变量 `ADMIN_USERNAME` 修改）
  - 邮箱：`admin@tradereview.local`（可通过环境变量 `ADMIN_EMAIL` 修改）
  - 密码：`admin123`（可通过环境变量 `ADMIN_PASSWORD` 修改）
  - 默认拥有企业版订阅，10年有效期

## 安全特性

1. **密码加密**: 使用 bcrypt 加密存储用户密码
2. **JWT 认证**: 无状态 Token，支持刷新
3. **权限校验**: 所有业务接口均有权限装饰器保护
4. **配额控制**: 回测次数按月统计，超额限制
5. **审计日志**: 记录关键操作（登录、注册、运行回测、套餐分配等）

## 后续扩展

1. 知识星球账号自动同步（通过 zsxq 开放接口）
2. 添加邮件通知（注册、开通、到期提醒）
3. 监控指标可视化
4. API 限流增强
5. 多因素认证
