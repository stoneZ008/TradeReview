import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
import re


def is_us_stock(symbol):
    """判断是否为美股代码（字母开头）"""
    return bool(re.match(r'^[A-Za-z]', symbol.strip().upper()))


def get_market_code(symbol):
    # 美股：105=纳斯达克, 106=纽交所
    if is_us_stock(symbol):
        return ['105.' + symbol, '106.' + symbol]
    # A股
    if symbol.startswith('688') or symbol.startswith('6'):
        return ['1.' + symbol]
    elif symbol.startswith('0') or symbol.startswith('3'):
        return ['0.' + symbol]
    elif symbol.startswith('4') or symbol.startswith('8'):
        return ['0.' + symbol]
    else:
        return ['0.' + symbol]


def _get_sina_prefix(symbol):
    if symbol.startswith('688') or symbol.startswith('6'):
        return 'sh' + symbol
    elif symbol.startswith('0') or symbol.startswith('3'):
        return 'sz' + symbol
    elif symbol.startswith('4') or symbol.startswith('8'):
        return 'sz' + symbol
    else:
        return 'sz' + symbol


def _fetch_eastmoney(symbol, start_date, end_date, adjust):
    secid_list = get_market_code(symbol)
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    
    for secid in secid_list:
        params = {
            'secid': secid,
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101',
            'fqt': '1' if adjust == 'qfq' else '0',
            'beg': start_date,
            'end': end_date,
            'lmt': '1000',
            'ut': 'fa5fd1943c7b386f172d6893dbfba10b'
        }
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
    
    return pd.DataFrame()


def _fetch_sina(symbol, start_date, end_date):
    prefix = _get_sina_prefix(symbol)
    url = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
    headers = {'User-Agent': 'Mozilla/5.0'}

    start_dt = datetime.strptime(start_date, '%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d')
    days_diff = (end_dt - start_dt).days
    datalen = min(max(days_diff, 250), 1500)

    r = requests.get(url, params={'symbol': prefix, 'scale': '240', 'ma': 'no', 'datalen': str(datalen)}, headers=headers, timeout=15)
    items = json.loads(r.text)
    if not items:
        return pd.DataFrame()

    records = []
    for item in items:
        records.append({
            'date': pd.to_datetime(item['day']),
            'open': float(item['open']),
            'close': float(item['close']),
            'high': float(item['high']),
            'low': float(item['low']),
            'volume': float(item['volume']),
        })
    df = pd.DataFrame(records)
    df = df.set_index('date')
    df = df.sort_index()
    df = df[df.index >= start_dt]
    df = df[df.index <= end_dt]
    return df


def _fetch_yfinance(symbol, start_date, end_date):
    """用 yfinance 获取美股数据"""
    try:
        import yfinance as yf
        # YYYYMMDD -> YYYY-MM-DD
        s = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        e = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=s, end=e, auto_adjust=False)
        if hist.empty:
            return pd.DataFrame()
        hist = hist.reset_index()
        hist.rename(columns={'Date': 'date', 'Open': 'open', 'High': 'high', 
                             'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
        hist['date'] = pd.to_datetime(hist['date'])
        hist = hist.set_index('date')
        hist['amount'] = hist['close'] * hist['volume'] / 1e6  # 估算成交额
        return hist.sort_index()
    except Exception as e:
        print(f"yfinance获取失败: {e}")
        return pd.DataFrame()


def fetch_stock_data(symbol, start_date=None, end_date=None, adjust="qfq"):
    symbol = symbol.strip().upper()
    if symbol.startswith(('SH', 'SZ')):
        symbol = symbol[2:]

    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    
    # 美股优先用 yfinance（东方财富美股接口不稳定）
    if is_us_stock(symbol):
        try:
            df = _fetch_yfinance(symbol, start_date, end_date)
            if not df.empty:
                return df
            print("yfinance返回空数据，尝试东方财富")
        except Exception as e:
            print(f"yfinance异常: {e}，尝试东方财富")
    
    # 东方财富接口：A 股主力，美股备用
    try:
        df = _fetch_eastmoney(symbol, start_date, end_date, adjust)
        if not df.empty:
            return df
        print("东方财富返回空数据")
    except requests.exceptions.RequestException as e:
        print(f"东方财富网络异常: {e}")
    except Exception as e:
        print(f"东方财富获取失败: {e}")
    
    # A股回退到新浪财经
    if not is_us_stock(symbol):
        try:
            print("回退到新浪财经")
            df = _fetch_sina(symbol, start_date, end_date)
            if df.empty:
                raise requests.exceptions.RequestException("新浪财经也返回空数据")
            return df
        except Exception as e:
            print(f"新浪财经获取失败: {e}")
    
    # 最终友好提示
    if is_us_stock(symbol):
        raise requests.exceptions.RequestException(
            f"获取美股 {symbol} 数据失败（可能是API限流，稍后重试）。代码示例：AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA"
        )
    
    raise requests.exceptions.RequestException(f"获取 {symbol} 数据失败")


def search_stock(keyword):
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
                if market in [1, 0] and (code.startswith('6') or code.startswith('0') or code.startswith('3') or code.startswith('688')):
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


def get_default_stock_list(include_us=False):
    stocks = [
        {'代码': '600519', '名称': '贵州茅台', '市场': '沪市'},
        {'代码': '601318', '名称': '中国平安', '市场': '沪市'},
        {'代码': '600036', '名称': '招商银行', '市场': '沪市'},
        {'代码': '601398', '名称': '工商银行', '市场': '沪市'},
        {'代码': '000001', '名称': '平安银行', '市场': '深市'},
        {'代码': '000858', '名称': '五粮液', '市场': '深市'},
        {'代码': '000333', '名称': '美的集团', '市场': '深市'},
        {'代码': '002594', '名称': '比亚迪', '市场': '深市'},
        {'代码': '688981', '名称': '中芯国际', '市场': '沪市'},
        {'代码': '688256', '名称': '寒武纪', '市场': '沪市'},
        {'代码': '688111', '名称': '金山办公', '市场': '沪市'},
        {'代码': '688008', '名称': '澜起科技', '市场': '沪市'},
        {'代码': '300750', '名称': '宁德时代', '市场': '深市'},
        {'代码': '300059', '名称': '东方财富', '市场': '深市'},
    ]
    if include_us:
        us_stocks = [
            {'代码': 'AAPL', '名称': '苹果', '市场': '美股'},
            {'代码': 'MSFT', '名称': '微软', '市场': '美股'},
            {'代码': 'GOOGL', '名称': '谷歌', '市场': '美股'},
            {'代码': 'AMZN', '名称': '亚马逊', '市场': '美股'},
            {'代码': 'TSLA', '名称': '特斯拉', '市场': '美股'},
            {'代码': 'META', '名称': 'Meta', '市场': '美股'},
            {'代码': 'NVDA', '名称': '英伟达', '市场': '美股'},
        ]
        stocks = us_stocks + stocks
    return pd.DataFrame(stocks)


def _get_stock_info_sina(symbol):
    prefix = _get_sina_prefix(symbol)
    url = f"https://hq.sinajs.cn/list={prefix}"
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn/'}
    r = requests.get(url, headers=headers, timeout=10)
    r.encoding = 'gbk'
    match_str = f'var hq_str_{prefix}="'
    for line in r.text.strip().split('\n'):
        if match_str in line:
            val = line.split('"')[1]
            if not val:
                return None
            parts = val.split(',')
            return {
                'code': symbol,
                'name': parts[0],
                'open': float(parts[1]) if parts[1] else 0,
                'price': float(parts[3]) if parts[3] else 0,
                'high': float(parts[4]) if parts[4] else 0,
                'low': float(parts[5]) if parts[5] else 0,
                'volume': float(parts[8]) if parts[8] else 0,
                'amount': float(parts[9]) if parts[9] else 0,
            }
    return None


def _get_stock_info_yfinance(symbol):
    """用 yfinance 获取美股基本信息"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info:
            return None
        return {
            'code': symbol,
            'name': info.get('shortName', info.get('longName', symbol)),
            'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
            'high': info.get('dayHigh', 0),
            'low': info.get('dayLow', 0),
            'open': info.get('open', 0),
            'volume': info.get('volume', 0),
            'amount': info.get('marketCap', 0),
            'pct_change': info.get('regularMarketChangePercent', 0)
        }
    except Exception as e:
        print(f"yfinance股票信息失败: {e}")
        return None


def get_stock_info(symbol):
    symbol = symbol.strip().upper()
    if symbol.startswith(('SH', 'SZ')):
        symbol = symbol[2:]
    secid_list = get_market_code(symbol)
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    
    for secid in secid_list:
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
            if data.get('data') and data['data'].get('f58'):
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
        except Exception as e:
            continue
    
    # 美股优先用 yfinance 获取名称
    if is_us_stock(symbol):
        info = _get_stock_info_yfinance(symbol)
        if info:
            return info
    
    # A股回退到新浪
    if not is_us_stock(symbol):
        try:
            return _get_stock_info_sina(symbol)
        except Exception as e:
            print(f"新浪获取股票信息失败: {e}")
    
    # 返回基本信息（至少包含代码作为名称）
    return {
        'code': symbol,
        'name': symbol,
        'price': 0,
        'high': 0,
        'low': 0,
        'open': 0,
        'volume': 0,
        'amount': 0,
        'pct_change': 0
    }


def get_stock_list():
    return get_default_stock_list()


if __name__ == '__main__':
    print("=== 测试获取真实数据 ===")

    print("\n1. 测试贵州茅台 (600519):")
    df = fetch_stock_data('600519', '20250101', '20260425')
    if not df.empty:
        print(f"   获取到 {len(df)} 条数据")
        print(f"   日期范围: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}")
    else:
        print("   获取失败")

    print("\n2. 测试科创板 (688251):")
    df = fetch_stock_data('688251', '20250101', '20260425')
    if not df.empty:
        print(f"   获取到 {len(df)} 条数据")
        print(f"   日期范围: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}")
    else:
        print("   获取失败")

    print("\n3. 测试创业板 (300750):")
    df = fetch_stock_data('300750', '20250101', '20260425')
    if not df.empty:
        print(f"   获取到 {len(df)} 条数据")
    else:
        print("   获取失败")
