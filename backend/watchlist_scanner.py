"""自选股信号扫描模块

每日生成用户自选股的信号快照，记录到 watchlist_signal_snapshots 表中。
同一用户同一天只记录一次（UNIQUE 约束 + INSERT OR IGNORE）。
"""
from datetime import datetime, timedelta
import pandas as pd

from user_db import get_connection
from data_fetcher import fetch_stock_data
from indicators import calculate_all_indicators
from strategies import generate_trading_signals


def _is_a_share(code):
    if not code:
        return False
    code = code.strip()
    if not code.isdigit():
        return False
    return code[0] in ('0', '3', '6')


def _today_str():
    return datetime.now().strftime('%Y%m%d')


def _scan_single_stock(code, name):
    """扫描单只股票，返回快照 dict"""
    end_date = _today_str()
    start_date = (datetime.now() - timedelta(days=200)).strftime('%Y%m%d')

    snapshot = {
        'stock_code': code,
        'stock_name': name,
        'last_trade_date': None,
        'close_price': None,
        'pct_change': None,
        'last_signal': 0,
        'last_signal_date': None,
        'has_signal_today': 0,
        'error': None,
    }

    try:
        df = fetch_stock_data(code, start_date, end_date)
        if df is None or df.empty:
            snapshot['error'] = '无数据'
            return snapshot

        df_ind = calculate_all_indicators(df)
        signals_df = generate_trading_signals(df_ind, {'buy_threshold': 0.08, 'sell_threshold': 0.12})

        merged = df_ind.copy()
        merged['signal'] = signals_df['signal']

        last_idx = merged.index[-1]
        last_row = merged.iloc[-1]

        snapshot['last_trade_date'] = last_idx.strftime('%Y-%m-%d')
        snapshot['close_price'] = round(float(last_row['close']), 2)

        # 涨跌幅：优先取数据源 pct_change，否则自算
        pct = None
        if 'pct_change' in df.columns and pd.notna(df.iloc[-1].get('pct_change')):
            pct = float(df.iloc[-1]['pct_change'])
        elif len(merged) >= 2:
            prev_close = float(merged.iloc[-2]['close'])
            if prev_close > 0:
                pct = (float(last_row['close']) - prev_close) / prev_close * 100
        if pct is not None:
            snapshot['pct_change'] = round(pct, 2)

        # 最近一个非零信号
        nonzero = merged[merged['signal'] != 0]
        if not nonzero.empty:
            last_sig_idx = nonzero.index[-1]
            last_sig_row = nonzero.iloc[-1]
            snapshot['last_signal'] = int(last_sig_row['signal'])
            snapshot['last_signal_date'] = last_sig_idx.strftime('%Y-%m-%d')

        # 最近一个交易日是否有信号
        if int(last_row['signal']) != 0:
            snapshot['has_signal_today'] = 1
    except Exception as e:
        snapshot['error'] = str(e)[:200]

    return snapshot


def _get_user_a_share_watchlist(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT stock_code, stock_name FROM user_watchlists
        WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [(r['stock_code'], r['stock_name']) for r in rows if _is_a_share(r['stock_code'])]


def has_today_snapshot(user_id, date_str=None):
    date_str = date_str or _today_str()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) AS c FROM watchlist_signal_snapshots
        WHERE user_id = ? AND snapshot_date = ?
    ''', (user_id, date_str))
    count = cursor.fetchone()['c']
    conn.close()
    return count > 0


def get_snapshots(user_id, date_str=None):
    date_str = date_str or _today_str()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM watchlist_signal_snapshots
        WHERE user_id = ? AND snapshot_date = ?
        ORDER BY has_signal_today DESC, last_signal_date DESC, stock_code ASC
    ''', (user_id, date_str))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows], date_str


def scan_user_watchlist(user_id, force=False):
    """扫描指定用户的 A 股自选股并入库；同日已扫则跳过（force=True 时强制重扫覆盖）。
    数据库仅保留当日快照，每次扫描前会清理该用户的历史快照。"""
    date_str = _today_str()

    if not force and has_today_snapshot(user_id, date_str):
        # 即便命中缓存，也清理一次非当日历史数据（兜底）
        conn = get_connection()
        conn.execute('DELETE FROM watchlist_signal_snapshots WHERE user_id = ? AND snapshot_date != ?',
                     (user_id, date_str))
        conn.commit()
        conn.close()
        return get_snapshots(user_id, date_str)

    stocks = _get_user_a_share_watchlist(user_id)

    conn = get_connection()
    cursor = conn.cursor()

    # 清理该用户所有非当日的历史快照（仅保留当日数据）
    cursor.execute('DELETE FROM watchlist_signal_snapshots WHERE user_id = ? AND snapshot_date != ?',
                   (user_id, date_str))

    if force:
        cursor.execute('DELETE FROM watchlist_signal_snapshots WHERE user_id = ? AND snapshot_date = ?',
                       (user_id, date_str))

    for code, name in stocks:
        snap = _scan_single_stock(code, name)
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO watchlist_signal_snapshots
                (user_id, snapshot_date, stock_code, stock_name, last_trade_date,
                 close_price, pct_change, last_signal, last_signal_date, has_signal_today, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, date_str, snap['stock_code'], snap['stock_name'],
                snap['last_trade_date'], snap['close_price'], snap['pct_change'],
                snap['last_signal'], snap['last_signal_date'], snap['has_signal_today'],
                snap['error']
            ))
        except Exception as e:
            print(f"写入快照失败 user={user_id} code={code}: {e}")

    conn.commit()
    conn.close()

    return get_snapshots(user_id, date_str)


def scan_all_users():
    """扫描所有有自选股的用户（供定时任务调用）"""
    print(f"[Scheduler] 开始执行每日自选股扫描 {datetime.now()}")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT user_id FROM user_watchlists')
    user_ids = [r['user_id'] for r in cursor.fetchall()]
    conn.close()

    total = len(user_ids)
    for i, uid in enumerate(user_ids, 1):
        try:
            scan_user_watchlist(uid, force=False)
            print(f"[Scheduler] ({i}/{total}) user={uid} 扫描完成")
        except Exception as e:
            print(f"[Scheduler] user={uid} 扫描失败: {e}")
    print(f"[Scheduler] 每日自选股扫描结束，共 {total} 个用户")
