import json
import os

WATCHLIST_FILE = 'watchlist.json'

def load_watchlist():
    """从文件加载自选股"""
    if not os.path.exists(WATCHLIST_FILE):
        # 默认自选股
        default_watchlist = [
            {'code': '600519', 'name': '贵州茅台'},
            {'code': '000858', 'name': '五粮液'},
            {'code': '000001', 'name': '平安银行'}
        ]
        save_watchlist(default_watchlist)
        return default_watchlist
    
    try:
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载自选股失败: {e}")
        return []

def save_watchlist(watchlist):
    """保存自选股到文件"""
    try:
        with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(watchlist, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存自选股失败: {e}")
        return False

def add_to_watchlist(stock):
    """添加股票到自选股"""
    watchlist = load_watchlist()
    
    # 检查是否已存在
    for item in watchlist:
        if item['code'] == stock['code']:
            return False, '该股票已在自选股中'
    
    watchlist.append(stock)
    save_watchlist(watchlist)
    return True, '添加成功'

def remove_from_watchlist(code):
    """从自选股删除股票"""
    watchlist = load_watchlist()
    original_length = len(watchlist)
    
    watchlist = [item for item in watchlist if item['code'] != code]
    
    if len(watchlist) < original_length:
        save_watchlist(watchlist)
        return True, '删除成功'
    else:
        return False, '股票不在自选股中'
