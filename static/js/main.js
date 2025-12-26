/**
 * 股票推荐系统 - 前端逻辑
 */

const API_BASE = '';

// DOM元素
const elements = {
    currentDate: document.getElementById('currentDate'),
    // 钧哥策略
    updateStatus: document.getElementById('updateStatus'),
    btnRefresh: document.getElementById('btnRefresh'),
    loadingState: document.getElementById('loadingState'),
    emptyState: document.getElementById('emptyState'),
    stockGrid: document.getElementById('stockGrid'),
    recCount: document.getElementById('recCount'),
    jungePage: document.getElementById('jungePage'),
    // BOLL策略
    bollUpdateStatus: document.getElementById('bollUpdateStatus'),
    btnBollRefresh: document.getElementById('btnBollRefresh'),
    bollLoadingState: document.getElementById('bollLoadingState'),
    bollEmptyState: document.getElementById('bollEmptyState'),
    bollStockGrid: document.getElementById('bollStockGrid'),
    bollRecCount: document.getElementById('bollRecCount'),
    bollPage: document.getElementById('bollPage')
};

// 当前Tab
let currentTab = 'junge';

/**
 * 初始化应用
 */
function init() {
    updateCurrentDate();
    fetchRecommendations();
    fetchBollRecommendations();
    
    // 定时刷新（每10分钟）
    setInterval(() => {
        if (currentTab === 'junge') {
            fetchRecommendations();
        } else {
            fetchBollRecommendations();
        }
    }, 10 * 60 * 1000);
}

/**
 * Tab切换
 */
function switchTab(tab) {
    currentTab = tab;
    
    // 更新Tab按钮状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        }
    });
    
    // 切换页面
    if (tab === 'junge') {
        elements.jungePage.style.display = 'block';
        elements.bollPage.style.display = 'none';
        document.body.classList.remove('boll-active');
    } else {
        elements.jungePage.style.display = 'none';
        elements.bollPage.style.display = 'block';
        document.body.classList.add('boll-active');
    }
    
    // 添加动画
    const activePage = tab === 'junge' ? elements.jungePage : elements.bollPage;
    activePage.style.animation = 'none';
    activePage.offsetHeight; // 触发reflow
    activePage.style.animation = 'fadeIn 0.3s ease';
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
        statusDot.style.background = 'var(--gold-primary)';
    } else {
        statusDot.style.background = 'var(--fall-green)';
    }
    statusText.textContent = text;
}

/**
 * 获取钧哥策略推荐
 */
async function fetchRecommendations(forceRefresh = false) {
    try {
        showLoading(true);
        updateStatus('loading', '分析中...');
        if (elements.btnRefresh) elements.btnRefresh.classList.add('loading');
        
        const url = forceRefresh 
            ? `${API_BASE}/api/recommendations?refresh=true`
            : `${API_BASE}/api/recommendations`;
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.loading) {
            setTimeout(() => fetchRecommendations(false), 3000);
            return;
        }
        
        if (result.success && result.data) {
            renderRecommendations(result.data);
            updateStatus('ready', `${result.data.last_update || '刚刚'}`);
        } else {
            showEmpty();
            updateStatus('error', '获取失败');
        }
    } catch (error) {
        console.error('获取推荐失败:', error);
        showEmpty();
        updateStatus('error', '网络错误');
    } finally {
        if (elements.btnRefresh) elements.btnRefresh.classList.remove('loading');
    }
}

/**
 * 显示加载状态
 */
function showLoading(show) {
    elements.loadingState.style.display = show ? 'flex' : 'none';
    elements.emptyState.style.display = 'none';
    if (show) elements.stockGrid.innerHTML = '';
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
    elements.recCount.textContent = count;
    showLoading(false);
    
    if (!recommendations || recommendations.length === 0) {
        showEmpty();
        return;
    }
    
    elements.stockGrid.innerHTML = recommendations.map((stock, index) => 
        createStockCard(stock, index)
    ).join('');
}

/**
 * 创建股票卡片
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

// ==================== BOLL策略 ====================

/**
 * 更新BOLL状态显示
 */
function updateBollStatus(status, text) {
    const statusDot = elements.bollUpdateStatus.querySelector('.status-dot');
    const statusText = elements.bollUpdateStatus.querySelector('.status-text');
    
    statusDot.className = 'status-dot boll-dot';
    if (status === 'loading') {
        statusDot.style.background = 'var(--boll-primary)';
    } else {
        statusDot.style.background = 'var(--boll-light)';
    }
    statusText.textContent = text;
}

/**
 * 获取BOLL策略推荐
 */
async function fetchBollRecommendations(forceRefresh = false) {
    try {
        showBollLoading(true);
        updateBollStatus('loading', '分析中...');
        
        const url = forceRefresh 
            ? `${API_BASE}/api/boll_recommendations?refresh=true`
            : `${API_BASE}/api/boll_recommendations`;
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.loading) {
            setTimeout(() => fetchBollRecommendations(false), 3000);
            return;
        }
        
        if (result.success && result.data) {
            renderBollRecommendations(result.data);
            updateBollStatus('ready', `${result.data.last_update || '刚刚'}`);
        } else {
            showBollEmpty();
            updateBollStatus('error', '获取失败');
        }
    } catch (error) {
        console.error('获取BOLL推荐失败:', error);
        showBollEmpty();
        updateBollStatus('error', '网络错误');
    }
}

/**
 * 显示BOLL加载状态
 */
function showBollLoading(show) {
    elements.bollLoadingState.style.display = show ? 'flex' : 'none';
    elements.bollEmptyState.style.display = 'none';
    if (show) elements.bollStockGrid.innerHTML = '';
}

/**
 * 显示BOLL空状态
 */
function showBollEmpty() {
    elements.bollLoadingState.style.display = 'none';
    elements.bollEmptyState.style.display = 'flex';
    elements.bollStockGrid.innerHTML = '';
    elements.bollRecCount.textContent = '0';
}

/**
 * 渲染BOLL推荐股票
 */
function renderBollRecommendations(data) {
    const { recommendations, count } = data;
    elements.bollRecCount.textContent = count;
    showBollLoading(false);
    
    if (!recommendations || recommendations.length === 0) {
        showBollEmpty();
        return;
    }
    
    elements.bollStockGrid.innerHTML = recommendations.map((stock, index) => 
        createBollStockCard(stock, index)
    ).join('');
}

/**
 * 创建BOLL股票卡片
 */
function createBollStockCard(stock, index) {
    const changeClass = stock.change_pct >= 0 ? 'up' : 'down';
    const changeSign = stock.change_pct >= 0 ? '+' : '';
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
                    <div class="metric-label">MA20</div>
                    <div class="metric-value">${stock.ma20.toFixed(2)}</div>
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
                <span class="boll-indicator ${stock.boll.is_contracting ? 'active' : ''}">BOLL收缩${stock.boll.is_contracting ? '✓' : ''}</span>
                <span class="boll-indicator ${stock.boll.breakthrough_ma20 ? 'active' : ''}">突破MA20${stock.boll.breakthrough_ma20 ? '✓' : ''}</span>
                <span class="boll-indicator ${stock.boll.above_ma20 ? 'active' : ''}">站上MA20${stock.boll.above_ma20 ? '✓' : ''}</span>
                <span class="boll-indicator ${stock.volume_change.is_amplified ? 'active' : ''}">量能放大${stock.volume_change.is_amplified ? '✓' : ''}</span>
            </div>
            
            <div class="stop-loss">
                <span>止损 -5%</span>
                <span>¥${stock.stop_loss.toFixed(2)}</span>
            </div>
        </div>
    `;
}

// ==================== 飞书推送 ====================

/**
 * 推送到飞书群
 */
async function pushToFeishu() {
    const btn = document.getElementById('btnFeishu');
    
    try {
        btn.classList.add('loading');
        btn.innerHTML = '📤 推送中...';
        
        const response = await fetch(`${API_BASE}/api/push_feishu`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            btn.classList.remove('loading');
            btn.classList.add('success');
            btn.innerHTML = '✅ 推送成功';
            
            setTimeout(() => {
                btn.classList.remove('success');
                btn.innerHTML = '📤 飞书';
            }, 3000);
        } else {
            throw new Error(result.error || 'Push failed');
        }
    } catch (error) {
        console.error('推送飞书失败:', error);
        btn.classList.remove('loading');
        btn.innerHTML = '❌ 失败';
        
        alert('推送失败: ' + error.message);
        
        setTimeout(() => {
            btn.innerHTML = '📤 飞书';
        }, 3000);
    }
}

// 格式化数字
function formatNumber(num) {
    if (num >= 100000000) {
        return (num / 100000000).toFixed(2) + '亿';
    } else if (num >= 10000) {
        return (num / 10000).toFixed(2) + '万';
    }
    return num.toFixed(2);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);

// 暴露函数给HTML使用
window.switchTab = switchTab;
window.fetchRecommendations = fetchRecommendations;
window.fetchBollRecommendations = fetchBollRecommendations;
window.pushToFeishu = pushToFeishu;
