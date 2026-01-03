# Backtesting Guide

## What is Backtesting?

Backtesting simulates how your trading strategy would have performed on historical data. It helps you:
- Validate if your rules actually work
- Measure performance (win rate, profit/loss)
- Find bugs in entry/exit logic
- Optimize parameters before risking real money

## Two Backtesting Systems

This project has **two separate backtesting systems**:

### 1. GS System Backtester (`backtester.py`)
Tests the **full rule-based strategy** with:
- Entry signals from RulesEngine (bias, confidence, checklist)
- Position sizing based on risk management
- Exit logic (stop loss, take profit at 2R)
- Point-in-time feature calculation (no lookahead bias)

### 2. Lambda Backtester (`backtest_lambda.py`)
Uses **Backtrader library** to test simple technical indicator strategies:
- RSI Strategy (buy <30, sell >70)
- EMA/SMA Crossover
- MACD Crossover
- Bollinger Bands

---

## How to Run Backtests

### GS System Backtester

**Basic backtest (last 100 days):**
```bash
python main.py backtest AAPL
```

**Custom account size:**
```bash
python main.py backtest AAPL --account 50000
```

**What it does:**
1. Fetches historical data for the symbol
2. Simulates trading day-by-day from 100 days ago to today
3. Applies entry rules (confidence ≥60, entry_allowed=True)
4. Manages positions (stop loss, 2R take profit)
5. Reports: total trades, win rate, PnL, final equity

**Output example:**
```
[Backtest Results for AAPL]
Total Trades: 5
Win Rate: 60.00%
Total PnL: $450.25
Final Equity: $10450.25

[Trade Log]
2024-01-15 -> 2024-01-22: TAKE_PROFIT_2R | PnL: $120.50 (2.4%)
2024-02-01 -> 2024-02-05: STOP_LOSS | PnL: -$50.00 (-1.0%)
...
```

### Lambda Backtester (Backtrader)

**Local test (no S3 required):**
```bash
python backtest_lambda.py
```

**AWS Lambda deployment:**
- Deploy to Lambda with S3 bucket access
- Trigger with event: `{"tickers": ["AAPL"], "strategies": ["RSI"]}`
- Results saved to S3: `s3://initial-data-01/backtests/`

---

## Testing Tasks Checklist

### ✅ Data Validation
- [ ] Verify data is fetched correctly (check cache or API)
- [ ] Ensure enough historical data (need 200+ days for indicators)
- [ ] Check date ranges are correct (no future dates)
- [ ] Validate indicator data exists (RSI, MACD values present)

### ✅ Entry Logic Testing
- [ ] **Entry conditions work**: Trades only enter when confidence ≥60
- [ ] **No lookahead bias**: Features calculated using only past data
- [ ] **Position sizing correct**: Units calculated based on 1% risk
- [ ] **Stop loss set**: Stop = entry - (2 * ATR) or structural level

### ✅ Exit Logic Testing
- [ ] **Stop loss triggers**: Position exits when price hits stop
- [ ] **Take profit works**: Exits at 2R target (entry + 2 * risk distance)
- [ ] **End of simulation**: Open positions closed at final bar

### ✅ Performance Metrics
- [ ] **Win rate calculation**: Wins / Total trades
- [ ] **PnL accuracy**: Sum of all trade PnLs matches equity change
- [ ] **Equity curve**: Tracks account value over time
- [ ] **Trade log complete**: All trades have entry/exit dates, prices, reasons

### ✅ Edge Cases
- [ ] **No data scenario**: Handles missing symbol data gracefully
- [ ] **Insufficient history**: Error message when <100 days available
- [ ] **No trades**: Reports 0 trades correctly (not a crash)
- [ ] **Multiple positions**: Only one position at a time (check active_position logic)

### ✅ Code Quality
- [ ] **Point-in-time state**: Each day only sees data up to that date
- [ ] **Indicator lookup**: Uses correct date keys from indicators dict
- [ ] **Weekly data filtering**: Weekly bars filtered before current date
- [ ] **Position tracking**: Active position properly cleared on exit

---

## Common Issues & Fixes

### Issue: "No daily data" error
**Fix**: Check API key in `config.py`, verify symbol exists, check cache

### Issue: Win rate shows 0% but trades exist
**Fix**: Check PnL calculation - trades with PnL=0 might be counted as losses

### Issue: Too many/few trades
**Fix**: Adjust entry confidence threshold in `backtester.py` line 133

### Issue: Stop loss never triggers
**Fix**: Verify stop price calculation and bar low comparison logic

### Issue: Equity goes negative
**Fix**: Check position sizing - units might be too large for account size

---

## What to Validate

1. **Strategy Logic**: Does it enter when it should? (RSI zones, structure, bias alignment)
2. **Risk Management**: Is 1% risk per trade actually respected?
3. **Exit Rules**: Do stops and targets work as designed?
4. **Performance**: Is win rate >50%? Is average win > average loss?
5. **Realism**: Are results too good? (might indicate bugs or overfitting)

---

## Next Steps After Backtesting

1. **Analyze losing trades**: Why did they fail? Adjust rules if needed
2. **Optimize parameters**: Test different confidence thresholds, R-multiples
3. **Forward testing**: Paper trade on live data before real money
4. **Compare strategies**: Test GS System vs simple RSI/MACD strategies

---

## Quick Test Command

Run this to test a few symbols quickly:
```bash
python main.py backtest AAPL
python main.py backtest TSLA
python main.py backtest NVDA
```

Compare results to see if strategy works across different stocks.

