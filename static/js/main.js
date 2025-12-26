/**
 * 钧哥天下无双 - 股票推荐系统前端逻辑
 */

// API基础URL
const API_BASE = '';

// DOM元素
const elements = {
    currentDate: document.getElementById('currentDate'),
    updateStatus: document.getElementById('updateStatus'),
    btnRefresh: document.getElementById('btnRefresh'),
    loadingState: document.getElementById('loadingState'),
    emptyState: document.getElementById('emptyState'),
    stockGrid: document.getElementById('stockGrid'),
    recCount: document.getElementById('recCount')
};

/**
 * 初始化应用
 */
function init() {
    // 设置当前日期
    updateCurrentDate();
    
    // 获取推荐数据
    fetchRecommendations();
    
    // 定时刷新（每10分钟）
    setInterval(() => {
        fetchRecommendations();
    }, 10 * 60 * 1000);
}

/**
 * 更新当前日期显示
 */
function updateCurrentDate() {
    const now = new Date();
    const month = now.getMonth() + 1;
    const day = now.getDate();
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    elements.currentDate.textContent = `${month}月${day}日 周${weekdays[now.getDay()]}`;
}

/**
 * 更新状态显示
 */
function updateStatus(status, text) {
    const statusDot = elements.updateStatus.querySelector('.status-dot');
    const statusText = elements.updateStatus.querySelector('.status-text');
    
    statusDot.className = 'status-dot';
    if (status === 'loading') {
        statusDot.classList.add('loading');
    }
    statusText.textContent = text;
}

/**
 * 获取推荐数据
 */
async function fetchRecommendations(forceRefresh = false) {
    try {
        // 显示加载状态
        showLoading(true);
        updateStatus('loading', '正在分析...');
        elements.btnRefresh.classList.add('loading');
        
        const url = forceRefresh 
            ? `${API_BASE}/api/recommendations?refresh=true`
            : `${API_BASE}/api/recommendations`;
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.loading) {
            // 如果服务器正在处理，轮询等待
            setTimeout(() => fetchRecommendations(false), 3000);
            return;
        }
        
        if (result.success && result.data) {
            renderRecommendations(result.data);
            updateStatus('ready', `更新于 ${result.data.last_update || '刚刚'}`);
        } else {
            showEmpty();
            updateStatus('error', '获取数据失败');
        }
    } catch (error) {
        console.error('获取推荐失败:', error);
        showEmpty();
        updateStatus('error', '网络错误');
    } finally {
        elements.btnRefresh.classList.remove('loading');
    }
}

/**
 * 显示加载状态
 */
function showLoading(show) {
    elements.loadingState.style.display = show ? 'flex' : 'none';
    elements.emptyState.style.display = 'none';
    if (show) {
        elements.stockGrid.innerHTML = '';
    }
}

/**
 * 显示空状态
 */
function showEmpty() {
    elements.loadingState.style.display = 'none';
    elements.emptyState.style.display = 'flex';
    elements.stockGrid.innerHTML = '';
    elements.recCount.textContent = '0';
}

/**
 * 渲染推荐股票
 */
function renderRecommendations(data) {
    const { recommendations, count } = data;
    
    // 更新推荐数量
    elements.recCount.textContent = count;
    
    // 隐藏加载状态
    showLoading(false);
    
    if (!recommendations || recommendations.length === 0) {
        showEmpty();
        return;
    }
    
    // 渲染股票卡片
    elements.stockGrid.innerHTML = recommendations.map((stock, index) => 
        createStockCard(stock, index)
    ).join('');
}

/**
 * 创建股票卡片HTML - 紧凑版
 */
function createStockCard(stock, index) {
    const changeClass = stock.change_pct >= 0 ? 'up' : 'down';
    const changeSign = stock.change_pct >= 0 ? '+' : '';
    const change5dClass = stock.price_trend.change_5d_pct >= 0 ? 'positive' : 'negative';
    const change5dSign = stock.price_trend.change_5d_pct >= 0 ? '+' : '';
    const volumeSign = stock.volume_change.volume_change_pct >= 0 ? '+' : '';
    
    return `
        <div class="stock-card">
            <div class="stock-header">
                <div class="stock-info">
                    <h3>${stock.name}</h3>
                    <span class="stock-code">${stock.code}</span>
                </div>
                <div class="stock-score">
                    <span class="score-value">${stock.score}</span>
                    <span class="score-label">评分</span>
                </div>
            </div>
            
            <div class="stock-price-row">
                <div>
                    <span class="price-value">${stock.latest_price.toFixed(2)}</span>
                    <span class="price-unit">元</span>
                </div>
                <div class="price-change ${changeClass}">${changeSign}${stock.change_pct.toFixed(2)}%</div>
            </div>
            
            <div class="stock-sector">
                📈 ${stock.sector} <span class="sector-rank">#${stock.sector_rank}</span>
                ${stock.market_cap ? `<span class="market-cap">${stock.market_cap.toFixed(0)}亿</span>` : ''}
            </div>
            
            <div class="stock-metrics">
                <div class="metric">
                    <div class="metric-label">5日涨幅</div>
                    <div class="metric-value ${change5dClass}">${change5dSign}${stock.price_trend.change_5d_pct.toFixed(1)}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">量能</div>
                    <div class="metric-value positive">${volumeSign}${stock.volume_change.volume_change_pct.toFixed(0)}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">资金</div>
                    <div class="metric-value">${stock.money_flow.consecutive_inflow}天</div>
                </div>
            </div>
            
            <div class="stock-indicators">
                <span class="indicator ${stock.price_trend.above_ma5 ? 'pass' : 'fail'}">5日线${stock.price_trend.above_ma5 ? '✓' : '✗'}</span>
                <span class="indicator ${stock.price_trend.above_ma10 ? 'pass' : 'fail'}">10日线${stock.price_trend.above_ma10 ? '✓' : '✗'}</span>
                <span class="indicator ${stock.volume_change.meets_criteria ? 'pass' : 'fail'}">量能${stock.volume_change.meets_criteria ? '✓' : '✗'}</span>
                <span class="indicator ${stock.money_flow.meets_criteria ? 'pass' : 'fail'}">资金${stock.money_flow.meets_criteria ? '✓' : '✗'}</span>
            </div>
            
            <div class="stop-loss">
                <span>止损 -5%</span>
                <span>¥${stock.stop_loss.toFixed(2)}</span>
            </div>
        </div>
    `;
}

/**
 * 格式化数字
 */
function formatNumber(num) {
    if (num >= 100000000) {
        return (num / 100000000).toFixed(2) + '亿';
    } else if (num >= 10000) {
        return (num / 10000).toFixed(2) + '万';
    }
    return num.toFixed(2);
}

/**
 * 推送到飞书群
 */
async function pushToFeishu() {
    const btn = document.getElementById('btnFeishu');
    
    try {
        btn.classList.add('loading');
        btn.innerHTML = '<span class="feishu-icon">📤</span> 推送中...';
        
        const response = await fetch(`${API_BASE}/api/push_feishu`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            btn.classList.remove('loading');
            btn.classList.add('success');
            btn.innerHTML = '<span class="feishu-icon">✅</span> 推送成功';
            
            // 3秒后恢复按钮状态
            setTimeout(() => {
                btn.classList.remove('success');
                btn.innerHTML = '<span class="feishu-icon">📤</span> 推送飞书';
            }, 3000);
        } else {
            throw new Error(result.error || 'Push failed');
        }
    } catch (error) {
        console.error('推送飞书失败:', error);
        btn.classList.remove('loading');
        btn.innerHTML = '<span class="feishu-icon">❌</span> 推送失败';
        
        // 显示错误提示
        alert('推送失败: ' + error.message + '\n\n请检查 config.py 中的 FEISHU_WEBHOOK_URL 配置');
        
        // 3秒后恢复按钮状态
        setTimeout(() => {
            btn.innerHTML = '<span class="feishu-icon">📤</span> 推送飞书';
        }, 3000);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);

// 暴露函数给HTML使用
window.fetchRecommendations = fetchRecommendations;
window.pushToFeishu = pushToFeishu;

