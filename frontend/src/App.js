import React, { useState, useCallback } from 'react';
import ReactECharts from 'echarts-for-react';

const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:5000/api';

function App() {
  const [symbol, setSymbol] = useState('600519');
  
  // 获取当前日期并格式化为YYYYMMDD
  const getCurrentDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}${month}${day}`;
  };
  
  const [startDate, setStartDate] = useState('20250101');
  const [endDate, setEndDate] = useState(getCurrentDate());
  const [loading, setLoading] = useState(false);
  const [stockData, setStockData] = useState(null);
  const [activeChart, setActiveChart] = useState('kline');
  const [activeTab, setActiveTab] = useState('signals');
  const [backtestResult, setBacktestResult] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const [watchlist, setWatchlist] = useState([]);

  // 加载自选股
  React.useEffect(() => {
    loadWatchlist();
  }, []);

  const loadWatchlist = async () => {
    try {
      const res = await fetch(`${API_BASE}/watchlist`);
      const data = await res.json();
      setWatchlist(data.data || []);
    } catch (e) {
      console.error('加载自选股失败:', e);
    }
  };

  const searchStock = async (keyword) => {
    if (!keyword || keyword.length < 2) {
      setSearchResults([]);
      setShowSearch(false);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/search?keyword=${keyword}`);
      const data = await res.json();
      setSearchResults(data.data || []);
      setShowSearch(true);
    } catch (e) {
      console.error('搜索失败:', e);
    }
  };

  const selectStock = (stock) => {
    setSymbol(stock['代码']);
    setShowSearch(false);
  };

  const selectWatchStock = (stock) => {
    setSymbol(stock.code);
    fetchDataForCode(stock.code);
  };

  const addToWatchlist = async () => {
    if (!stockData?.name || !symbol) {
      alert('请先获取股票数据');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/watchlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: symbol, name: stockData.name })
      });
      const data = await res.json();
      if (data.success) {
        setWatchlist(data.data);
      } else {
        alert(data.message);
      }
    } catch (e) {
      console.error('添加自选股失败:', e);
      alert('添加失败');
    }
  };

  const removeFromWatchlist = async (code, e) => {
    e.stopPropagation();
    try {
      const res = await fetch(`${API_BASE}/watchlist/${code}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (data.success) {
        setWatchlist(data.data);
      }
    } catch (e) {
      console.error('删除自选股失败:', e);
    }
  };

  const fetchDataForCode = async (code) => {
    if (!code) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/stock/${code}?start_date=${startDate}&end_date=${endDate}`);
      const data = await res.json();
      if (data.error) {
        alert(data.error);
      } else {
        setStockData(data);
      }
    } catch (e) {
      alert('获取数据失败，请确保后端服务已启动');
    }
    setLoading(false);
  };

  const fetchData = useCallback(async () => {
    if (!symbol) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/stock/${symbol}?start_date=${startDate}&end_date=${endDate}`);
      const data = await res.json();
      if (data.error) {
        alert(data.error);
      } else {
        setStockData(data);
      }
    } catch (e) {
      alert('获取数据失败，请确保后端服务已启动');
    }
    setLoading(false);
  }, [symbol, startDate, endDate]);

  const runBacktest = async () => {
    if (!symbol) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/backtest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          start_date: startDate,
          end_date: endDate,
          config: {
            initial_capital: 100000,
            commission_rate: 0.001,
            buy_threshold: 0.08,
            sell_threshold: 0.12
          }
        })
      });
      const data = await res.json();
      if (data.error) {
        alert(data.error);
      } else {
        setBacktestResult(data);
        setActiveTab('backtest');
      }
    } catch (e) {
      alert('回测失败');
    }
    setLoading(false);
  };

  const getKlineOption = () => {
    if (!stockData?.data) return {};
    
    const data = stockData.data;
    const dates = data.map(d => d.date);
    const candleData = data.map(d => [d.open, d.close, d.low, d.high]);
    
    // 标记买卖点 - 买入信号强度 >= 10% 才显示
    const buyPoints = data.filter(d => d.signal === 1 && d.buy_score >= 0.1).map(d => ({
      name: `B`,
      coord: [d.date, d.low],
      symbol: 'circle',
      symbolSize: 20,
      label: {
        show: true,
        formatter: 'B',
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold'
      },
      itemStyle: { 
        color: '#ef4444',
        borderColor: '#fff',
        borderWidth: 1
      }
    }));
    
    // 卖出信号条件：signal=-1 且 收盘价跌破MA5（防主升浪卖飞）
    const sellPoints = data.filter(d => {
      if (d.signal !== -1) return false;
      return d.close < d.ma5;
    }).map(d => ({
      name: `S`,
      coord: [d.date, d.high],
      symbol: 'circle',
      symbolSize: 20,
      label: {
        show: true,
        formatter: 'S',
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold'
      },
      itemStyle: { 
        color: '#3b82f6',
        borderColor: '#fff',
        borderWidth: 1
      }
    }));

    // MACD背离检测
    const detectMACDDivergence = () => {
      const topDivergence = [];
      const bottomDivergence = [];
      const lookback = 20;
      
      for (let i = lookback; i < data.length; i++) {
        let isPriceHigh = true;
        for (let j = 1; j <= 5; j++) {
          if (i - j >= 0 && data[i - j].close >= data[i].close) { isPriceHigh = false; break; }
          if (i + j < data.length && data[i + j].close >= data[i].close) { isPriceHigh = false; break; }
        }
        
        let isPriceLow = true;
        for (let j = 1; j <= 5; j++) {
          if (i - j >= 0 && data[i - j].close <= data[i].close) { isPriceLow = false; break; }
          if (i + j < data.length && data[i + j].close <= data[i].close) { isPriceLow = false; break; }
        }
        
        if (isPriceHigh) {
          for (let j = i - lookback; j < i - 5; j++) {
            let isPrevHigh = true;
            for (let k = 1; k <= 5; k++) {
              if (j - k >= 0 && data[j - k].close >= data[j].close) { isPrevHigh = false; break; }
              if (j + k < data.length && data[j + k].close >= data[j].close) { isPrevHigh = false; break; }
            }
            if (isPrevHigh) {
              if (data[i].close > data[j].close && data[i].macd < data[j].macd && data[i].macd > 0) {
                topDivergence.push({
                  name: '顶背离',
                  coord: [data[i].date, data[i].macd],
                  symbol: 'arrow',
                  symbolSize: 14,
                  label: { show: true, formatter: '顶背离', color: '#ef4444', fontSize: 10, fontWeight: 'bold', position: 'top' },
                  itemStyle: { color: '#ef4444' }
                });
              }
              break;
            }
          }
        }
        
        if (isPriceLow) {
          for (let j = i - lookback; j < i - 5; j++) {
            let isPrevLow = true;
            for (let k = 1; k <= 5; k++) {
              if (j - k >= 0 && data[j - k].close <= data[j].close) { isPrevLow = false; break; }
              if (j + k < data.length && data[j + k].close <= data[j].close) { isPrevLow = false; break; }
            }
            if (isPrevLow) {
              if (data[i].close < data[j].close && data[i].macd > data[j].macd && data[i].macd < 0) {
                bottomDivergence.push({
                  name: '底背离',
                  coord: [data[i].date, data[i].macd],
                  symbol: 'arrow',
                  symbolSize: 14,
                  label: { show: true, formatter: '底背离', color: '#22c55e', fontSize: 10, fontWeight: 'bold', position: 'bottom' },
                  itemStyle: { color: '#22c55e' }
                });
              }
              break;
            }
          }
        }
      }
      return { topDivergence, bottomDivergence };
    };

    const { topDivergence, bottomDivergence } = detectMACDDivergence();

    return {
      backgroundColor: '#0f0f1a',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(26, 26, 46, 0.9)',
        borderColor: '#2a2a4a',
        textStyle: { color: '#fff' },
        formatter: function(params) {
          const date = params[0]?.axisValue;
          const dataItem = data.find(d => d.date === date);
          
          let html = `<div style="padding: 8px">
            <div style="font-weight: bold; margin-bottom: 4px">${stockData.name || ''} (${symbol})</div>
            <div style="font-size: 12px; color: #a0a0a0; margin-bottom: 8px">${date || ''}</div>`;
          params.forEach(p => {
            // 跳过标记点
            if (p.componentType === 'markPoint') return;
            
            if (p.seriesType === 'candlestick') {
              html += `<div>开盘: ${p.data[1]?.toFixed(2)}</div>
                <div>收盘: ${p.data[2]?.toFixed(2)}</div>
                <div>最低: ${p.data[3]?.toFixed(2)}</div>
                <div>最高: ${p.data[4]?.toFixed(2)}</div>`;
            } else if (p.seriesType === 'line') {
              // 均线、DIF、DEA等线型数据
              const val = typeof p.data === 'number' ? p.data : null;
              if (val !== null) {
                html += `<div>${p.seriesName}: ${val.toFixed(2)}</div>`;
              }
            } else if (p.seriesType === 'bar') {
              // 柱状图数据（MACD柱、成交量）
              const val = (typeof p.data === 'object' && p.data !== null) ? p.data.value : p.data;
              if (typeof val === 'number') {
                html += `<div>${p.seriesName}: ${val.toFixed(2)}</div>`;
              }
            }
          });
          
          if (dataItem && dataItem.signal !== 0) {
            if (dataItem.signal === 1) {
              html += `<div style="color: #ef4444; margin-top: 4px">买入信号强度: ${(dataItem.buy_score * 100).toFixed(1)}%</div>`;
            } else if (dataItem.signal === -1) {
              html += `<div style="color: #3b82f6; margin-top: 4px">卖出信号强度: ${(dataItem.sell_score * 100).toFixed(1)}%</div>`;
            }
          }
          
          html += '</div>';
          return html;
        }
      },
      legend: {
        data: ['K线', 'MA5', 'MA10', 'MA20', 'DIF', 'DEA', 'MACD柱'],
        textStyle: { color: '#a0a0a0' },
        top: 0
      },
      grid: [
        { left: '10%', right: '5%', top: '12%', height: '40%' },
        { left: '10%', right: '5%', top: '55%', height: '16%' },
        { left: '10%', right: '5%', top: '74%', height: '14%' }
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          gridIndex: 0,
          axisLine: { lineStyle: { color: '#2a2a4a' } },
          axisLabel: { show: false }
        },
        {
          type: 'category',
          data: dates,
          gridIndex: 1,
          axisLine: { lineStyle: { color: '#2a2a4a' } },
          axisLabel: { show: false }
        },
        {
          type: 'category',
          data: dates,
          gridIndex: 2,
          axisLine: { lineStyle: { color: '#2a2a4a' } },
          axisLabel: { color: '#a0a0a0', fontSize: 10 }
        }
      ],
      yAxis: [
        {
          scale: true,
          gridIndex: 0,
          splitLine: { lineStyle: { color: '#2a2a4a' } },
          axisLabel: { color: '#a0a0a0' }
        },
        {
          scale: true,
          gridIndex: 1,
          splitLine: { show: false },
          axisLabel: { show: false }
        },
        {
          scale: true,
          gridIndex: 2,
          splitLine: { show: false },
          axisLabel: { show: false }
        }
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1, 2], start: 50, end: 100 },
        { type: 'slider', xAxisIndex: [0, 1, 2], bottom: 0, height: 20 }
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: candleData,
          xAxisIndex: 0,
          yAxisIndex: 0,
          itemStyle: {
            color: '#ef4444',
            color0: '#22c55e',
            borderColor: '#ef4444',
            borderColor0: '#22c55e'
          },
          markPoint: {
            data: [...buyPoints, ...sellPoints]
          }
        },
        {
          name: 'MA5',
          type: 'line',
          data: data.map(d => d.ma5),
          xAxisIndex: 0,
          yAxisIndex: 0,
          lineStyle: { color: '#fbbf24', width: 1 },
          symbol: 'none'
        },
        {
          name: 'MA10',
          type: 'line',
          data: data.map(d => d.ma10),
          xAxisIndex: 0,
          yAxisIndex: 0,
          lineStyle: { color: '#60a5fa', width: 1 },
          symbol: 'none'
        },
        {
          name: 'MA20',
          type: 'line',
          data: data.map(d => d.ma20),
          xAxisIndex: 0,
          yAxisIndex: 0,
          lineStyle: { color: '#a78bfa', width: 1 },
          symbol: 'none'
        },
        {
          name: '布林带',
          type: 'line',
          data: data.map(d => d.boll_upper),
          xAxisIndex: 0,
          yAxisIndex: 0,
          lineStyle: { color: '#3b82f6', width: 1, type: 'dashed' },
          symbol: 'none'
        },
        {
          name: '布林中轨',
          type: 'line',
          data: data.map(d => d.boll_middle),
          xAxisIndex: 0,
          yAxisIndex: 0,
          lineStyle: { color: '#3b82f6', width: 1 },
          symbol: 'none'
        },
        {
          name: '布林下轨',
          type: 'line',
          data: data.map(d => d.boll_lower),
          xAxisIndex: 0,
          yAxisIndex: 0,
          lineStyle: { color: '#3b82f6', width: 1, type: 'dashed' },
          symbol: 'none'
        },
        // MACD DIF
        {
          name: 'DIF',
          type: 'line',
          data: data.map(d => d.macd),
          xAxisIndex: 1,
          yAxisIndex: 1,
          lineStyle: { color: '#3b82f6', width: 1.5 },
          symbol: 'none',
          markPoint: {
            data: [...topDivergence, ...bottomDivergence]
          }
        },
        // MACD DEA
        {
          name: 'DEA',
          type: 'line',
          data: data.map(d => d.macd_signal),
          xAxisIndex: 1,
          yAxisIndex: 1,
          lineStyle: { color: '#fbbf24', width: 1.5 },
          symbol: 'none'
        },
        // MACD柱
        {
          name: 'MACD柱',
          type: 'bar',
          data: data.map(d => ({
            value: d.macd_hist,
            itemStyle: { color: d.macd_hist >= 0 ? '#ef4444' : '#22c55e' }
          })),
          xAxisIndex: 1,
          yAxisIndex: 1
        },
        // 成交量
        {
          name: '成交量',
          type: 'bar',
          data: data.map(d => ({
            value: d.volume,
            itemStyle: { color: d.close >= d.open ? '#ef4444' : '#22c55e' }
          })),
          xAxisIndex: 2,
          yAxisIndex: 2
        }
      ]
    };
  };

  const getMACDOption = () => {
    if (!stockData?.data) return {};
    
    const data = stockData.data;
    const dates = data.map(d => d.date);

    // MACD背离检测
    const detectMACDDivergence = () => {
      const topDivergence = [];
      const bottomDivergence = [];
      const lookback = 20; // 回看窗口
      
      for (let i = lookback; i < data.length; i++) {
        // 找局部高点（价格）
        let isPriceHigh = true;
        for (let j = 1; j <= 5; j++) {
          if (i - j >= 0 && data[i - j].close >= data[i].close) { isPriceHigh = false; break; }
          if (i + j < data.length && data[i + j].close >= data[i].close) { isPriceHigh = false; break; }
        }
        
        // 找局部低点（价格）
        let isPriceLow = true;
        for (let j = 1; j <= 5; j++) {
          if (i - j >= 0 && data[i - j].close <= data[i].close) { isPriceLow = false; break; }
          if (i + j < data.length && data[i + j].close <= data[i].close) { isPriceLow = false; break; }
        }
        
        if (isPriceHigh) {
          // 检查前一个局部高点
          for (let j = i - lookback; j < i - 5; j++) {
            let isPrevHigh = true;
            for (let k = 1; k <= 5; k++) {
              if (j - k >= 0 && data[j - k].close >= data[j].close) { isPrevHigh = false; break; }
              if (j + k < data.length && data[j + k].close >= data[j].close) { isPrevHigh = false; break; }
            }
            if (isPrevHigh) {
              // 顶背离：价格创新高但MACD未创新高
              if (data[i].close > data[j].close && data[i].macd < data[j].macd && data[i].macd > 0) {
                topDivergence.push({
                  name: '顶背离',
                  coord: [data[i].date, data[i].macd],
                  symbol: 'arrow',
                  symbolSize: 16,
                  label: {
                    show: true,
                    formatter: '顶背离',
                    color: '#ef4444',
                    fontSize: 11,
                    fontWeight: 'bold',
                    position: 'top'
                  },
                  itemStyle: { color: '#ef4444' }
                });
              }
              break;
            }
          }
        }
        
        if (isPriceLow) {
          // 检查前一个局部低点
          for (let j = i - lookback; j < i - 5; j++) {
            let isPrevLow = true;
            for (let k = 1; k <= 5; k++) {
              if (j - k >= 0 && data[j - k].close <= data[j].close) { isPrevLow = false; break; }
              if (j + k < data.length && data[j + k].close <= data[j].close) { isPrevLow = false; break; }
            }
            if (isPrevLow) {
              // 底背离：价格创新低但MACD未创新低
              if (data[i].close < data[j].close && data[i].macd > data[j].macd && data[i].macd < 0) {
                bottomDivergence.push({
                  name: '底背离',
                  coord: [data[i].date, data[i].macd],
                  symbol: 'arrow',
                  symbolSize: 16,
                  label: {
                    show: true,
                    formatter: '底背离',
                    color: '#22c55e',
                    fontSize: 11,
                    fontWeight: 'bold',
                    position: 'bottom'
                  },
                  itemStyle: { color: '#22c55e' }
                });
              }
              break;
            }
          }
        }
      }
      
      return { topDivergence, bottomDivergence };
    };

    const { topDivergence, bottomDivergence } = detectMACDDivergence();
 
    return {
      backgroundColor: '#0f0f1a',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(26, 26, 46, 0.9)',
        borderColor: '#2a2a4a',
        textStyle: { color: '#fff' },
        formatter: function(params) {
          const date = params[0]?.axisValue;
          let html = `<div style="padding: 8px">
            <div style="font-weight: bold; margin-bottom: 4px">${stockData.name || ''} (${symbol})</div>
            <div style="font-size: 12px; color: #a0a0a0; margin-bottom: 8px">${date || ''}</div>`;
          params.forEach(p => {
            const val = p.data;
            const numVal = typeof val === 'object' ? val.value : val;
            if (typeof numVal === 'number') {
              html += `<div>${p.seriesName}: ${numVal.toFixed(4)}</div>`;
            }
          });
          html += '</div>';
          return html;
        }
      },
      legend: {
        data: ['DIF', 'DEA', 'MACD柱', '顶背离', '底背离'],
        textStyle: { color: '#a0a0a0' },
        top: 0
      },
      grid: { left: '10%', right: '5%', top: '12%', bottom: '15%' },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#2a2a4a' } },
        axisLabel: { color: '#a0a0a0' }
      },
      yAxis: {
        scale: true,
        splitLine: { lineStyle: { color: '#2a2a4a' } },
        axisLabel: { color: '#a0a0a0' }
      },
      dataZoom: [
        { type: 'inside', start: 50, end: 100 },
        { type: 'slider', bottom: 0, height: 20 }
      ],
      series: [
        {
          name: 'DIF',
          type: 'line',
          data: data.map(d => d.macd),
          lineStyle: { color: '#3b82f6', width: 2 },
          symbol: 'none'
        },
        {
          name: 'DEA',
          type: 'line',
          data: data.map(d => d.macd_signal),
          lineStyle: { color: '#fbbf24', width: 2 },
          symbol: 'none'
        },
        {
          name: 'MACD柱',
          type: 'bar',
          data: data.map(d => ({
            value: d.macd_hist,
            itemStyle: { color: d.macd_hist >= 0 ? '#ef4444' : '#22c55e' }
          }))
        },
        {
          name: '顶背离',
          type: 'scatter',
          data: topDivergence.map(d => ({
            value: d.coord[1],
            ...d
          })),
          markPoint: {
            data: topDivergence,
            symbol: 'arrow',
            symbolSize: 16,
            label: {
              show: true,
              formatter: '顶背离',
              color: '#ef4444',
              fontSize: 11,
              fontWeight: 'bold',
              position: 'top'
            },
            itemStyle: { color: '#ef4444' }
          }
        },
        {
          name: '底背离',
          type: 'scatter',
          data: bottomDivergence.map(d => ({
            value: d.coord[1],
            ...d
          })),
          markPoint: {
            data: bottomDivergence,
            symbol: 'arrow',
            symbolSize: 16,
            label: {
              show: true,
              formatter: '底背离',
              color: '#22c55e',
              fontSize: 11,
              fontWeight: 'bold',
              position: 'bottom'
            },
            itemStyle: { color: '#22c55e' }
          }
        }
      ]
    };
  };

  const getRSIOption = () => {
    if (!stockData?.data) return {};
    
    const data = stockData.data;
    const dates = data.map(d => d.date);
 
    return {
      backgroundColor: '#0f0f1a',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(26, 26, 46, 0.9)',
        borderColor: '#2a2a4a',
        textStyle: { color: '#fff' },
        formatter: function(params) {
          const date = params[0]?.axisValue;
          let html = `<div style="padding: 8px">
            <div style="font-weight: bold; margin-bottom: 4px">${stockData.name || ''} (${symbol})</div>
            <div style="font-size: 12px; color: #a0a0a0; margin-bottom: 8px">${date || ''}</div>`;
          params.forEach(p => {
            html += `<div>${p.seriesName}: ${p.data?.toFixed(2)}</div>`;
          });
          html += '</div>';
          return html;
        }
      },
      grid: { left: '10%', right: '5%', top: '12%', bottom: '15%' },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#2a2a4a' } }
      },
      yAxis: {
        min: 0,
        max: 100,
        splitLine: { lineStyle: { color: '#2a2a4a' } }
      },
      dataZoom: [
        { type: 'inside', start: 50, end: 100 },
        { type: 'slider', bottom: 0, height: 20 }
      ],
      series: [
        {
          name: 'RSI',
          type: 'line',
          data: data.map(d => d.rsi),
          lineStyle: { color: '#a78bfa' },
          symbol: 'none',
          markLine: {
            data: [
              { yAxis: 70, lineStyle: { color: '#ef4444' } },
              { yAxis: 30, lineStyle: { color: '#22c55e' } }
            ]
          }
        }
      ]
    };
  };

  const getKDJOotion = () => {
    if (!stockData?.data) return {};
    
    const data = stockData.data;
    const dates = data.map(d => d.date);
 
    return {
      backgroundColor: '#0f0f1a',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(26, 26, 46, 0.9)',
        borderColor: '#2a2a4a',
        textStyle: { color: '#fff' },
        formatter: function(params) {
          const date = params[0]?.axisValue;
          let html = `<div style="padding: 8px">
            <div style="font-weight: bold; margin-bottom: 4px">${stockData.name || ''} (${symbol})</div>
            <div style="font-size: 12px; color: #a0a0a0; margin-bottom: 8px">${date || ''}</div>`;
          params.forEach(p => {
            html += `<div>${p.seriesName}: ${p.data?.toFixed(2)}</div>`;
          });
          html += '</div>';
          return html;
        }
      },
      grid: { left: '10%', right: '5%', top: '12%', bottom: '15%' },
      xAxis: {
        type: 'category',
        data: dates
      },
      yAxis: {
        min: 0,
        max: 100,
        splitLine: { lineStyle: { color: '#2a2a4a' } }
      },
      dataZoom: [
        { type: 'inside', start: 50, end: 100 },
        { type: 'slider', bottom: 0, height: 20 }
      ],
      series: [
        {
          name: 'K',
          type: 'line',
          data: data.map(d => d.kdj_k),
          lineStyle: { color: '#3b82f6' },
          symbol: 'none'
        },
        {
          name: 'D',
          type: 'line',
          data: data.map(d => d.kdj_d),
          lineStyle: { color: '#fbbf24' },
          symbol: 'none'
        },
        {
          name: 'J',
          type: 'line',
          data: data.map(d => d.kdj_j),
          lineStyle: { color: '#a78bfa' },
          symbol: 'none'
        }
      ]
    };
  };

  const getEquityOption = () => {
    if (!backtestResult?.equity_curve) return {};
    
    const data = backtestResult.equity_curve;
    const dates = data.map(d => d.date);
    const equity = data.map(d => d.equity);

    return {
      backgroundColor: '#0f0f1a',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(26, 26, 46, 0.9)',
        borderColor: '#2a2a4a',
        textStyle: { color: '#fff' },
        formatter: (params) => {
          const p = params[0];
          const value = p.value || 0;
          return `<div style="padding: 8px">
            <div style="font-weight: bold; margin-bottom: 4px">${stockData.name || ''} (${symbol})</div>
            <div style="font-size: 12px; color: #a0a0a0; margin-bottom: 8px">${p.name}</div>
            <div>权益: ¥${value.toLocaleString()}</div>
          </div>`;
        }
      },
      grid: { left: '10%', right: '5%', top: '12%', bottom: '15%' },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: { color: '#a0a0a0' }
      },
      yAxis: {
        scale: true,
        splitLine: { lineStyle: { color: '#2a2a4a' } },
        axisLabel: {
          color: '#a0a0a0',
          formatter: (v) => `${(v/10000).toFixed(0)}万`
        }
      },
      series: [{
        name: '权益曲线',
        type: 'line',
        data: equity,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
              { offset: 1, color: 'rgba(59, 130, 246, 0)' }
            ]
          }
        },
        lineStyle: { color: '#3b82f6', width: 2 },
        symbol: 'none'
      }]
    };
  };

  const getChartOption = () => {
    switch (activeChart) {
      case 'macd': return getMACDOption();
      case 'rsi': return getRSIOption();
      case 'kdj': return getKDJOotion();
      case 'backtest': return getEquityOption();
      default: return getKlineOption();
    }
  };

  const renderMetrics = () => {
    if (!backtestResult?.metrics) return null;
    const m = backtestResult.metrics;
    
    const metrics = [
      { label: '总收益率', value: `${m.total_return || 0}%`, positive: (m.total_return || 0) > 0 },
      { label: '年化收益率', value: `${m.annual_return || 0}%`, positive: (m.annual_return || 0) > 0 },
      { label: '最大回撤', value: `${m.max_drawdown || 0}%`, negative: true },
      { label: '胜率', value: `${m.win_rate || 0}%`, positive: (m.win_rate || 0) > 50 },
      { label: '总交易次数', value: m.total_trades || 0 },
      { label: '盈亏比', value: m.profit_loss_ratio || 0 },
      { label: '初始资金', value: `¥${(m.initial_capital || 0).toLocaleString()}` },
      { label: '最终资金', value: `¥${(m.final_equity || 0).toLocaleString()}`, positive: (m.final_equity || 0) > (m.initial_capital || 0) }
    ];
    
    return (
      <div className="metrics-grid">
        {metrics.map((item, i) => (
          <div key={i} className="metric-card">
            <div className="metric-label">{item.label}</div>
            <div className={`metric-value ${item.positive ? 'positive' : item.negative ? 'negative' : ''}`}>
              {item.value}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderSignals = () => {
    if (!stockData?.data) return null;
    
    const signals = stockData.data.filter(d => d.signal !== 0).sort((a, b) => {
      return new Date(b.date) - new Date(a.date);
    });
    
    if (signals.length === 0) {
      return (
        <div className="empty-state">
          <p>暂无买卖信号</p>
        </div>
      );
    }
    
    return (
      <div className="signal-list">
        {signals.map((s, i) => (
          <div key={i} className={`signal-item ${s.signal === 1 ? 'buy' : 'sell'}`}>
            <div className="signal-info">
              <span className="signal-date">{s.date}</span>
              <span className={`signal-type ${s.signal === 1 ? 'buy' : 'sell'}`}>
                {s.signal === 1 ? '买入信号' : '卖出信号'}
              </span>
              <span className="signal-price">¥{s.close}</span>
            </div>
            <div className="signal-score">
              {s.signal === 1 ? `强度: ${(s.buy_score * 100).toFixed(0)}%` : `强度: ${(s.sell_score * 100).toFixed(0)}%`}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderBacktest = () => {
    if (!backtestResult) {
      return (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <p className="empty-state-text">尚未运行回测</p>
          <p className="empty-state-hint">点击"运行回测"按钮开始</p>
        </div>
      );
    }
    
    return (
      <div>
        <h3 style={{ marginBottom: 16 }}>回测指标</h3>
        {renderMetrics()}
        
        <h3 style={{ margin: '24px 0 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>交易记录</span>
          {backtestResult.trades.length > 0 && (
            <span style={{ fontSize: 13, color: '#a0a0a0', fontWeight: 'normal' }}>
              共 {backtestResult.trades.length} 笔
              （买入 {(backtestResult.trades.filter(t => t.type === 'buy').length)} 笔，
              卖出 {(backtestResult.trades.filter(t => t.type === 'sell').length)} 笔）
            </span>
          )}
        </h3>
        <div className="trade-list">
          {backtestResult.trades.length === 0 ? (
            <div className="empty-state">
              <p>暂无交易记录</p>
            </div>
          ) : (
            backtestResult.trades.slice().reverse().map((t, i) => (
              <div key={i} className="trade-item">
                <span className={`trade-type ${t.type}`}>{t.type === 'buy' ? '买入' : '卖出'}</span>
                <div className="trade-info">
                  <span>{t.date}</span>
                  <span>¥{(t.price || 0).toFixed(2)}</span>
                  <span>{t.shares || 0}股</span>
                  {t.type === 'sell' && t.profit_pct != null && (
                    <span className={`trade-profit ${(t.profit || 0) > 0 ? 'positive' : 'negative'}`}>
                      {(t.profit || 0) > 0 ? '+' : ''}{(t.profit_pct || 0).toFixed(2)}%
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-icon">📈</div>
          <span className="logo-text">ATradeReview</span>
        </div>
        
        <div className="controls">
          <div className="input-group" style={{ position: 'relative' }}>
            <label>股票代码</label>
            <input
              className="input"
              value={symbol}
              onChange={(e) => {
                setSymbol(e.target.value);
                searchStock(e.target.value);
              }}
              onFocus={() => searchStock(symbol)}
              onBlur={() => setTimeout(() => setShowSearch(false), 200)}
              placeholder="输入代码或名称"
            />
            {showSearch && searchResults.length > 0 && (
              <div className="search-results">
                {searchResults.map((s, i) => (
                  <div key={i} className="search-item" onClick={() => selectStock(s)}>
                    <span className="stock-code">{s['代码']}</span>
                    <span className="stock-name">{s['名称']}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="input-group">
            <label>开始日期</label>
            <input
              className="input input-sm"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              placeholder="YYYYMMDD"
            />
          </div>
          
          <div className="input-group">
            <label>结束日期</label>
            <input
              className="input input-sm"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              placeholder="YYYYMMDD"
            />
          </div>
          
          <button className="btn btn-primary" onClick={fetchData} disabled={loading}>
            {loading ? '加载中...' : '获取数据'}
          </button>
          
          <button className="btn btn-watchlist-add" onClick={addToWatchlist} disabled={loading || !stockData}>
            ⭐ 加入自选
          </button>
          
          <button className="btn btn-secondary" onClick={runBacktest} disabled={loading || !stockData}>
            运行回测
          </button>
        </div>
      </header>
      
      <div className="main-content">
        <div className="watchlist-sidebar">
          <div className="watchlist-header">
            <span>⭐ 自选股 ({watchlist.length})</span>
          </div>
          <div className="watchlist-content">
            {watchlist.map((stock, i) => (
              <div key={i} className="watchlist-item-card" onClick={() => selectWatchStock(stock)}>
                <div className="watchlist-stock-info">
                  <span className="watchlist-code">{stock.code}</span>
                  <span className="watchlist-name">{stock.name}</span>
                </div>
                <button className="btn-delete-watchlist" onClick={(e) => removeFromWatchlist(stock.code, e)}>
                  ✕
                </button>
              </div>
            ))}
            {watchlist.length === 0 && (
              <div className="watchlist-empty">
                <p>暂无自选股</p>
              </div>
            )}
          </div>
        </div>
        
        <div className="chart-section">
          <div className="chart-tabs">
            <button className={`tab ${activeChart === 'kline' ? 'active' : ''}`} onClick={() => setActiveChart('kline')}>
              K线图
            </button>
            <button className={`tab ${activeChart === 'rsi' ? 'active' : ''}`} onClick={() => setActiveChart('rsi')}>
              RSI
            </button>
            <button className={`tab ${activeChart === 'kdj' ? 'active' : ''}`} onClick={() => setActiveChart('kdj')}>
              KDJ
            </button>
            {backtestResult && (
              <button className={`tab ${activeChart === 'backtest' ? 'active' : ''}`} onClick={() => setActiveChart('backtest')}>
                权益曲线
              </button>
            )}
          </div>
          
          <div className="chart-legend">
            <div className="legend-item">
              <div className="legend-dot" style={{ background: '#ef4444' }}></div>
              <span>B 买入</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot" style={{ background: '#3b82f6' }}></div>
              <span>S 卖出</span>
            </div>
          </div>
          
          <div className="chart-container">
            {!stockData ? (
              <div className="empty-state">
                <div className="empty-state-icon">📊</div>
                <p className="empty-state-text">等待数据加载</p>
                <p className="empty-state-hint">输入股票代码并点击"获取数据"</p>
              </div>
            ) : loading ? (
              <div className="loading">
                <div className="spinner"></div>
              </div>
            ) : (
              <ReactECharts option={getChartOption()} style={{ height: '100%' }} />
            )}
          </div>
        </div>
        
        <div className="sidebar">
          <div className="sidebar-tabs">
            <button className={`sidebar-tab ${activeTab === 'signals' ? 'active' : ''}`} onClick={() => setActiveTab('signals')}>
              买卖信号 ({stockData?.summary?.buy_signals || 0}/{stockData?.summary?.sell_signals || 0})
            </button>
            <button className={`sidebar-tab ${activeTab === 'backtest' ? 'active' : ''}`} onClick={() => setActiveTab('backtest')}>
              回测结果
            </button>
          </div>
          
          <div className="sidebar-content">
            {activeTab === 'signals' ? renderSignals() : renderBacktest()}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
