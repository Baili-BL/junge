"""
钧哥天下无双 - 配置文件
"""

# 飞书群机器人Webhook地址
# 获取方式: 
# 1. 打开飞书群
# 2. 点击群设置 -> 群机器人 -> 添加机器人
# 3. 选择"自定义机器人"
# 4. 复制Webhook地址粘贴到下面

FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/4dbfb98d-927c-4937-b513-c82605b75c15"  # 在这里填写你的飞书Webhook地址

# 示例格式:
# FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"


# 其他配置
CONFIG = {
    # 推荐股票数量
    "recommend_count": 6,
    
    # 是否只分析主板股票
    "main_board_only": True,
    
    # 分析的板块数量
    "top_sectors_count": 10,
    
    # 每个板块分析的股票数量
    "stocks_per_sector": 20,
    
    # 最低评分阈值
    "min_score": 40,
}


