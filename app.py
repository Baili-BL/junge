"""
钧哥天下无双 - Flask 后端API
"""

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from stock_analyzer import JunGeAnalyzer
from feishu_bot import push_to_feishu
from datetime import datetime
import json
import os
import threading
import time

# 尝试加载配置
try:
    from config import FEISHU_WEBHOOK_URL, CONFIG
except ImportError:
    FEISHU_WEBHOOK_URL = ""
    CONFIG = {"recommend_count": 3}

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# 全局缓存
cache = {
    'recommendations': None,
    'last_update': None,
    'hot_sectors': None,
    'is_loading': False
}

analyzer = JunGeAnalyzer()


def update_cache():
    """更新缓存数据"""
    global cache
    cache['is_loading'] = True
    try:
        recommendations = analyzer.get_recommendations(top_n=CONFIG.get('recommend_count', 6))
        hot_sectors = analyzer.get_hot_sectors()
        
        cache['recommendations'] = recommendations
        cache['hot_sectors'] = hot_sectors.to_dict('records') if not hot_sectors.empty else []
        cache['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"更新缓存失败: {e}")
    finally:
        cache['is_loading'] = False


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/recommendations')
def get_recommendations():
    """获取股票推荐"""
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    # 如果正在加载，返回加载状态
    if cache['is_loading']:
        return jsonify({
            'success': True,
            'loading': True,
            'message': '正在分析数据，请稍候...'
        })
    
    # 检查是否需要刷新
    need_refresh = (
        force_refresh or 
        cache['recommendations'] is None or
        cache['last_update'] is None
    )
    
    # 检查是否是新的一天
    if cache['last_update']:
        last_date = cache['last_update'].split(' ')[0]
        today_date = datetime.now().strftime('%Y-%m-%d')
        if last_date != today_date:
            need_refresh = True
    
    if need_refresh:
        # 在后台线程更新
        thread = threading.Thread(target=update_cache)
        thread.start()
        thread.join(timeout=120)  # 最多等待120秒
        
        if cache['is_loading']:
            return jsonify({
                'success': True,
                'loading': True,
                'message': '正在分析数据，请稍候...'
            })
    
    # 格式化推荐数据 (确保所有值都是Python原生类型)
    formatted_recommendations = []
    for rec in (cache['recommendations'] or []):
        formatted_recommendations.append({
            'code': str(rec['code']),
            'name': str(rec['name']),
            'sector': str(rec['sector']),
            'sector_rank': int(rec['sector_rank']),
            'score': float(round(rec['score'], 1)),
            'latest_price': float(round(rec['latest_price'], 2)),
            'change_pct': float(round(rec.get('change_pct', 0), 2)),
            'market_cap': float(round(rec.get('market_cap', 0), 1)),  # 市值（亿元）
            'price_trend': {
                'change_5d_pct': float(round(rec['price_trend'].get('change_5d_pct', 0), 2)),
                'above_ma5': bool(rec['price_trend'].get('above_ma5', False)),
                'above_ma10': bool(rec['price_trend'].get('above_ma10', False))
            },
            'volume_change': {
                'volume_change_pct': float(round(rec['volume_change'].get('volume_change_pct', 0), 1)),
                'meets_criteria': bool(rec['volume_change'].get('meets_criteria', False))
            },
            'money_flow': {
                'consecutive_inflow': int(rec['money_flow'].get('consecutive_inflow', 0)),
                'meets_criteria': bool(rec['money_flow'].get('meets_criteria', False))
            },
            'stop_loss': float(round(rec['latest_price'] * 0.95, 2))
        })
    
    return jsonify({
        'success': True,
        'loading': False,
        'data': {
            'recommendations': formatted_recommendations,
            'last_update': cache['last_update'],
            'date': datetime.now().strftime('%Y年%m月%d日'),
            'count': len(formatted_recommendations)
        }
    })


@app.route('/api/hot_sectors')
def get_hot_sectors():
    """获取热门板块"""
    try:
        if cache['hot_sectors'] is None:
            hot_sectors = analyzer.get_hot_sectors()
            cache['hot_sectors'] = hot_sectors.head(20).to_dict('records') if not hot_sectors.empty else []
        
        return jsonify({
            'success': True,
            'data': cache['hot_sectors'][:20]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/stock/<code>')
def get_stock_detail(code):
    """获取单只股票详情"""
    try:
        hist_df = analyzer.get_stock_history(code, days=30)
        money_flow = analyzer.get_money_flow(code)
        
        if hist_df.empty:
            return jsonify({
                'success': False,
                'error': '无法获取股票数据'
            })
        
        # 格式化历史数据
        history = []
        for _, row in hist_df.iterrows():
            history.append({
                'date': str(row.get('日期', '')),
                'open': float(row.get('开盘', 0)),
                'close': float(row.get('收盘', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'volume': float(row.get('成交量', 0)),
                'change_pct': float(row.get('涨跌幅', 0))
            })
        
        return jsonify({
            'success': True,
            'data': {
                'code': code,
                'history': history,
                'money_flow': money_flow.to_dict('records') if not money_flow.empty else []
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/strategy')
def get_strategy():
    """获取策略说明"""
    strategy = {
        'name': '钧哥天下无双低吸策略',
        'core_principle': '题材主线 > 技术突破 > 商业模式 > 财务',
        'key_rules': [
            '题材3天不发酵即切换',
            '低吸为主，避免追高',
            '只做主板股票(60/00开头)',
            '排除ST和退市股'
        ],
        'quantitative_criteria': {
            'money_flow': {
                'title': '资金流入维度（最重要）',
                'rules': [
                    '连续3日净流入',
                    '单日净流入规模达到3%涨幅',
                    '机构净买入占比>25%',
                    '连续3日加仓'
                ]
            },
            'volume': {
                'title': '成交量维度',
                'rules': [
                    '首日放量100%-300%',
                    '次日温和放大20%-50%',
                    '量价齐升'
                ]
            },
            'price': {
                'title': '板块涨幅维度',
                'rules': [
                    '龙头2连板以上',
                    '封单/流通市值≥5%',
                    '中军大盘股放量上涨5%+'
                ]
            }
        },
        'exit_signals': [
            '主力资金大幅流出',
            '成交量萎缩50%以上',
            '涨停梯队瓦解',
            '中军股破5日线',
            '板块指数连续2日收阴'
        ]
    }
    
    return jsonify({
        'success': True,
        'data': strategy
    })


@app.route('/api/status')
def get_status():
    """获取系统状态"""
    return jsonify({
        'success': True,
        'data': {
            'is_loading': cache['is_loading'],
            'last_update': cache['last_update'],
            'has_data': cache['recommendations'] is not None,
            'feishu_configured': bool(FEISHU_WEBHOOK_URL)
        }
    })


@app.route('/api/push_feishu', methods=['POST'])
def push_to_feishu_api():
    """推送到飞书群"""
    # 每次调用时重新读取配置
    try:
        import importlib
        import config
        importlib.reload(config)
        webhook_url = config.FEISHU_WEBHOOK_URL
        print(f"[DEBUG] Loaded webhook URL: {webhook_url[:50] if webhook_url else 'EMPTY'}...")
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        webhook_url = ""
    
    # 也支持前端传入webhook地址
    data = request.get_json() or {}
    if data.get('webhook_url'):
        webhook_url = data['webhook_url']
    
    if not webhook_url:
        print("[ERROR] Webhook URL is empty")
        return jsonify({
            'success': False,
            'error': 'Feishu webhook URL not configured. Please edit config.py'
        })
    
    # 获取推荐数据
    if not cache['recommendations']:
        print("[ERROR] No recommendations in cache")
        return jsonify({
            'success': False,
            'error': 'No recommendations available. Please refresh data first.'
        })
    
    # 格式化数据用于飞书推送
    recommendations = []
    for rec in cache['recommendations']:
        recommendations.append({
            'code': str(rec['code']),
            'name': str(rec['name']),
            'sector': str(rec['sector']),
            'sector_rank': int(rec['sector_rank']),
            'score': float(rec['score']),
            'latest_price': float(rec['latest_price']),
            'change_pct': float(rec.get('change_pct', 0)),
            'price_trend': {
                'change_5d_pct': float(rec['price_trend'].get('change_5d_pct', 0)),
                'above_ma5': bool(rec['price_trend'].get('above_ma5', False)),
                'above_ma10': bool(rec['price_trend'].get('above_ma10', False))
            },
            'volume_change': {
                'volume_change_pct': float(rec['volume_change'].get('volume_change_pct', 0)),
                'meets_criteria': bool(rec['volume_change'].get('meets_criteria', False))
            },
            'money_flow': {
                'consecutive_inflow': int(rec['money_flow'].get('consecutive_inflow', 0)),
                'meets_criteria': bool(rec['money_flow'].get('meets_criteria', False))
            },
            'stop_loss': float(rec['latest_price'] * 0.95)
        })
    
    # 推送到飞书
    print(f"[INFO] Pushing {len(recommendations)} stocks to Feishu...")
    success = push_to_feishu(webhook_url, recommendations)
    print(f"[INFO] Push result: {success}")
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Successfully pushed to Feishu!'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to push to Feishu. Please check webhook URL.'
        })


if __name__ == '__main__':
    # 确保模板和静态文件夹存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("[OK] Starting JunGe Stock Recommendation System...")
    print("[INFO] Visit http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

