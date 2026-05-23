# TradeReview - Agent Instructions

## Project Overview

A股技术分析与回测工具。Flask 后端 + React 前端，Docker 部署。

```
backend/          Flask API (port 5000)
frontend/         React + ECharts SPA (port 80 in Docker)
docker-compose.yml
deploy.sh
```

## Development Commands

```bash
# Backend
cd backend && pip install -r requirements.txt && python app.py

# Frontend
cd frontend && npm install && npm start

# Docker (build & deploy)
./deploy.sh
# or manually
docker-compose build && docker-compose up -d
```

## Architecture Notes

- **数据源**: 东方财富 API (`data_fetcher.py`)，需外网访问
- **技术指标**: `indicators.py` 计算 MACD、BOLL、RSI、KDJ、MA、成交量、K 线形态
- **策略系统**: `strategies.py` 使用加权组合策略，买入/卖出信号由多个子策略加权生成，有趋势过滤
- **回测引擎**: `backtest.py`，支持手续费、最大回撤、夏普比率等指标
- **自选股**: `watchlist_manager.py` 使用本地 JSON 文件存储（`backend/watchlist.json`）；用户级自选存于 `users.db` 的 `user_watchlists`
- **账户体系**: `auth.py` + `user_db.py` + `user_service.py`，JWT + RBAC + 套餐配额
- **会员开通**: **无在线支付**。通过加入知识星球，由管理员在 `/admin` 后台手动分配套餐 (`PUT /api/admin/users/:id/subscription`)
- **前端**: 单文件 `frontend/src/App.js`（约 400 行），所有图表配置在同一个组件内

## Key Conventions

- **日期格式**: 后端统一使用 `YYYYMMDD`（如 `20250101`）
- **股票代码**: 纯数字，不带市场前缀（如 `600519`），通过首位数字判断市场
- **API 路径**: `/api/stock/<symbol>`、`/api/backtest`、`/api/search`、`/api/watchlist`
- **信号编码**: `1` = 买入，`-1` = 卖出，`0` = 无信号
- **中文**: 界面、注释、提交信息使用中文
- **涨跌配色**: 涨 = 红色 `#ef4444`，跌 = 绿色 `#22c55e`

## Frontend API 配置

- 开发环境: `http://localhost:5000/api`
- 生产环境: `/api`（nginx 代理到 `backend:5000`）
- 见 `App.js:4`

## Docker 注意事项

- 使用国内镜像：`docker.m.daocloud.io`、`registry.npmmirror.com`、`pypi.tuna.tsinghua.edu.cn`
- 生产环境使用 gunicorn（4 worker）+ nginx
- 后端容器暴露 5000，前端 nginx 暴露 80

## 已知限制

- 无测试代码
- 无 lint/typecheck 配置
- 无 CI/CD
- 前端单文件 1200+ 行，修改时注意 ECharts 配置的复杂性
- 回测结果依赖 akshare 数据质量，`watchlist.json` 变更需重启后端
