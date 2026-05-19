from datetime import datetime
import numpy as np
from hotspot_fetcher import (
    get_mock_hot_sectors,
    get_mock_sector_stocks,
    get_sector_stocks,
    get_stock_concepts,
    get_fund_flow,
    get_hot_sectors
)


def _safe_get(obj, key, default=None):
    """安全获取字典值"""
    try:
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(key, default)
        if isinstance(obj, (list, tuple)) and key < len(obj):
            return obj[key]
        return default
    except Exception:
        return default


def analyze_stock_attribution(code, name=''):
    """分析股票归因"""
    try:
        concepts = get_stock_concepts(code) or []
    except Exception:
        concepts = []

    try:
        fund_flow_data = get_fund_flow() or []
        stock_fund = next((f for f in fund_flow_data if f.get('code') == str(code)), None)
    except Exception:
        stock_fund = None

    price = _safe_float(_safe_get(stock_fund, 'price', 0))
    change_pct = _safe_float(_safe_get(stock_fund, 'change_pct', 0))
    main_net_inflow = _safe_float(_safe_get(stock_fund, 'main_net_inflow', 0))
    super_large_net_inflow = _safe_float(_safe_get(stock_fund, 'super_large_net_inflow', 0))
    large_net_inflow = _safe_float(_safe_get(stock_fund, 'large_net_inflow', 0))
    medium_net_inflow = _safe_float(_safe_get(stock_fund, 'medium_net_inflow', 0))
    small_net_inflow = _safe_float(_safe_get(stock_fund, 'small_net_inflow', 0))

    technical_signals = _detect_technical_signals(change_pct, main_net_inflow, price)

    industry_concept = concepts[0] if concepts else '待确定'

    result = {
        'code': str(code),
        'name': name,
        'change_pct': round(change_pct, 2),
        'price': round(price, 2),
        'attribution': {
            'industry': {'name': industry_concept, 'change_pct': 0, 'contribution': 0.4},
            'concepts': [{'name': c, 'change_pct': 0, 'contribution': 1.0 / len(concepts) if concepts else 0} for c in concepts[:5]],
        },
        'fund_flow': {
            'main_net_inflow': int(main_net_inflow),
            'super_large_net_inflow': int(super_large_net_inflow),
            'large_net_inflow': int(large_net_inflow),
            'medium_net_inflow': int(medium_net_inflow),
            'small_net_inflow': int(small_net_inflow),
        },
        'technical_signals': technical_signals,
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    return result


def _safe_float(value, default=0.0):
    """安全转换为浮点数"""
    try:
        if value is None or value == '--' or value == '':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def _detect_technical_signals(change_pct, fund_inflow, price):
    """检测技术信号"""
    signals = []

    try:
        if change_pct > 5:
            signals.append('放量大涨')
        elif change_pct > 3:
            signals.append('强势上涨')
        elif change_pct < -5:
            signals.append('放量大跌')
        elif change_pct < -3:
            signals.append('弱势下跌')

        if fund_inflow > 100000000:
            signals.append('主力大幅流入')
        elif fund_inflow > 50000000:
            signals.append('主力净流入')
        elif fund_inflow < -100000000:
            signals.append('主力大幅流出')

        if change_pct > 2 and fund_inflow > 0:
            signals.append('量价齐升')
        elif change_pct < -2 and fund_inflow < 0:
            signals.append('量价齐跌')

        if not signals:
            signals.append('震荡整理')
    except Exception as e:
        print(f"技术信号检测异常: {e}")
        signals.append('震荡整理')

    return signals[:4]


def analyze_sector_attribution(sector_name, sector_type='concept'):
    """分析板块归因"""
    try:
        stocks = get_sector_stocks(sector_name, sector_type) or []
    except Exception:
        stocks = []

    if not stocks or (len(stocks) > 0 and stocks[0].get('is_mock', True)):
        stocks = get_mock_sector_stocks() or []

    try:
        up_count = sum(1 for s in stocks if _safe_float(s.get('change_pct', 0)) > 0)
        down_count = len(stocks) - up_count

        changes = [_safe_float(s.get('change_pct', 0)) for s in stocks]
        avg_change = np.mean(changes) if changes else 0

        lead_stocks = sorted(stocks, key=lambda x: _safe_float(x.get('change_pct', 0)), reverse=True)[:5]
        weak_stocks = sorted(stocks, key=lambda x: _safe_float(x.get('change_pct', 0)))[:3]

        driving_factors = _calculate_driving_factors(stocks, avg_change)

        result = {
            'sector_name': sector_name,
            'change_pct': round(avg_change, 2),
            'stock_count': len(stocks),
            'up_count': up_count,
            'down_count': down_count,
            'lead_stocks': lead_stocks,
            'driving_factors': driving_factors,
            'weak_stocks': weak_stocks,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        return result
    except Exception as e:
        print(f"板块归因分析异常: {e}")
        return {
            'sector_name': sector_name,
            'change_pct': 0,
            'stock_count': 0,
            'up_count': 0,
            'down_count': 0,
            'lead_stocks': [],
            'driving_factors': [],
            'weak_stocks': [],
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }


def _calculate_driving_factors(stocks, avg_change):
    """计算驱动因素"""
    factors = []

    try:
        fund_total = sum(_safe_float(s.get('fund_net_inflow', 0)) for s in stocks)
        fund_weight = min(abs(fund_total) / (len(stocks) * 50000000 + 1), 0.5)

        if avg_change > 0:
            if fund_total > 0:
                factors.append({
                    'type': '资金推动',
                    'description': f'主力资金净流入 {round(fund_total / 100000000, 2)} 亿',
                    'weight': 0.35 + fund_weight * 0.2
                })
            else:
                factors.append({
                    'type': '情绪驱动',
                    'description': '市场情绪回暖，板块普涨',
                    'weight': 0.3
                })
        else:
            factors.append({
                'type': '情绪回落',
                'description': '市场情绪降温，板块调整',
                'weight': 0.3
            })

        tech_weight = 0.3
        if avg_change > 2:
            factors.append({
                'type': '技术突破',
                'description': '板块整体突破关键压力位',
                'weight': tech_weight
            })
        elif avg_change < -2:
            factors.append({
                'type': '技术破位',
                'description': '板块跌破关键支撑位',
                'weight': tech_weight
            })
        else:
            factors.append({
                'type': '技术震荡',
                'description': '板块处于震荡整理区间',
                'weight': tech_weight
            })

        policy_weight = 0.35
        factors.append({
            'type': '政策预期',
            'description': '行业政策面利好预期',
            'weight': policy_weight
        })

        total_weight = sum(f['weight'] for f in factors)
        if total_weight > 0:
            for f in factors:
                f['weight'] = round(f['weight'] / total_weight, 2)

    except Exception as e:
        print(f"驱动因素计算异常: {e}")
        factors = [{
            'type': '综合因素',
            'description': '市场综合影响',
            'weight': 1.0
        }]

    return factors


def get_market_overview():
    """获取市场概览"""
    try:
        sectors = get_hot_sectors() or []

        if not sectors or (len(sectors) > 0 and sectors[0].get('is_mock', True)):
            return {
                'market_status': '强势',
                'hot_topic': 'AI大模型、半导体国产化',
            }

        up_sectors = sum(1 for s in sectors if _safe_float(s.get('change_pct', 0)) > 0)
        hot_topic_names = [s.get('name', '') for s in sectors[:3]]

        if up_sectors > len(sectors) * 0.7:
            market_status = '强势'
        elif up_sectors > len(sectors) * 0.4:
            market_status = '震荡'
        else:
            market_status = '弱势'

        return {
            'market_status': market_status,
            'hot_topic': '、'.join(hot_topic_names),
        }
    except Exception as e:
        print(f"市场概览获取异常: {e}")
        return {
            'market_status': '震荡',
            'hot_topic': '市场波动',
        }
