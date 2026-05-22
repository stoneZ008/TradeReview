import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
import re
import time
import threading


_DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

_CACHE = {}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL = 300  # 5 分钟


def _cache_get(key):
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if not item:
            return None
        ts, df = item
        if time.time() - ts > _CACHE_TTL:
            _CACHE.pop(key, None)
            return None
        return df.copy()


def _cache_set(key, df):
    with _CACHE_LOCK:
        _CACHE[key] = (time.time(), df.copy())


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


def _fetch_tencent_a(symbol, start_date, end_date):
    """腾讯A股日K线接口（盘中含当日数据、支持前复权）"""
    try:
        if symbol.startswith('688') or symbol.startswith('6'):
            prefix = 'sh' + symbol
        elif symbol.startswith('0') or symbol.startswith('3'):
            prefix = 'sz' + symbol
        elif symbol.startswith('4') or symbol.startswith('8'):
            prefix = 'sz' + symbol
        else:
            prefix = 'sz' + symbol
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        days = (end_dt - start_dt).days
        count = min(max(days + 60, 320), 1500)
        param = f"{prefix},day,,,{count},qfq"
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {'param': param}
        headers = {**_DEFAULT_HEADERS, 'Referer': 'https://gu.qq.com/'}
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()
        if data.get('code') != 0:
            return pd.DataFrame()
        inner = data.get('data', {}).get(prefix)
        if not inner:
            for key in data.get('data', {}):
                inner = data['data'][key]
                break
        if not inner or not isinstance(inner, dict):
            return pd.DataFrame()
        kline_data = inner.get('qfqday') or inner.get('day')
        if not kline_data:
            return pd.DataFrame()
        records = []
        for item in kline_data:
            if len(item) >= 6:
                try:
                    records.append({
                        'date': pd.to_datetime(item[0]),
                        'open': float(item[1]),
                        'close': float(item[2]),
                        'high': float(item[3]),
                        'low': float(item[4]),
                        'volume': float(item[5]),
                    })
                except (ValueError, TypeError):
                    continue
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df = df.set_index('date')
        df = df.sort_index()
        df = df[(df.index >= start_dt) & (df.index <= end_dt)]
        if df.empty:
            return pd.DataFrame()
        df['amount'] = df['close'] * df['volume'] / 1e6
        return df
    except Exception as e:
        print(f"腾讯A股获取失败: {e}")
        return pd.DataFrame()


def _is_a_trading_time():
    """是否处在 A 股交易时段（含午休）"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.time()
    from datetime import time as dtime
    return (dtime(9, 25) <= t <= dtime(11, 35)) or (dtime(12, 55) <= t <= dtime(15, 5))


def _append_intraday_kline_a(symbol, df):
    """A 股盘中：若 df 末尾不是今日，从新浪实时行情拼一根当日 K 线"""
    if not _is_a_trading_time() or df.empty:
        return df
    today = pd.Timestamp(datetime.now().date())
    if df.index[-1].date() >= today.date():
        return df
    try:
        info = _get_stock_info_sina(symbol)
        if not info or not info.get('price') or info['price'] == 0:
            return df
        new_row = pd.DataFrame([{
            'open': info.get('open', info['price']),
            'high': info.get('high', info['price']),
            'low': info.get('low', info['price']),
            'close': info['price'],
            'volume': info.get('volume', 0),
            'amount': info.get('amount', 0) / 1e6 if info.get('amount', 0) > 1e8 else info.get('amount', 0),
        }], index=[today])
        df = pd.concat([df, new_row])
    except Exception as e:
        print(f"拼接当日K线失败: {e}")
    return df


def _fetch_sina_us(symbol, start_date, end_date):
    """雪球美股日K线接口（国内稳定、免 API Key）"""
    try:
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        begin_ts = int(end_dt.timestamp() * 1000)
        days = (end_dt - start_dt).days
        count = min(max(days + 60, 320), 1023)
        session = requests.Session()
        session.headers.update({**_DEFAULT_HEADERS, 'Referer': 'https://xueqiu.com/'})
        session.get('https://xueqiu.com/', headers=_DEFAULT_HEADERS, timeout=10)
        url = 'https://stock.xueqiu.com/v5/stock/chart/kline.json'
        params = {
            'symbol': symbol,
            'begin': begin_ts,
            'period': 'day',
            'type': 'before',
            'count': -count,
            'indicator': 'kline',
        }
        r = session.get(url, params=params, timeout=15)
        data = r.json()
        items = data.get('data', {}).get('item', [])
        columns = data.get('data', {}).get('column', [])
        if not items or not columns:
            return pd.DataFrame()
        col_map = {'timestamp': 'date', 'open': 'open', 'high': 'high',
                    'low': 'low', 'close': 'close', 'volume': 'volume', 'amount': 'amount'}
        col_indices = {}
        for i, c in enumerate(columns):
            if c in col_map:
                col_indices[col_map[c]] = i
        if 'date' not in col_indices:
            return pd.DataFrame()
        records = []
        for row in items:
            try:
                rec = {}
                for name, idx in col_indices.items():
                    val = row[idx] if idx < len(row) else None
                    if val is None:
                        continue
                    if name == 'date':
                        rec['date'] = pd.to_datetime(val, unit='ms')
                    else:
                        rec[name] = float(val)
                if 'date' in rec:
                    records.append(rec)
            except (ValueError, TypeError, IndexError):
                continue
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df = df.set_index('date')
        df = df.sort_index()
        df = df[(df.index >= start_dt) & (df.index <= end_dt)]
        if 'amount' not in df.columns:
            df['amount'] = df['close'] * df['volume'] / 1e6
        else:
            df['amount'] = df['amount'] / 1e6
        return df
    except Exception as e:
        print(f"雪球美股获取失败: {e}")
        return pd.DataFrame()


def _fetch_tencent_us(symbol, start_date, end_date):
    """腾讯美股日K线接口（国内稳定、支持前复权）"""
    try:
        sym = symbol.upper().replace('.', '_')
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        days = (end_dt - start_dt).days
        count = min(max(days + 60, 320), 1023)
        suffixes = ['.OQ', '.N', '.OB']
        for suffix in suffixes:
            full_code = f"us{sym}{suffix}"
            param = f"{full_code},day,,,{count},qfq"
            url = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            params = {'param': param}
            headers = {**_DEFAULT_HEADERS, 'Referer': 'https://gu.qq.com/'}
            try:
                r = requests.get(url, params=params, headers=headers, timeout=15)
                data = r.json()
            except Exception:
                continue
            if data.get('code') != 0:
                continue
            inner = data.get('data', {}).get(full_code)
            if not inner:
                continue
            kline_data = inner.get('qfqday') or inner.get('day')
            if not kline_data:
                continue
            records = []
            for item in kline_data:
                if len(item) >= 6:
                    try:
                        records.append({
                            'date': pd.to_datetime(item[0]),
                            'open': float(item[1]),
                            'close': float(item[2]),
                            'high': float(item[3]),
                            'low': float(item[4]),
                            'volume': float(item[5]),
                        })
                    except (ValueError, TypeError):
                        continue
            if not records:
                continue
            df = pd.DataFrame(records)
            df = df.set_index('date')
            df = df.sort_index()
            df = df[(df.index >= start_dt) & (df.index <= end_dt)]
            if df.empty:
                continue
            df['amount'] = df['close'] * df['volume'] / 1e6
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"腾讯美股获取失败: {e}")
        return pd.DataFrame()


def _fetch_eastmoney_us(symbol, start_date, end_date, adjust):
    """东方财富美股K线（扩展 secid 候选）"""
    secid_candidates = [
        f'105.{symbol}', f'106.{symbol}', f'100.{symbol}',
        f'107.{symbol}', f'153.{symbol}',
    ]
    ut_candidates = [
        'fa5fd1943c7b386f172d6893dbfba10b',
        '7eea3edcaed734bea9cbfc24409ed989',
    ]
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    headers = {**_DEFAULT_HEADERS, 'Referer': 'https://quote.eastmoney.com/'}
    for secid in secid_candidates:
        for ut in ut_candidates:
            params = {
                'secid': secid,
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': '101',
                'fqt': '1' if adjust == 'qfq' else '0',
                'beg': start_date,
                'end': end_date,
                'lmt': '1000',
                'ut': ut,
            }
            try:
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
                            'turnover': float(parts[10]),
                        })
                    df = pd.DataFrame(records)
                    df = df.set_index('date')
                    df = df.sort_index()
                    return df
            except Exception:
                continue
    return pd.DataFrame()


def _fetch_yfinance(symbol, start_date, end_date):
    """用 yfinance 获取美股数据（加重试+退避）"""
    try:
        import yfinance as yf
        s = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        e = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        for attempt in range(3):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=s, end=e, auto_adjust=False)
                if hist.empty:
                    if attempt < 2:
                        time.sleep(5 * (attempt + 1))
                        continue
                    return pd.DataFrame()
                hist = hist.reset_index()
                hist.rename(columns={'Date': 'date', 'Open': 'open', 'High': 'high',
                                     'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
                hist['date'] = pd.to_datetime(hist['date'])
                hist = hist.set_index('date')
                hist['amount'] = hist['close'] * hist['volume'] / 1e6
                return hist.sort_index()
            except Exception as ex:
                err_msg = str(ex).lower()
                if '429' in err_msg or 'rate' in err_msg or 'too many' in err_msg:
                    time.sleep(10 * (attempt + 1))
                    continue
                raise
        return pd.DataFrame()
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

    cache_key = f"kline:{symbol}:{start_date}:{end_date}:{adjust}"
    cached = _cache_get(cache_key)
    if cached is not None and not cached.empty:
        return cached

    # 美股：多源回退链
    if is_us_stock(symbol):
        us_fetchers = [
            ('腾讯美股', lambda: _fetch_tencent_us(symbol, start_date, end_date)),
            ('雪球美股', lambda: _fetch_sina_us(symbol, start_date, end_date)),
            ('东方财富', lambda: _fetch_eastmoney_us(symbol, start_date, end_date, adjust)),
            ('yfinance', lambda: _fetch_yfinance(symbol, start_date, end_date)),
        ]
        last_err = None
        for name, fn in us_fetchers:
            try:
                df = fn()
                if df is not None and not df.empty:
                    print(f"美股 {symbol} 数据源: {name}, 共 {len(df)} 条")
                    _cache_set(cache_key, df)
                    return df
                print(f"{name} 返回空数据")
            except Exception as e:
                last_err = e
                print(f"{name} 异常: {e}")
        raise requests.exceptions.RequestException(
            f"获取美股 {symbol} 数据失败（所有数据源均不可用，可能是API限流，稍后重试）。"
            f"代码示例：AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA"
        )

    # A 股：东方财富 → 腾讯 → 新浪
    a_fetchers = [
        ('东方财富', lambda: _fetch_eastmoney(symbol, start_date, end_date, adjust)),
        ('腾讯', lambda: _fetch_tencent_a(symbol, start_date, end_date)),
        ('新浪', lambda: _fetch_sina(symbol, start_date, end_date)),
    ]
    df = pd.DataFrame()
    used_source = None
    for name, fn in a_fetchers:
        try:
            df = fn()
            if df is not None and not df.empty:
                used_source = name
                print(f"A股 {symbol} 数据源: {name}, 共 {len(df)} 条")
                break
            print(f"{name} 返回空数据")
        except requests.exceptions.RequestException as e:
            print(f"{name} 网络异常: {e}")
        except Exception as e:
            print(f"{name} 获取失败: {e}")

    if df is None or df.empty:
        raise requests.exceptions.RequestException(f"获取 {symbol} 数据失败")

    # 盘中：若末尾不是当日，用新浪实时行情拼一根当日 K 线
    df = _append_intraday_kline_a(symbol, df)

    _cache_set(cache_key, df)
    return df


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


def _get_stock_info_sina_us(symbol):
    """新浪美股实时行情（替代 yfinance.info，更稳定）"""
    try:
        sym = symbol.lower().replace('.', '_')
        url = f"https://hq.sinajs.cn/list=gb_{sym}"
        headers = {**_DEFAULT_HEADERS, 'Referer': 'https://finance.sina.com.cn/'}
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = 'gbk'
        for line in r.text.strip().split('\n'):
            if '="' not in line:
                continue
            val = line.split('"')[1]
            if not val:
                continue
            parts = val.split(',')
            if len(parts) < 8:
                continue
            try:
                price = float(parts[1]) if parts[1] else 0
                pct_change = float(parts[2]) if parts[2] else 0
                open_price = float(parts[5]) if parts[5] else 0
                high = float(parts[6]) if parts[6] else 0
                low = float(parts[7]) if parts[7] else 0
                volume = float(parts[10]) if len(parts) > 10 and parts[10] else 0
                return {
                    'code': symbol,
                    'name': parts[0],
                    'price': price,
                    'high': high,
                    'low': low,
                    'open': open_price,
                    'volume': volume,
                    'amount': 0,
                    'pct_change': pct_change,
                }
            except (ValueError, IndexError):
                continue
        return None
    except Exception as e:
        print(f"新浪美股信息获取失败: {e}")
        return None


def _get_stock_info_tencent_us(symbol):
    """腾讯美股实时行情（备用）"""
    try:
        sym = symbol.upper().replace('.', '_')
        for suffix in ['.OQ', '.N', '.OB']:
            url = f"http://qt.gtimg.cn/q=us{sym}{suffix}"
            headers = {**_DEFAULT_HEADERS, 'Referer': 'https://gu.qq.com/'}
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = 'gbk'
            text = r.text.strip()
            if '="' not in text:
                continue
            val = text.split('"')[1]
            if not val or '~' not in val:
                continue
            parts = val.split('~')
            if len(parts) < 35:
                continue
            try:
                return {
                    'code': symbol,
                    'name': parts[1],
                    'price': float(parts[3]) if parts[3] else 0,
                    'high': float(parts[33]) if parts[33] else 0,
                    'low': float(parts[34]) if parts[34] else 0,
                    'open': float(parts[5]) if parts[5] else 0,
                    'volume': float(parts[6]) if parts[6] else 0,
                    'amount': float(parts[37]) if len(parts) > 37 and parts[37] else 0,
                    'pct_change': float(parts[32]) if parts[32] else 0,
                }
            except (ValueError, IndexError):
                continue
        return None
    except Exception as e:
        print(f"腾讯美股信息获取失败: {e}")
        return None


def _get_stock_info_yfinance(symbol):
    """用 yfinance 获取美股基本信息（仅作兜底，易触发限流）"""
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

    # 美股：优先用新浪/腾讯实时行情（避免 yfinance.info 限流）
    if is_us_stock(symbol):
        for fn in [_get_stock_info_sina_us, _get_stock_info_tencent_us]:
            try:
                info = fn(symbol)
                if info and info.get('name'):
                    return info
            except Exception as e:
                print(f"{fn.__name__} 失败: {e}")
        # 兜底用 yfinance
        try:
            info = _get_stock_info_yfinance(symbol)
            if info:
                return info
        except Exception as e:
            print(f"yfinance 兜底失败: {e}")
        return {
            'code': symbol, 'name': symbol, 'price': 0, 'high': 0, 'low': 0,
            'open': 0, 'volume': 0, 'amount': 0, 'pct_change': 0,
        }

    # A 股：东方财富 → 新浪
    secid_list = get_market_code(symbol)
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    for secid in secid_list:
        params = {
            'secid': secid,
            'fields': 'f43,f44,f45,f46,f47,f48,f57,f58,f170',
            'ut': 'fa5fd1943c7b386f172d6893dbfba10b'
        }
        try:
            headers = {**_DEFAULT_HEADERS, 'Referer': 'https://quote.eastmoney.com/'}
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
        except Exception:
            continue

    try:
        return _get_stock_info_sina(symbol)
    except Exception as e:
        print(f"新浪获取股票信息失败: {e}")

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

    print("\n4. 测试美股 AAPL:")
    df = fetch_stock_data('AAPL', '20250101', '20260425')
    if not df.empty:
        print(f"   获取到 {len(df)} 条数据")
        print(f"   日期范围: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}")
        print(f"   最新收盘: {df['close'].iloc[-1]}")
    else:
        print("   获取失败")

    print("\n5. 测试美股 TSLA 信息:")
    info = get_stock_info('TSLA')
    print(f"   {info}")

    print("\n6. 测试 A 股盘中当日数据 (600519, 截至今日):")
    today = datetime.now().strftime('%Y%m%d')
    start = (datetime.now() - timedelta(days=15)).strftime('%Y%m%d')
    df = fetch_stock_data('600519', start, today)
    if not df.empty:
        print(f"   获取到 {len(df)} 条数据")
        for d in df.index[-5:]:
            row = df.loc[d]
            print(f"     {d.strftime('%Y-%m-%d')} O={row['open']} C={row['close']} H={row['high']} L={row['low']}")
    else:
        print("   获取失败")
