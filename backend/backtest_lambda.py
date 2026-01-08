import backtrader as bt
import pandas as pd
import boto3
import json
import io
import os
from datetime import datetime

# --- Custom Strategy Classes ---

class RSIStrategy(bt.Strategy):
    params = (
        ('rsi_low', 30),
        ('rsi_high', 70),
    )

    def __init__(self):
        # We assume the data feed has an 'rsi_14' column
        # mapped to a generic 'rsi' line
        self.rsi = self.datas[0].rsi_14

    def next(self):
        if not self.position:
            if self.rsi < self.params.rsi_low:
                self.buy()
        else:
            if self.rsi > self.params.rsi_high:
                self.close()

class EMACrossoverStrategy(bt.Strategy):
    params = (('fast', 20), ('slow', 50))
    def __init__(self):
        self.ema_fast = self.datas[0].ema_20
        self.ema_slow = self.datas[0].ema_50
        self.crossover = bt.ind.CrossOver(self.ema_fast, self.ema_slow)
    def next(self):
        if not self.position:
            if self.crossover > 0: self.buy()
        elif self.crossover < 0: self.close()

class SMACrossoverStrategy(bt.Strategy):
    params = (('fast', 20), ('slow', 50))
    def __init__(self):
        self.sma_fast = self.datas[0].sma_20
        self.sma_slow = self.datas[0].sma_50
        self.crossover = bt.ind.CrossOver(self.sma_fast, self.sma_slow)
    def next(self):
        if not self.position:
            if self.crossover > 0: self.buy()
        elif self.crossover < 0: self.close()

class MACDStrategy(bt.Strategy):
    def __init__(self):
        self.macd = self.datas[0].macd
        self.signal = self.datas[0].macd_signal
        self.crossover = bt.ind.CrossOver(self.macd, self.signal)
    def next(self):
        if not self.position:
            if self.crossover > 0: self.buy()
        elif self.crossover < 0: self.close()

class BBandsStrategy(bt.Strategy):
    def __init__(self):
        self.price = self.datas[0].close
        self.upper = self.datas[0].bb_upper
        self.lower = self.datas[0].bb_lower
    def next(self):
        if not self.position:
            if self.price < self.lower: self.buy()
        elif self.price > self.upper: self.close()

# --- Data Feed Configuration ---

class IndicatorData(bt.feeds.PandasData):
    """Custom Pandas DataFeed that includes indicator columns"""
    lines = ('sma_20', 'sma_50', 'ema_20', 'ema_50', 'rsi_14', 
             'macd', 'macd_signal', 'macd_hist',
             'bb_upper', 'bb_middle', 'bb_lower')
    
    # Map CSV column names to Backtrader lines
    params = (
        ('datetime', 'Date'),
        ('open', 'Open'),
        ('high', 'High'),
        ('low', 'Low'),
        ('close', 'Close'),
        ('volume', 'Volume'),
        ('openinterest', -1),
        ('sma_20', 'SMA_20'),
        ('sma_50', 'SMA_50'),
        ('ema_20', 'EMA_20'),
        ('ema_50', 'EMA_50'),
        ('rsi_14', 'RSI_14'),
        ('macd', 'MACD_12_26_9'),
        ('macd_signal', 'MACDs_12_26_9'),
        ('macd_hist', 'MACDh_12_26_9'),
        ('bb_upper', 'BBU_20_2.0_2.0'),
        ('bb_middle', 'BBM_20_2.0_2.0'),
        ('bb_lower', 'BBL_20_2.0_2.0'),
    )

# --- Helper Functions ---

def get_indicator_data_from_s3(bucket, key):
    """Helper to read indicators CSV from S3"""
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(io.BytesIO(response['Body'].read()))
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        print(f"Error reading from S3: {str(e)}")
        return None

def save_result_to_s3(bucket, key, result_dict):
    """Helper to save results as JSON to S3"""
    s3 = boto3.client('s3')
    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(result_dict, indent=2, default=str),
            ContentType='application/json'
        )
        print(f"✓ Saved backtest result to S3: s3://{bucket}/{key}")
        return True
    except Exception as e:
        print(f"Error saving to S3: {str(e)}")
        return False

# --- Lambda Handler ---

def lambda_handler(event, context):
    """
    AWS Lambda Handler for backtesting
    Expected event: 
    - {} (Default: 11 stocks x 5 strategies)
    - {"tickers": ["NVDA"], "strategies": ["RSI", "MACD"]} (Subsets)
    """
    # 1. Configuration
    default_tickers = ["AAPL", "NVDA", "PANW", "RH", "AVGO", "MSTR", "COIN", "BLK", "ADBE", "MDB", "ASML", "TSLA"]
    default_strategies = ["RSI", "EMA", "SMA", "MACD", "BBANDS"]
    
    tickers = event.get('tickers')
    if not tickers:
        single_ticker = event.get('ticker')
        tickers = [single_ticker] if single_ticker else default_tickers
        
    strategies = event.get('strategies')
    if not strategies:
        single_strat = event.get('strategy')
        strategies = [single_strat] if single_strat else default_strategies
        
    initial_cash = event.get('initial_cash', 10000.0)
    s3_bucket = "initial-data-01"
    
    results_summary = []
    
    # 2. Outer Loop: Tickers
    for ticker in tickers:
        ticker = ticker.upper()
        input_key = f"indicators/{ticker}_indicators.csv"
        
        print(f"[{ticker}] Loading data...")
        df = get_indicator_data_from_s3(s3_bucket, input_key)
        
        if df is None or df.empty:
            print(f"[{ticker}] ⚠ Data not found. Skipping.")
            continue
            
        # 3. Inner Loop: Strategies
        for strat_name in strategies:
            strat_name = strat_name.upper()
            print(f"  - Running {strat_name}...")
            
            try:
                cerebro = bt.Cerebro()
                cerebro.broker.setcash(initial_cash)
                cerebro.broker.setcommission(commission=0.001)
                
                data = IndicatorData(dataname=df)
                cerebro.adddata(data)
                
                # Assign Strategy
                if strat_name == 'RSI':
                    cerebro.addstrategy(RSIStrategy)
                elif strat_name == 'EMA':
                    cerebro.addstrategy(EMACrossoverStrategy)
                elif strat_name == 'SMA':
                    cerebro.addstrategy(SMACrossoverStrategy)
                elif strat_name == 'MACD':
                    cerebro.addstrategy(MACDStrategy)
                elif strat_name == 'BBANDS':
                    cerebro.addstrategy(BBandsStrategy)
                else:
                    continue
                
                # Analysts
                cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
                cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
                cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
                
                # Run
                run_res = cerebro.run()
                final_value = cerebro.broker.getvalue()
                pnl = final_value - initial_cash
                
                # Results
                strat = run_res[0]
                trade_analysis = strat.analyzers.trades.get_analysis()
                dd_analysis = strat.analyzers.drawdown.get_analysis()
                returns_analysis = strat.analyzers.returns.get_analysis()
                
                summary = {
                    "ticker": ticker,
                    "strategy": strat_name,
                    "final_value": round(final_value, 2),
                    "pnl_percent": round((pnl / initial_cash) * 100, 2),
                    "max_drawdown": round(dd_analysis.max.drawdown, 2) if hasattr(dd_analysis, 'max') else 0,
                    "trades": trade_analysis.total.total if 'total' in trade_analysis else 0
                }
                
                # Save Individual result to S3
                res_key = f"backtests/{ticker}_{strat_name}_result.json"
                save_result_to_s3(s3_bucket, res_key, summary)
                results_summary.append(summary)
                
            except Exception as e:
                print(f"  - ✖ Error: {str(e)}")
                
    # 4. Final Aggregated Response
    return {
        'statusCode': 200,
        'body': json.dumps({
            "message": f"Completed {len(results_summary)} backtests",
            "results": results_summary
        }, default=str)
    }

# Local Testing
if __name__ == "__main__":
    if not os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        print("Running mock backtest locally...")
        # Simple dummy data for verification (100 days)
        dates = pd.date_range(start='2020-01-01', periods=100)
        df = pd.DataFrame({
            'Date': dates,
            'Open': [100.0 + i for i in range(100)],
            'High': [105.0 + i for i in range(100)],
            'Low': [95.0 + i for i in range(100)],
            'Close': [100.0 + i for i in range(100)],
            'Volume': [1000] * 100,
            # Force a buy (RSI < 30) on day 10 and sell (RSI > 70) on day 20
            'RSI_14': [25.0 if i == 10 else 75.0 if i == 20 else 50.0 for i in range(100)],
            'EMA_20': [100.0] * 100,
            'EMA_50': [100.0] * 100,
            'SMA_20': [100.0] * 100,
            'SMA_50': [100.0] * 100,
            'MACD_12_26_9': [0.0] * 100,
            'MACDs_12_26_9': [0.0] * 100,
            'MACDh_12_26_9': [0.0] * 100,
            'BBU_20_2.0_2.0': [110.0] * 100,
            'BBM_20_2.0_2.0': [100.0] * 100,
            'BBL_20_2.0_2.0': [90.0] * 100
        })
        
        # Manually run the backtrader part since we can't call lambda_handler (no S3)
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(10000.0)
        data = IndicatorData(dataname=df)
        cerebro.adddata(data)
        cerebro.addstrategy(RSIStrategy)
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        
        print("Starting local Backtrader run...")
        results = cerebro.run()
        print(f"Final Value: {cerebro.broker.getvalue():.2f}")
        
        trade_analysis = results[0].analyzers.trades.get_analysis()
        if 'total' in trade_analysis:
            print(f"Total Trades: {trade_analysis.total.total}")
            print(f"Won/Lost: {trade_analysis.won.total}/{trade_analysis.lost.total}")
        else:
            print("No trades executed. Check RSI values and strategy logic.")
