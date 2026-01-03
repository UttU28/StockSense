# GS System

A rule-based trading system that analyzes stocks using technical indicators, market structure, and pattern recognition to generate entry signals and position sizing recommendations.

## What It Does

- **Data Collection**: Fetches daily/weekly price data and technical indicators from Alpha Vantage API
- **Feature Engineering**: Computes RSI, MACD, StochRSI, ATR, SMAs, candle patterns, and support/resistance levels
- **Rule-Based Analysis**: Determines market bias, volatility regime, entry confidence, and options strategy recommendations
- **Position Sizing**: Calculates position size based on 1% risk per trade with confidence scaling
- **Backtesting**: Tests strategies on historical data
- **Market Scanning**: Scans multiple stocks for trading opportunities

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Set your Alpha Vantage API key in `config.py`:
```python
ALPHA_VANTAGE_API_KEY = "YOUR_API_KEY"
```

### Usage

**Analyze a single stock:**
```bash
python main.py analyze AAPL
```

**Backtest a symbol:**
```bash
python main.py backtest AAPL
```

> 📖 **See [BACKTESTING.md](BACKTESTING.md) for detailed backtesting guide, testing tasks, and validation checklist.**

**Scan watchlist for opportunities:**
```bash
python main.py scan
```

**Custom account size:**
```bash
python main.py analyze AAPL --account 50000
```

## Commands

- `analyze <SYMBOL>` - Full analysis with entry signals and position sizing
- `backtest <SYMBOL>` - Backtest strategy on last 100 days
- `scan [SYMBOLS]` - Scan default watchlist or custom symbols (comma-separated)

## Data Caching

All API responses are cached in `cache/gs_data.db` (SQLite) with 12-hour expiry to minimize API calls.

## API Server (FastAPI)

Run the REST API server:

```bash
python app.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs

See [API_README.md](API_README.md) for complete API documentation and examples.

**Available Endpoints:**
- `POST /analyze` - Analyze a stock symbol
- `POST /backtest` - Run backtest on historical data
- `POST /scan` - Scan multiple stocks for opportunities
- `GET /symbols/{symbol}/price` - Get current price

## AWS Lambda

The `backtest_lambda.py` module can be deployed to AWS Lambda for serverless backtesting. It reads indicator data from S3 and writes results back.

