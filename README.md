# ATradeReview - A股交易复盘工具

一个基于技术分析的A股交易复盘工具，支持多种技术指标和买卖点识别。

## 功能特性

### 技术指标
- **MACD**: 金叉/死叉信号、柱状图分析
- **布林带 (BOLL)**: 上中下轨、突破信号
- **RSI**: 超买超卖判断
- **KDJ**: 金叉死叉信号
- **均线**: MA5/MA10/MA20/MA60
- **成交量**: 量比、放量/缩量分析
- **K线形态**: 十字星、锤子线、吞没形态等

### 买卖策略
1. MACD金叉 + 成交量放大 → 买入
2. 布林带下轨支撑 → 买入
3. RSI超卖回升 → 买入
4. KDJ超卖区金叉 → 买入
5. MACD死叉 → 卖出
6. 布林带上轨压力 → 卖出
7. K线形态识别

### 回测功能
- 支持历史数据回测
- 计算收益率、胜率、最大回撤
- 交易记录展示
- 权益曲线可视化

## 项目结构

```
ATradeReview/
├── backend/
│   ├── app.py              # Flask API服务
│   ├── data_fetcher.py     # 数据获取模块 (akshare)
│   ├── indicators.py       # 技术指标计算
│   ├── strategies.py       # 买卖策略
│   ├── backtest.py         # 回测引擎
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.js          # 主组件
        └── index.css       # 样式
```

## 安装运行

### 1. 启动后端服务

```bash
cd backend
pip install -r requirements.txt
python app.py
```

后端服务默认运行在 http://localhost:5000

### 2. 启动前端

```bash
cd frontend
npm start
```

前端默认运行在 http://localhost:3000

## 使用说明

1. 输入股票代码（如 600519 贵州茅台）
2. 设置时间范围
3. 点击"获取数据"加载K线数据和技术指标
4. 查看K线图上的买卖信号标记
5. 点击"运行回测"验证策略效果

## 技术栈

- **后端**: Python + Flask + pandas + akshare
- **前端**: React + ECharts
- **数据源**: akshare (免费A股数据)
