"""
飞书群机器人推送模块
参考文档: https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot
"""

import requests
import json
from datetime import datetime
from typing import List, Dict
import sys

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class FeishuBot:
    """飞书群机器人"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_text(self, content: str) -> bool:
        """发送纯文本消息"""
        data = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        return self._send(data)
    
    def send_rich_text(self, title: str, content: List[List[Dict]]) -> bool:
        """发送富文本消息"""
        data = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": content
                    }
                }
            }
        }
        return self._send(data)
    
    def _send(self, data: Dict) -> bool:
        """发送消息到飞书"""
        try:
            headers = {"Content-Type": "application/json; charset=utf-8"}
            
            json_str = json.dumps(data, ensure_ascii=False)
            
            response = requests.post(
                self.webhook_url,
                headers=headers,
                data=json_str.encode('utf-8'),
                timeout=10
            )
            
            result = response.json()
            
            # 飞书返回格式检查
            if result.get("code") == 0 or result.get("StatusCode") == 0 or result.get("msg") == "success":
                print("[OK] Feishu message sent successfully")
                return True
            else:
                print(f"[ERROR] Feishu API error: {result}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Feishu send exception: {e}")
            return False
    
    def send_stock_recommendations(self, recommendations: List[Dict], date_str: str = None) -> bool:
        """发送股票推荐"""
        
        if not recommendations:
            return self.send_text("今日暂无符合条件的推荐股票，建议观望等待明确题材主线。")
        
        if not date_str:
            date_str = datetime.now().strftime("%Y年%m月%d日")
        
        # 构建富文本消息内容
        content = []
        
        # 标题信息
        content.append([
            {"tag": "text", "text": "策略: 题材主线 > 技术突破 > 商业模式 > 财务\n"},
        ])
        content.append([
            {"tag": "text", "text": "纪律: 题材3天不发酵即切换 | 低吸为主\n"},
        ])
        content.append([
            {"tag": "text", "text": "━━━━━━━━━━━━━━━━━━━━\n"},
        ])
        
        # 添加每只股票信息
        for i, stock in enumerate(recommendations, 1):
            change_sign = "+" if stock.get('change_pct', 0) >= 0 else ""
            change_5d = stock.get('price_trend', {}).get('change_5d_pct', 0)
            change_5d_sign = "+" if change_5d >= 0 else ""
            
            # 指标状态
            ma5_status = "[OK]" if stock.get('price_trend', {}).get('above_ma5') else "[X]"
            ma10_status = "[OK]" if stock.get('price_trend', {}).get('above_ma10') else "[X]"
            vol_status = "[OK]" if stock.get('volume_change', {}).get('meets_criteria') else "[X]"
            money_status = "[OK]" if stock.get('money_flow', {}).get('meets_criteria') else "[X]"
            
            stock_text = f"""
【推荐{i}】{stock['name']} ({stock['code']})
综合评分: {stock['score']}分
所属板块: {stock['sector']} 热度#{stock['sector_rank']}
当前价格: {stock['latest_price']}元 ({change_sign}{stock.get('change_pct', 0):.2f}%)
5日涨幅: {change_5d_sign}{change_5d:.2f}%
量能变化: +{stock.get('volume_change', {}).get('volume_change_pct', 0):.1f}%
资金流入: 连续{stock.get('money_flow', {}).get('consecutive_inflow', 0)}天
技术面: 5日线{ma5_status} 10日线{ma10_status} 量能{vol_status} 资金{money_status}
建议止损: {stock.get('stop_loss', stock['latest_price']*0.95):.2f}元 (-5%)
"""
            content.append([
                {"tag": "text", "text": stock_text}
            ])
            
            if i < len(recommendations):
                content.append([
                    {"tag": "text", "text": "────────────────────\n"}
                ])
        
        # 风险提示
        content.append([
            {"tag": "text", "text": "\n[风险提示] 本推荐仅供参考，不构成投资建议。股市有风险，投资需谨慎。"}
        ])
        
        title = f"[钧哥天下无双] {date_str} 股票推荐"
        
        return self.send_rich_text(title, content)


def push_to_feishu(webhook_url: str, recommendations: List[Dict]) -> bool:
    """推送股票推荐到飞书群"""
    if not webhook_url:
        print("[WARN] Feishu webhook URL not configured")
        return False
    
    bot = FeishuBot(webhook_url)
    return bot.send_stock_recommendations(recommendations)


def test_webhook(webhook_url: str) -> bool:
    """测试webhook是否可用"""
    bot = FeishuBot(webhook_url)
    return bot.send_text("[测试] 钧哥天下无双系统测试消息 - 如果你看到这条消息，说明飞书推送配置成功！")


if __name__ == "__main__":
    from config import FEISHU_WEBHOOK_URL
    
    if FEISHU_WEBHOOK_URL:
        print("Testing Feishu webhook...")
        test_webhook(FEISHU_WEBHOOK_URL)
    else:
        print("Please configure FEISHU_WEBHOOK_URL in config.py first")
