"""
钧哥天下无双 - 低吸策略股票分析器
核心量化标准实现
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class JunGeAnalyzer:
    """钧哥天下无双低吸策略分析器"""
    
    def __init__(self):
        self.today = datetime.now().strftime('%Y%m%d')
        self.cache = {}
        
    def get_hot_sectors(self) -> pd.DataFrame:
        """获取当日热门板块"""
        try:
            # 获取板块资金流向
            df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
            return df
        except Exception as e:
            print(f"获取板块数据失败: {e}")
            return pd.DataFrame()
    
    def get_sector_stocks(self, sector_name: str) -> pd.DataFrame:
        """获取板块内股票"""
        try:
            df = ak.stock_board_industry_cons_em(symbol=sector_name)
            return df
        except Exception as e:
            print(f"获取板块{sector_name}股票失败: {e}")
            return pd.DataFrame()
    
    def get_stock_history(self, stock_code: str, days: int = 10) -> pd.DataFrame:
        """获取股票历史数据"""
        try:
            # 处理股票代码格式
            if stock_code.startswith('6'):
                symbol = f"sh{stock_code}"
            else:
                symbol = f"sz{stock_code}"
            
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                    start_date=start_date, end_date=end_date, adjust="qfq")
            return df.tail(days)
        except Exception as e:
            print(f"获取股票{stock_code}历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_money_flow(self, stock_code: str) -> pd.DataFrame:
        """获取个股资金流向"""
        try:
            df = ak.stock_individual_fund_flow(stock=stock_code, market="sh" if stock_code.startswith('6') else "sz")
            return df.head(5)  # 最近5天
        except Exception as e:
            print(f"获取资金流向失败: {e}")
            return pd.DataFrame()
    
    def get_main_board_stocks(self) -> pd.DataFrame:
        """获取主板股票列表（排除创业板、科创板、北交所）"""
        try:
            df = ak.stock_zh_a_spot_em()
            # 主板: 60开头(沪主板) 00开头(深主板)
            df = df[df['代码'].str.match('^(60|00)')]
            # 排除ST股票
            df = df[~df['名称'].str.contains('ST|退')]
            return df
        except Exception as e:
            print(f"获取主板股票失败: {e}")
            return pd.DataFrame()
    
    def get_all_stocks_market_cap(self) -> Dict[str, float]:
        """获取所有股票的总市值（单位：亿元）"""
        if 'market_cap_cache' in self.cache:
            return self.cache['market_cap_cache']
        
        try:
            print("[INFO] Loading market cap data...")
            df = ak.stock_zh_a_spot_em()
            market_cap_dict = {}
            for _, row in df.iterrows():
                code = row.get('代码', '')
                cap = row.get('总市值', 0)
                try:
                    # 转换为亿元
                    market_cap_dict[code] = float(cap) / 100000000 if cap else 0
                except:
                    market_cap_dict[code] = 0
            self.cache['market_cap_cache'] = market_cap_dict
            print(f"[INFO] Loaded market cap for {len(market_cap_dict)} stocks")
            return market_cap_dict
        except Exception as e:
            print(f"[ERROR] Failed to load market cap: {e}")
            return {}
    
    def get_limit_up_stocks(self) -> pd.DataFrame:
        """获取涨停股票"""
        try:
            df = ak.stock_zt_pool_em(date=self.today)
            return df
        except Exception as e:
            print(f"获取涨停数据失败: {e}")
            return pd.DataFrame()
    
    def get_dragon_tiger_list(self) -> pd.DataFrame:
        """获取龙虎榜数据"""
        try:
            df = ak.stock_lhb_detail_em(start_date=self.today, end_date=self.today)
            return df
        except Exception as e:
            print(f"获取龙虎榜失败: {e}")
            return pd.DataFrame()
    
    def calculate_volume_change(self, df: pd.DataFrame) -> Dict:
        """计算成交量变化"""
        if df.empty or len(df) < 6:
            return {'valid': False}
        
        # 最近5日均量
        avg_vol_5 = df['成交量'].iloc[-6:-1].mean()
        today_vol = df['成交量'].iloc[-1]
        
        vol_change = (today_vol / avg_vol_5 - 1) * 100 if avg_vol_5 > 0 else 0
        
        return {
            'valid': True,
            'avg_volume_5d': avg_vol_5,
            'today_volume': today_vol,
            'volume_change_pct': vol_change,
            'meets_criteria': 50 <= vol_change <= 300  # 放大50%-300%
        }
    
    def calculate_price_trend(self, df: pd.DataFrame) -> Dict:
        """计算价格趋势"""
        if df.empty or len(df) < 5:
            return {'valid': False}
        
        # 计算5日涨幅
        price_5d_ago = df['收盘'].iloc[-5]
        today_price = df['收盘'].iloc[-1]
        change_5d = (today_price / price_5d_ago - 1) * 100
        
        # 计算是否站上5日均线
        ma5 = df['收盘'].tail(5).mean()
        above_ma5 = today_price > ma5
        
        # 计算10日均线
        if len(df) >= 10:
            ma10 = df['收盘'].tail(10).mean()
            above_ma10 = today_price > ma10
        else:
            ma10 = None
            above_ma10 = None
        
        return {
            'valid': True,
            'change_5d_pct': change_5d,
            'today_price': today_price,
            'ma5': ma5,
            'ma10': ma10,
            'above_ma5': above_ma5,
            'above_ma10': above_ma10
        }
    
    def check_money_flow_criteria(self, money_flow_df: pd.DataFrame) -> Dict:
        """检查资金流入标准"""
        if money_flow_df.empty or len(money_flow_df) < 3:
            return {'valid': False, 'consecutive_inflow': 0}
        
        # 检查连续净流入天数
        consecutive_inflow = 0
        for i in range(min(3, len(money_flow_df))):
            try:
                # 尝试获取主力净流入数据
                if '主力净流入-净额' in money_flow_df.columns:
                    inflow = money_flow_df.iloc[i]['主力净流入-净额']
                elif '主力净额' in money_flow_df.columns:
                    inflow = money_flow_df.iloc[i]['主力净额']
                else:
                    inflow = 0
                
                if inflow > 0:
                    consecutive_inflow += 1
                else:
                    break
            except:
                break
        
        return {
            'valid': True,
            'consecutive_inflow': consecutive_inflow,
            'meets_criteria': consecutive_inflow >= 2  # 至少连续2日净流入
        }
    
    def score_stock(self, stock_info: Dict) -> float:
        """
        股票综合评分
        权重: 题材主线(35%) > 技术突破(30%) > 商业模式(20%) > 财务(15%)
        """
        score = 0
        
        # 题材主线评分 (35分)
        if stock_info.get('in_hot_sector'):
            score += 20
        if stock_info.get('sector_rank', 100) <= 5:
            score += 15
        
        # 技术突破评分 (30分)
        price_trend = stock_info.get('price_trend', {})
        if price_trend.get('above_ma5'):
            score += 10
        if price_trend.get('above_ma10'):
            score += 10
        if 0 < price_trend.get('change_5d_pct', -100) <= 15:
            score += 10
        
        # 资金流入评分 (20分) - 代替商业模式
        money_flow = stock_info.get('money_flow', {})
        consecutive = money_flow.get('consecutive_inflow', 0)
        score += min(consecutive * 7, 20)
        
        # 成交量评分 (15分)
        volume = stock_info.get('volume_change', {})
        if volume.get('meets_criteria'):
            score += 15
        elif volume.get('volume_change_pct', 0) > 30:
            score += 8
        
        return score
    
    def analyze_single_stock(self, stock_code: str, stock_name: str, 
                            sector_name: str = "", sector_rank: int = 100,
                            market_cap: float = 0) -> Optional[Dict]:
        """分析单只股票"""
        # 只分析主板股票 (60开头或00开头)
        if not (stock_code.startswith('60') or stock_code.startswith('00')):
            return None
        
        # 排除市值超过1000亿的大盘股
        if market_cap > 1000:
            return None
        
        # 获取历史数据
        hist_df = self.get_stock_history(stock_code, days=15)
        if hist_df.empty:
            return None
        
        # 计算各项指标
        volume_change = self.calculate_volume_change(hist_df)
        price_trend = self.calculate_price_trend(hist_df)
        
        # 获取资金流向
        money_flow_df = self.get_money_flow(stock_code)
        money_flow = self.check_money_flow_criteria(money_flow_df)
        
        stock_info = {
            'code': stock_code,
            'name': stock_name,
            'sector': sector_name,
            'sector_rank': sector_rank,
            'in_hot_sector': sector_rank <= 10,
            'volume_change': volume_change,
            'price_trend': price_trend,
            'money_flow': money_flow,
            'latest_price': hist_df['收盘'].iloc[-1] if not hist_df.empty else 0,
            'change_pct': hist_df['涨跌幅'].iloc[-1] if not hist_df.empty and '涨跌幅' in hist_df.columns else 0,
            'market_cap': market_cap  # 市值（亿元）
        }
        
        # 计算综合评分
        stock_info['score'] = self.score_stock(stock_info)
        
        return stock_info
    
    def get_recommendations(self, top_n: int = 3) -> List[Dict]:
        """
        获取推荐股票
        核心逻辑:
        1. 获取热门板块
        2. 筛选主板股票
        3. 应用钧哥量化标准
        4. 返回TOP推荐
        """
        recommendations = []
        
        print("[INFO] Fetching hot sectors...")
        hot_sectors = self.get_hot_sectors()
        
        if hot_sectors.empty:
            print("[ERROR] Failed to get sector data")
            return []
        
        # 预加载所有股票市值数据
        market_cap_dict = self.get_all_stocks_market_cap()
        
        # 获取资金净流入前10的板块
        print("[INFO] Analyzing top sectors...")
        top_sectors = hot_sectors.head(10)
        
        analyzed_stocks = []
        
        for idx, sector in top_sectors.iterrows():
            sector_name = sector.get('名称', sector.get('行业', ''))
            if not sector_name:
                continue
                
            print(f"  [+] Analyzing: {sector_name}")
            
            # 获取板块内股票
            sector_stocks = self.get_sector_stocks(sector_name)
            if sector_stocks.empty:
                continue
            
            # 筛选主板股票，分析前20只
            count = 0
            for _, stock in sector_stocks.iterrows():
                if count >= 20:
                    break
                    
                stock_code = stock.get('代码', '')
                stock_name = stock.get('名称', '')
                
                if not stock_code or not stock_name:
                    continue
                
                # 从缓存获取市值（单位：亿元）
                market_cap = market_cap_dict.get(stock_code, 0)
                
                # 排除市值超过1000亿的公司
                if market_cap > 1000:
                    print(f"    [SKIP] {stock_name}({stock_code}) - Market cap {market_cap:.0f}B > 1000B")
                    continue
                
                # 只分析主板
                if not (stock_code.startswith('60') or stock_code.startswith('00')):
                    continue
                
                # 排除ST
                if 'ST' in stock_name or '退' in stock_name:
                    continue
                
                result = self.analyze_single_stock(
                    stock_code, stock_name, 
                    sector_name, idx + 1,
                    market_cap
                )
                
                if result and result['score'] >= 40:
                    analyzed_stocks.append(result)
                
                count += 1
        
        # 按评分排序
        analyzed_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        # 返回TOP N推荐
        recommendations = analyzed_stocks[:top_n]
        
        return recommendations
    
    def format_recommendation(self, rec: Dict) -> str:
        """格式化推荐结果"""
        output = f"""
{'='*50}
[PICK] {rec['name']} ({rec['code']})
{'='*50}
Score: {rec['score']:.1f}/100

Sector: {rec['sector']} (Rank #{rec['sector_rank']})

Price: {rec['latest_price']:.2f} CNY
Change: {rec.get('change_pct', 0):.2f}%

Technical:
  - 5D Change: {rec['price_trend'].get('change_5d_pct', 0):.2f}%
  - Above MA5: {'YES' if rec['price_trend'].get('above_ma5') else 'NO'}
  - Above MA10: {'YES' if rec['price_trend'].get('above_ma10') else 'NO'}

Volume:
  - vs 5D Avg: {rec['volume_change'].get('volume_change_pct', 0):.1f}%
  - Meets Criteria: {'YES' if rec['volume_change'].get('meets_criteria') else 'NO'}

Money Flow:
  - Consecutive Inflow: {rec['money_flow'].get('consecutive_inflow', 0)} days
  - Meets Criteria: {'YES' if rec['money_flow'].get('meets_criteria') else 'NO'}

Suggestion:
  - Buy on dips near MA5
  - Exit if no momentum in 3 days
  - Stop Loss: {rec['latest_price'] * 0.95:.2f} CNY (-5%)
"""
        return output
    
    def generate_daily_report(self) -> str:
        """生成每日推荐报告"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        report = f"""
{'#'*60}
#      JunGe TianXiaWuShuang - Daily Stock Picks
#      Date: {today_str}
{'#'*60}

Strategy:
------------------------------------------
Priority: Theme > Technical > Business > Finance
Core: Quantitative + Buy-the-dip
Rule: Exit if no momentum in 3 days
Scope: Main board stocks only (60/00)
------------------------------------------

"""
        
        print("\n[INFO] Starting analysis...")
        recommendations = self.get_recommendations(top_n=3)
        
        if not recommendations:
            report += "\n[NONE] No qualified stocks today\n"
            report += "Suggestion: Wait for clear market themes\n"
        else:
            report += f"\n[OK] Today's {len(recommendations)} picks:\n"
            for rec in recommendations:
                report += self.format_recommendation(rec)
        
        report += f"""
{'='*50}
RISK WARNING:
1. For reference only, not investment advice
2. Market has risks, invest carefully
3. Strictly follow stop-loss discipline
4. Control position size
{'='*50}
"""
        
        return report


def main():
    """主函数"""
    analyzer = JunGeAnalyzer()
    report = analyzer.generate_daily_report()
    print(report)
    
    # 保存报告
    today = datetime.now().strftime('%Y%m%d')
    filename = f"report_{today}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[OK] Report saved to: {filename}")


if __name__ == "__main__":
    main()

