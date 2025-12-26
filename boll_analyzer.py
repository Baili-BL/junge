"""
BOLL中线策略分析器
核心条件：
1. BOLL带连续收缩
2. 突破20日均线
3. 板块资金连续3日流入
4. 当前股票量能放大
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class BollAnalyzer:
    """BOLL中线策略分析器"""
    
    def __init__(self):
        self.today = datetime.now().strftime('%Y%m%d')
        self.cache = {}
    
    def get_hot_sectors(self) -> pd.DataFrame:
        """获取资金流入板块"""
        try:
            df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
            return df
        except Exception as e:
            print(f"[ERROR] Failed to get sector data: {e}")
            return pd.DataFrame()
    
    def get_sector_stocks(self, sector_name: str) -> pd.DataFrame:
        """获取板块内股票"""
        try:
            df = ak.stock_board_industry_cons_em(symbol=sector_name)
            return df
        except Exception as e:
            print(f"[ERROR] Failed to get sector stocks: {e}")
            return pd.DataFrame()
    
    def get_stock_history(self, stock_code: str, days: int = 60) -> pd.DataFrame:
        """获取股票历史数据（需要更多天数计算BOLL）"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                    start_date=start_date, end_date=end_date, adjust="qfq")
            return df.tail(days)
        except Exception as e:
            print(f"[ERROR] Failed to get history for {stock_code}: {e}")
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
                    market_cap_dict[code] = float(cap) / 100000000 if cap else 0
                except:
                    market_cap_dict[code] = 0
            self.cache['market_cap_cache'] = market_cap_dict
            return market_cap_dict
        except Exception as e:
            print(f"[ERROR] Failed to load market cap: {e}")
            return {}
    
    def calculate_boll(self, df: pd.DataFrame, period: int = 20) -> Dict:
        """
        计算布林带指标
        返回：中轨(MA20)、上轨、下轨、带宽
        """
        if df.empty or len(df) < period + 5:
            return {'valid': False}
        
        close = df['收盘']
        
        # 计算中轨（20日均线）
        ma20 = close.rolling(window=period).mean()
        
        # 计算标准差
        std = close.rolling(window=period).std()
        
        # 计算上下轨
        upper = ma20 + 2 * std
        lower = ma20 - 2 * std
        
        # 计算带宽（布林带宽度百分比）
        bandwidth = ((upper - lower) / ma20) * 100
        
        # 获取最近几天的数据
        current_price = close.iloc[-1]
        current_ma20 = ma20.iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        current_bandwidth = bandwidth.iloc[-1]
        
        # 检查BOLL收缩（最近5天带宽是否持续缩小）
        recent_bandwidth = bandwidth.tail(5).values
        is_contracting = all(recent_bandwidth[i] >= recent_bandwidth[i+1] for i in range(len(recent_bandwidth)-1))
        
        # 检查是否突破20日均线
        prev_close = close.iloc[-2]
        prev_ma20 = ma20.iloc[-2]
        breakthrough_ma20 = (prev_close <= prev_ma20) and (current_price > current_ma20)
        
        # 站在20日均线上方
        above_ma20 = current_price > current_ma20
        
        return {
            'valid': True,
            'current_price': current_price,
            'ma20': current_ma20,
            'upper': current_upper,
            'lower': current_lower,
            'bandwidth': current_bandwidth,
            'is_contracting': is_contracting,
            'breakthrough_ma20': breakthrough_ma20,
            'above_ma20': above_ma20,
            'bandwidth_values': bandwidth.tail(5).tolist()
        }
    
    def calculate_volume_change(self, df: pd.DataFrame) -> Dict:
        """计算成交量变化"""
        if df.empty or len(df) < 6:
            return {'valid': False}
        
        avg_vol_5 = df['成交量'].iloc[-6:-1].mean()
        today_vol = df['成交量'].iloc[-1]
        
        vol_change = (today_vol / avg_vol_5 - 1) * 100 if avg_vol_5 > 0 else 0
        
        return {
            'valid': True,
            'avg_volume_5d': avg_vol_5,
            'today_volume': today_vol,
            'volume_change_pct': vol_change,
            'is_amplified': vol_change > 30  # 量能放大30%以上
        }
    
    def get_money_flow(self, stock_code: str) -> pd.DataFrame:
        """获取个股资金流向"""
        try:
            df = ak.stock_individual_fund_flow(stock=stock_code, market="sh" if stock_code.startswith('6') else "sz")
            return df.head(5)
        except Exception as e:
            return pd.DataFrame()
    
    def check_money_flow(self, money_flow_df: pd.DataFrame) -> Dict:
        """检查资金流入情况"""
        if money_flow_df.empty or len(money_flow_df) < 3:
            return {'valid': False, 'consecutive_inflow': 0}
        
        consecutive_inflow = 0
        for i in range(min(3, len(money_flow_df))):
            try:
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
            'meets_criteria': consecutive_inflow >= 2
        }
    
    def score_stock(self, stock_info: Dict) -> float:
        """
        BOLL策略评分
        权重: BOLL收缩(30%) + 突破MA20(25%) + 量能放大(25%) + 资金流入(20%)
        """
        score = 0
        
        boll = stock_info.get('boll', {})
        volume = stock_info.get('volume_change', {})
        money_flow = stock_info.get('money_flow', {})
        
        # BOLL收缩评分 (30分)
        if boll.get('is_contracting'):
            score += 30
        elif boll.get('bandwidth', 100) < 15:  # 带宽较窄也加分
            score += 15
        
        # 突破/站上MA20评分 (25分)
        if boll.get('breakthrough_ma20'):
            score += 25  # 刚突破，最佳买点
        elif boll.get('above_ma20'):
            score += 15  # 站在MA20上方
        
        # 量能放大评分 (25分)
        if volume.get('is_amplified'):
            score += 25
        elif volume.get('volume_change_pct', 0) > 15:
            score += 12
        
        # 资金流入评分 (20分)
        consecutive = money_flow.get('consecutive_inflow', 0)
        score += min(consecutive * 7, 20)
        
        return score
    
    def analyze_single_stock(self, stock_code: str, stock_name: str,
                            sector_name: str = "", sector_rank: int = 100,
                            market_cap: float = 0) -> Optional[Dict]:
        """分析单只股票"""
        # 只分析主板股票
        if not (stock_code.startswith('60') or stock_code.startswith('00')):
            return None
        
        # 排除市值超过1000亿的大盘股
        if market_cap > 1000:
            return None
        
        # 获取历史数据（需要更多数据计算BOLL）
        hist_df = self.get_stock_history(stock_code, days=60)
        if hist_df.empty or len(hist_df) < 30:
            return None
        
        # 计算BOLL指标
        boll = self.calculate_boll(hist_df)
        if not boll.get('valid'):
            return None
        
        # 必须满足：站在MA20上方或刚突破
        if not boll.get('above_ma20') and not boll.get('breakthrough_ma20'):
            return None
        
        # 计算量能变化
        volume_change = self.calculate_volume_change(hist_df)
        
        # 获取资金流向
        money_flow_df = self.get_money_flow(stock_code)
        money_flow = self.check_money_flow(money_flow_df)
        
        stock_info = {
            'code': stock_code,
            'name': stock_name,
            'sector': sector_name,
            'sector_rank': sector_rank,
            'boll': boll,
            'volume_change': volume_change,
            'money_flow': money_flow,
            'latest_price': boll.get('current_price', 0),
            'ma20': boll.get('ma20', 0),
            'change_pct': hist_df['涨跌幅'].iloc[-1] if '涨跌幅' in hist_df.columns else 0,
            'market_cap': market_cap
        }
        
        # 计算综合评分
        stock_info['score'] = self.score_stock(stock_info)
        
        return stock_info
    
    def get_recommendations(self, top_n: int = 6) -> List[Dict]:
        """获取BOLL策略推荐股票"""
        print("[INFO] BOLL Strategy: Fetching hot sectors...")
        hot_sectors = self.get_hot_sectors()
        
        if hot_sectors.empty:
            print("[ERROR] Failed to get sector data")
            return []
        
        # 预加载市值数据
        market_cap_dict = self.get_all_stocks_market_cap()
        
        # 获取资金净流入前10的板块
        print("[INFO] BOLL Strategy: Analyzing sectors...")
        top_sectors = hot_sectors.head(10)
        
        analyzed_stocks = []
        
        for idx, sector in top_sectors.iterrows():
            sector_name = sector.get('名称', sector.get('行业', ''))
            if not sector_name:
                continue
            
            print(f"  [+] BOLL Analyzing: {sector_name}")
            
            sector_stocks = self.get_sector_stocks(sector_name)
            if sector_stocks.empty:
                continue
            
            count = 0
            for _, stock in sector_stocks.iterrows():
                if count >= 15:
                    break
                
                stock_code = stock.get('代码', '')
                stock_name = stock.get('名称', '')
                
                if not stock_code or not stock_name:
                    continue
                
                # 只分析主板
                if not (stock_code.startswith('60') or stock_code.startswith('00')):
                    continue
                
                # 排除ST
                if 'ST' in stock_name or '退' in stock_name:
                    continue
                
                # 获取市值
                market_cap = market_cap_dict.get(stock_code, 0)
                
                # 排除大市值
                if market_cap > 1000:
                    continue
                
                result = self.analyze_single_stock(
                    stock_code, stock_name,
                    sector_name, idx + 1,
                    market_cap
                )
                
                if result and result['score'] >= 50:
                    analyzed_stocks.append(result)
                
                count += 1
        
        # 按评分排序
        analyzed_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        return analyzed_stocks[:top_n]


def main():
    analyzer = BollAnalyzer()
    recommendations = analyzer.get_recommendations(top_n=6)
    
    print("\n" + "="*50)
    print("BOLL Mid-term Strategy Recommendations")
    print("="*50)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['name']} ({rec['code']})")
        print(f"   Score: {rec['score']}")
        print(f"   Price: {rec['latest_price']:.2f}, MA20: {rec['ma20']:.2f}")
        print(f"   BOLL Contracting: {rec['boll'].get('is_contracting')}")
        print(f"   Volume Amplified: {rec['volume_change'].get('is_amplified')}")


if __name__ == "__main__":
    main()

