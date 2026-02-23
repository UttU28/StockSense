// Stock Gita Market Ticker Bar
// Live scrolling ticker showing major indices and crypto
// Auto-refreshes every 30 seconds

class MarketTickerBar {
    constructor(symbols = ['SPY', 'QQQ', 'DIA', '^VIX', 'BTC-USD']) {
        this.symbols = symbols;
        this.refreshInterval = 30000; // 30 seconds
        this.tickerData = {};
        this.intervalId = null;
        this.init();
    }

    async init() {
        // Create ticker bar element
        this.createTickerBar();

        // Fetch initial data
        await this.fetchAllData();

        // Start auto-refresh
        this.startAutoRefresh();
    }

    createTickerBar() {
        // Check if ticker already exists
        if (document.getElementById('stock-gita-ticker')) {
            return;
        }

        // Create ticker container
        const tickerContainer = document.createElement('div');
        tickerContainer.id = 'stock-gita-ticker';
        tickerContainer.className = 'stock-gita-ticker-container';

        // Create inner ticker content (will scroll)
        const tickerContent = document.createElement('div');
        tickerContent.id = 'ticker-content';
        tickerContent.className = 'ticker-content';

        tickerContainer.appendChild(tickerContent);

        // Insert at top of body or specific container
        const targetContainer = document.querySelector('.main-content') || document.body;
        targetContainer.insertBefore(tickerContainer, targetContainer.firstChild);
    }

    async fetchAllData() {
        const promises = this.symbols.map(symbol => this.fetchSymbolData(symbol));
        const results = await Promise.allSettled(promises);

        results.forEach((result, index) => {
            if (result.status === 'fulfilled') {
                this.tickerData[this.symbols[index]] = result.value;
            } else {
                console.error(`Error fetching ${this.symbols[index]}:`, result.reason);
            }
        });

        this.renderTicker();
    }

    async fetchSymbolData(symbol) {
        try {
            // Use YFinance API proxy endpoint on our backend
            const response = await fetch(`/api/ticker/${symbol}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return this.parseTickerData(symbol, data);
        } catch (error) {
            console.error(`Failed to fetch ${symbol}:`, error);
            // Return fallback data
            return {
                symbol: symbol,
                price: '---',
                change: 0,
                changePercent: 0
            };
        }
    }

    parseTickerData(symbol, data) {
        // Parse data from YFinance format
        const currentPrice = data.currentPrice || data.price || 0;
        const previousClose = data.previousClose || currentPrice;
        const change = currentPrice - previousClose;
        const changePercent = previousClose > 0 ? (change / previousClose) * 100 : 0;

        return {
            symbol: this.formatSymbol(symbol),
            price: this.formatPrice(currentPrice),
            change: this.formatChange(change),
            changePercent: changePercent.toFixed(2)
        };
    }

    formatSymbol(symbol) {
        // Clean up symbol for display
        return symbol.replace('^', '').replace('-USD', '');
    }

    formatPrice(price) {
        if (typeof price !== 'number') return '---';

        // Format based on price magnitude
        if (price >= 1000) {
            return price.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        } else {
            return price.toFixed(2);
        }
    }

    formatChange(change) {
        if (typeof change !== 'number') return '';
        return change >= 0 ? `+${change.toFixed(2)}` : change.toFixed(2);
    }

    renderTicker() {
        const tickerContent = document.getElementById('ticker-content');
        if (!tickerContent) return;

        // Build ticker HTML
        let html = '';

        for (const symbol in this.tickerData) {
            const data = this.tickerData[symbol];
            const changePercent = parseFloat(data.changePercent);
            const isPositive = changePercent >= 0;
            const directionIcon = isPositive ? '▲' : '▼';
            const colorClass = isPositive ? 'ticker-positive' : 'ticker-negative';

            html += `
                <div class="ticker-item" data-symbol="${symbol}" onclick="analyzeSymbol('${symbol}')">
                    <span class="ticker-symbol">${data.symbol}:</span>
                    <span class="ticker-price">$${data.price}</span>
                    <span class="ticker-change ${colorClass}">
                        ${directionIcon} ${Math.abs(changePercent).toFixed(2)}%
                    </span>
                </div>
                <span class="ticker-separator">|</span>
            `;
        }

        // Duplicate content for seamless scrolling
        tickerContent.innerHTML = html + html;

        // Update last refresh time
        this.updateRefreshTime();
    }

    updateRefreshTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        // Add refresh indicator
        let refreshIndicator = document.getElementById('ticker-refresh-time');
        if (!refreshIndicator) {
            refreshIndicator = document.createElement('div');
            refreshIndicator.id = 'ticker-refresh-time';
            refreshIndicator.className = 'ticker-refresh';
            const tickerContainer = document.getElementById('stock-gita-ticker');
            if (tickerContainer) {
                tickerContainer.appendChild(refreshIndicator);
            }
        }

        refreshIndicator.innerHTML = `<span class="refresh-icon">🔄</span> ${timeString}`;
        refreshIndicator.classList.add('pulse');
        setTimeout(() => refreshIndicator.classList.remove('pulse'), 500);
    }

    startAutoRefresh() {
        // Clear any existing interval
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        // Set up new interval
        this.intervalId = setInterval(async () => {
            await this.fetchAllData();
        }, this.refreshInterval);
    }

    destroy() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        const ticker = document.getElementById('stock-gita-ticker');
        if (ticker) {
            ticker.remove();
        }
    }
}

// Global function to analyze a symbol from ticker
window.analyzeSymbol = function (symbol) {
    // Find chat input
    const chatInput = document.querySelector('textarea[placeholder*="message"], textarea.message-input, #message-input');

    if (chatInput) {
        // Set value and trigger analysis
        chatInput.value = `analyze ${symbol}`;
        chatInput.focus();

        // Trigger enter key event
        const enterEvent = new KeyboardEvent('keydown', {
            key: 'Enter',
            code: 'Enter',
            keyCode: 13,
            which: 13,
            bubbles: true
        });
        chatInput.dispatchEvent(enterEvent);
    } else {
        console.warn('Chat input not found');
    }
};

// Initialize ticker when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.marketTicker = new MarketTickerBar();
    });
} else {
    window.marketTicker = new MarketTickerBar();
}

// CSS Styles for ticker (to be added inline or in separate stylesheet)
const tickerStyles = `
.stock-gita-ticker-container {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 40px;
    background: linear-gradient(135deg, var(--sg-bg-secondary) 0%, var(--sg-bg-tertiary) 100%);
    border-bottom: 1px solid var(--sg-border-primary);
    overflow: hidden;
    z-index: 1000;
    display: flex;
    align-items: center;
    padding: 0 16px;
    box-shadow: var(--sg-shadow-md);
    font-family: var(--sg-font-data);
}

.ticker-content {
    display: flex;
    align-items: center;
    white-space: nowrap;
    animation: ticker-scroll 60s linear infinite;
}

@keyframes ticker-scroll {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}

.stock-gita-ticker-container:hover .ticker-content {
    animation-play-state: paused;
}

.ticker-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-right: 16px;
    cursor: pointer;
    padding: 6px 12px;
    border-radius: var(--sg-radius-sm);
    transition: all 0.2s ease;
}

.ticker-item:hover {
    background-color: var(--sg-bg-elevated);
    transform: translateY(-1px);
}

.ticker-symbol {
    font-weight: var(--sg-weight-semibold);
    color: var(--sg-text-primary);
    font-size: var(--sg-text-sm);
}

.ticker-price {
    color: var(--sg-text-primary);
    font-weight: var(--sg-weight-medium);
    font-size: var(--sg-text-sm);
}

.ticker-change {
    font-weight: var(--sg-weight-semibold);
    font-size: var(--sg-text-xs);
}

.ticker-positive {
    color: var(--sg-accent-bullish);
}

.ticker-negative {
    color: var(--sg-accent-bearish);
}

.ticker-separator {
    color: var(--sg-border-primary);
    margin: 0 8px;
    font-size: var(--sg-text-sm);
}

.ticker-refresh {
    position: absolute;
    right: 16px;
    font-size: var(--sg-text-xs);
    color: var(--sg-text-tertiary);
    display: flex;
    align-items: center;
    gap: 4px;
}

.ticker-refresh.pulse {
    animation: pulse-once 0.5s ease;
}

@keyframes pulse-once {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.refresh-icon {
    display: inline-block;
    animation: rotate 2s linear infinite;
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* Adjust main content to account for ticker */
.main-content,
body {
    padding-top: 40px !important;
}
`;

// Inject styles
const styleElement = document.createElement('style');
styleElement.textContent = tickerStyles;
document.head.appendChild(styleElement);
