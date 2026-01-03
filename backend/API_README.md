# GS System API Documentation

FastAPI backend server for the GS Trading System.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run the Server

```bash
# Development mode (auto-reload)
python app.py

# Or using uvicorn directly
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

## API Endpoints

### 1. Health Check

**GET** `/` or `/health`

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy"
}
```

### 2. Analyze Symbol

**POST** `/analyze`

Analyze a stock and get trading signals, position sizing, and recommendations.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "account_size": 10000
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "account_size": 10000}'
```

**Response:**
```json
{
  "success": true,
  "symbol": "AAPL",
  "account_size": 10000,
  "analysis": {
    "symbol": "AAPL",
    "current_price": 254.63,
    "features": {
      "daily_rsi": 45.2,
      "daily_macd_regime": "BULLISH",
      "atr_14": 2.5,
      ...
    },
    "bias": {
      "bias": "BULLISH",
      "confidence": 85
    },
    "plan": {
      "entry_analysis": {
        "entry_allowed": true,
        "entry_confidence": 75,
        "tier": "A"
      }
    }
  },
  "position": {
    "units": 9,
    "stop": 244.95,
    "take_profit_1r": 264.31,
    "take_profit_2r": 273.99,
    "risk_amount": 100.0
  }
}
```

### 3. Backtest Symbol

**POST** `/backtest`

Run a backtest on historical data.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "account_size": 10000,
  "days": 100
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/backtest" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "account_size": 10000, "days": 100}'
```

**Response:**
```json
{
  "success": true,
  "symbol": "AAPL",
  "account_size": 10000,
  "days": 100,
  "results": {
    "total_trades": 4,
    "win_rate": 50.0,
    "total_pnl": 15.81,
    "final_equity": 10015.82,
    "trades": [
      {
        "entry_date": "2025-09-30",
        "exit_date": "2025-10-10",
        "entry_price": 254.63,
        "exit_price": 244.95,
        "pnl": -87.15,
        "reason": "STOP_LOSS",
        "return_pct": -3.8
      },
      ...
    ]
  }
}
```

### 4. Scan Market

**POST** `/scan`

Scan multiple stocks for trading opportunities.

**Request Body:**
```json
{
  "symbols": ["AAPL", "TSLA", "NVDA"],
  "account_size": 10000
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "TSLA"], "account_size": 10000}'
```

**Response:**
```json
{
  "success": true,
  "account_size": 10000,
  "watchlist": ["AAPL", "TSLA"],
  "count": 2,
  "opportunities": [
    {
      "symbol": "AAPL",
      "bias": "BULLISH",
      "confidence": 75,
      "strategy": "LONG CALL (Debit)",
      "take_profit_1r": 264.31,
      "take_profit_2r": 273.99,
      "units": 9,
      "reason": "RSI in Entry Zone, Structure Bullish",
      "current_price": 254.63
    },
    ...
  ]
}
```

### 5. Get Current Price

**GET** `/symbols/{symbol}/price`

Get current price and latest bar data for a symbol.

**Example:**
```bash
curl http://localhost:8000/symbols/AAPL/price
```

**Response:**
```json
{
  "success": true,
  "symbol": "AAPL",
  "price": 254.63,
  "date": "2025-12-31",
  "open": 253.50,
  "high": 255.20,
  "low": 252.80,
  "volume": 50000000
}
```

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Analyze a symbol
response = requests.post(
    f"{BASE_URL}/analyze",
    json={"symbol": "AAPL", "account_size": 10000}
)
data = response.json()
print(f"Entry Confidence: {data['analysis']['plan']['entry_analysis']['entry_confidence']}")

# Run backtest
response = requests.post(
    f"{BASE_URL}/backtest",
    json={"symbol": "AAPL", "account_size": 10000, "days": 100}
)
results = response.json()
print(f"Win Rate: {results['results']['win_rate']}%")

# Scan market
response = requests.post(
    f"{BASE_URL}/scan",
    json={"symbols": ["AAPL", "TSLA", "NVDA"], "account_size": 10000}
)
opportunities = response.json()["opportunities"]
for opp in opportunities:
    print(f"{opp['symbol']}: {opp['confidence']}/100")
```

## JavaScript/TypeScript Client Example

```javascript
const BASE_URL = 'http://localhost:8000';

// Analyze symbol
async function analyze(symbol, accountSize = 10000) {
  const response = await fetch(`${BASE_URL}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, account_size: accountSize })
  });
  return await response.json();
}

// Backtest
async function backtest(symbol, accountSize = 10000, days = 100) {
  const response = await fetch(`${BASE_URL}/backtest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, account_size: accountSize, days })
  });
  return await response.json();
}

// Usage
const analysis = await analyze('AAPL', 10000);
console.log('Confidence:', analysis.analysis.plan.entry_analysis.entry_confidence);
```

## Error Handling

All endpoints return standard HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **404**: Not Found (symbol not found)
- **500**: Internal Server Error

Error response format:
```json
{
  "detail": "Error message here"
}
```

## CORS

The API is configured to allow CORS from all origins by default. For production, update the `allow_origins` in `app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Your frontend domain
    ...
)
```

## Production Deployment

For production, use a production ASGI server:

```bash
# Using gunicorn with uvicorn workers
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or using uvicorn directly
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

## Environment Variables

Make sure your Alpha Vantage API key is set in `config.py`:

```python
ALPHA_VANTAGE_API_KEY = "YOUR_API_KEY"
```

## Rate Limiting

The API respects Alpha Vantage rate limits (15 seconds between calls). The backend uses caching to minimize API calls.

