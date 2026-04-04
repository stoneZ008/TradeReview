import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json

def get_market_code(symbol):
    """
    根据股票代码获取市场代码
    """
    if symbol.startswith('6'):
        return '1.' + symbol  # 沪市
    elif symbol.startswith('0') or symbol.startswith('3'):
        return '0.' + symbol  # 深市
    elif symbol.startswith('688'):
        return '1.' + symbol  # 科创板
    else:
        return '0.' + symbol

def fetch_stock_data(symbol, start_date=None, end_date=None, adjust="qfq"):
    """
    从东方财富获取真实A股历史数据
    
    参数:
        symbol: 股票代码，如 '600519'
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        adjust: 复权方式 'qfq'前复权, ''不复权
    """
    # 清理股票代码
    symbol = symbol.strip().upper()
    if symbol.startswith(('SH', 'SZ')):
        symbol = symbol[2:]
    
    # 默认日期
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    
    # 转换日期格式
    start_dt = datetime.strptime(start_date, '%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d')
    
    secid = get_market_code(symbol)
    
    # 东方财富K线API
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    
    params = {
        'secid': secid,
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'klt': '101',  # 日K
        'fqt': '1' if adjust == 'qfq' else '0',  # 前复权
        'beg': start_date,
        'end': end_date,
        'lmt': '1000',
        'ut': 'fa5fd1943c7b386f172d6893dbfba10b'
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        data = response.json()
        
        if data.get('data') and data['data'].get('klines'):
            klines = data['data']['klines']
            
            records = []
            for line in klines:
                parts = line.split(',')
                # 日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
                records.append({
                    'date': pd.to_datetime(parts[0]),
                    'open': float(parts[1]),
                    'close': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'volume': float(parts[5]),
                    'amount': float(parts[6]),
                    'amplitude': float(parts[7]),
                    'pct_change': float(parts[8]),
                    'change': float(parts[9]),
                    'turnover': float(parts[10])
                })
            
            df = pd.DataFrame(records)
            df = df.set_index('date')
            df = df.sort_index()
            
            return df
        else:
            print(f"API返回数据为空: {data.get('message', '未知错误')}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"获取数据失败: {e}")
        return pd.DataFrame()

def search_stock(keyword):
    """
    搜索股票 - 使用东方财富API
    """
    url = "https://searchapi.eastmoney.com/api/suggest/get"
    
    params = {
        'type': '14',
        'token': 'D43BF722C8E33BDC906FB84D85E326E8',
        'count': '20',
        'query': keyword
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.eastmoney.com/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('QuotationCodeTable') and data['QuotationCodeTable'].get('Data'):
            stocks = []
            for item in data['QuotationCodeTable']['Data']:
                code = item.get('Code', '')
                name = item.get('Name', '')
                market = item.get('Market', 0)
                
                # 只要A股
                if market in [1, 0] and (code.startswith('6') or code.startswith('0') or code.startswith('3')):
                    stocks.append({
                        '代码': code,
                        '名称': name,
                        '市场': '沪市' if market == 1 else '深市'
                    })
            
            return pd.DataFrame(stocks) if stocks else get_default_stock_list()
        else:
            return get_default_stock_list()
            
    except Exception as e:
        print(f"搜索失败: {e}")
        return get_default_stock_list()

def get_default_stock_list():
    """获取默认股票列表"""
    stocks = [
        # 主板
        {'代码': '600519', '名称': '贵州茅台', '市场': '沪市'},
        {'代码': '601318', '名称': '中国平安', '市场': '沪市'},
        {'代码': '600036', '名称': '招商银行', '市场': '沪市'},
        {'代码': '601398', '名称': '工商银行', '市场': '沪市'},
        {'代码': '000001', '名称': '平安银行', '市场': '深市'},
        {'代码': '000858', '名称': '五粮液', '市场': '深市'},
        {'代码': '000333', '名称': '美的集团', '市场': '深市'},
        {'代码': '002594', '名称': '比亚迪', '市场': '深市'},
        # 科创板
        {'代码': '688981', '名称': '中芯国际', '市场': '沪市'},
        {'代码': '688256', '名称': '寒武纪', '市场': '沪市'},
        {'代码': '688111', '名称': '金山办公', '市场': '沪市'},
        {'代码': '688008', '名称': '澜起科技', '市场': '沪市'},
        # 创业板
        {'代码': '300750', '名称': '宁德时代', '市场': '深市'},
        {'代码': '300059', '名称': '东方财富', '市场': '深市'},
    ]
    return pd.DataFrame(stocks)

def get_stock_info(symbol):
    """
    获取股票实时信息
    """
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    
    symbol = symbol.strip().upper()
    if symbol.startswith(('SH', 'SZ')):
        symbol = symbol[2:]
    
    secid = get_market_code(symbol)
    
    params = {
        'secid': secid,
        'fields': 'f43,f44,f45,f46,f47,f48,f57,f58,f170',
        'ut': 'fa5fd1943c7b386f172d6893dbfba10b'
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('data'):
            d = data['data']
            return {
                'code': symbol,
                'name': d.get('f58', ''),
                'price': d.get('f43', 0) / 100 if d.get('f43') else 0,
                'high': d.get('f44', 0) / 100 if d.get('f44') else 0,
                'low': d.get('f45', 0) / 100 if d.get('f45') else 0,
                'open': d.get('f46', 0) / 100 if d.get('f46') else 0,
                'volume': d.get('f47', 0),
                'amount': d.get('f48', 0),
                'pct_change': d.get('f170', 0) / 100 if d.get('f170') else 0
            }
        return None
    except Exception as e:
        print(f"获取股票信息失败: {e}")
        return None

def get_stock_list():
    """获取A股列表"""
    return get_default_stock_list()

# 测试
if __name__ == '__main__':
    print("=== 测试获取真实数据 ===")
    
    print("\n1. 测试贵州茅台 (600519):")
    df = fetch_stock_data('600519', '20240101', '20240301')
    if not df.empty:
        print(f"   获取到 {len(df)} 条数据")
        print(f"   日期范围: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}")
        print(f"   最新收盘价: {df['close'].iloc[-1]}")
    else:
        print("   获取失败")
    
    print("\n2. 测试中芯国际 (688981):")
    df = fetch_stock_data('688981', '20240101', '20240301')
    if not df.empty:
        print(f"   获取到 {len(df)} 条数据")
        print(f"   最新收盘价: {df['close'].iloc[-1]}")
    else:
        print("   获取失败")
    
    print("\n3. 测试搜索功能:")
    result = search_stock('茅台')
    print(result.head())
