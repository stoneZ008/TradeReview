from datetime import datetime
import numpy as np
from hotspot_fetcher import (
    get_mock_sector_stocks,
    get_sector_stocks,
    get_stock_concepts,
    get_industry_sectors,
    get_market_metrics,
    get_mock_market_metrics
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

    price = 0.0
    change_pct = 0.0
    main_net_inflow = 0.0

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


def analyze_sector_attribution(sector_name, sector_type='industry'):
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


def _evaluate_bull_market(metrics):
    """基于市场指标进行牛市多因子判定"""
    reasons = []
    score = 0

    sh = (metrics or {}).get('sh_index') or {}
    hs = (metrics or {}).get('hs300') or {}
    up_ratio = _safe_float((metrics or {}).get('up_ratio', 0))

    sh_close = _safe_float(sh.get('close'))
    sh_ma200 = _safe_float(sh.get('ma200'))
    if sh_close and sh_ma200:
        hit = sh_close > sh_ma200
        if hit:
            score += 25
        reasons.append({
            'label': '上证指数 > 200日均线',
            'hit': bool(hit),
            'detail': f"{sh_close:.2f} vs {sh_ma200:.2f}",
            'weight': 25
        })

    if 'ma200_slope_up' in sh:
        hit = bool(sh.get('ma200_slope_up'))
        if hit:
            score += 15
        reasons.append({
            'label': '上证200日均线趋势向上',
            'hit': hit,
            'detail': '近 20 日均线抬升' if hit else '近 20 日均线走平或下行',
            'weight': 15
        })

    drawdown = sh.get('drawdown_from_high')
    if drawdown is not None:
        d = _safe_float(drawdown)
        hit = d < 0.15
        if hit:
            score += 20
        reasons.append({
            'label': '距 52 周高点回撤 < 15%',
            'hit': hit,
            'detail': f"当前回撤 {d * 100:.1f}%",
            'weight': 20
        })

    ret_60d = sh.get('ret_60d')
    if ret_60d is not None:
        r = _safe_float(ret_60d)
        hit = r > 0.10
        if hit:
            score += 15
        reasons.append({
            'label': '上证近 60 日涨幅 > 10%',
            'hit': hit,
            'detail': f"{r * 100:+.1f}%",
            'weight': 15
        })

    hs_close = _safe_float(hs.get('close'))
    hs_ma200 = _safe_float(hs.get('ma200'))
    if hs_close and hs_ma200:
        hit = hs_close > hs_ma200
        if hit:
            score += 15
        reasons.append({
            'label': '沪深300 > 200日均线',
            'hit': bool(hit),
            'detail': f"{hs_close:.2f} vs {hs_ma200:.2f}",
            'weight': 15
        })

    if up_ratio > 0:
        hit = up_ratio > 0.6
        if hit:
            score += 10
        reasons.append({
            'label': '全市场上涨家数占比 > 60%',
            'hit': hit,
            'detail': f"{up_ratio * 100:.1f}%",
            'weight': 10
        })

    is_bull = score >= 60
    hit_labels = [r['label'] for r in reasons if r['hit']][:3]
    if is_bull:
        if hit_labels:
            summary = '满足 ' + '、'.join(hit_labels) + ' 等条件，符合牛市特征'
        else:
            summary = '多项指标向好，符合牛市特征'
    else:
        miss_labels = [r['label'] for r in reasons if not r['hit']][:3]
        if miss_labels:
            summary = '未达 ' + '、'.join(miss_labels) + '，暂不符合牛市标准'
        else:
            summary = '当前指标尚不支持牛市判定'

    return {
        'is_bull_market': is_bull,
        'bull_market_score': score,
        'bull_market_reasons': reasons,
        'bull_market_summary': summary,
    }


def get_market_overview():
    """获取市场概览"""
    try:
        sectors = get_industry_sectors() or []

        try:
            metrics = get_market_metrics() or {}
        except Exception as e:
            print(f"市场指标获取异常: {e}")
            metrics = get_mock_market_metrics()

        if not sectors or (len(sectors) > 0 and sectors[0].get('is_mock', True)):
            mock_metrics = metrics if metrics else get_mock_market_metrics()
            bull = _evaluate_bull_market(mock_metrics)
            return {
                'market_status': '强势',
                'hot_topic': '银行、证券、半导体',
                'total_turnover': mock_metrics.get('total_turnover_yi', 0),
                'total_turnover_text': mock_metrics.get('total_turnover_text', '0亿'),
                **bull,
            }

        up_sectors = sum(1 for s in sectors if _safe_float(s.get('change_pct', 0)) > 0)
        hot_topic_names = [s.get('name', '') for s in sectors[:3]]

        if up_sectors > len(sectors) * 0.7:
            market_status = '强势'
        elif up_sectors > len(sectors) * 0.4:
            market_status = '震荡'
        else:
            market_status = '弱势'

        bull = _evaluate_bull_market(metrics)

        return {
            'market_status': market_status,
            'hot_topic': '、'.join(hot_topic_names),
            'total_turnover': metrics.get('total_turnover_yi', 0),
            'total_turnover_text': metrics.get('total_turnover_text', '0亿'),
            **bull,
        }
    except Exception as e:
        print(f"市场概览获取异常: {e}")
        mock_metrics = get_mock_market_metrics()
        bull = _evaluate_bull_market(mock_metrics)
        return {
            'market_status': '震荡',
            'hot_topic': '市场波动',
            'total_turnover': mock_metrics.get('total_turnover_yi', 0),
            'total_turnover_text': mock_metrics.get('total_turnover_text', '0亿'),
            **bull,
        }

