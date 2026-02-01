import pandas as pd
import yfinance as yf
import requests
import concurrent.futures
from typing import Optional, Dict

class TwelveDataAPI:
    """
    Wrapper for YFinance to maintain compatibility with Stock Gita Engine.
    Named 'TwelveDataAPI' to avoid breaking imports in consumers.
    """
    
    def __init__(self, api_key: str = None):
        self.api_keys = ["yfinance-free-tier"]

    def _get_next_key(self):
        return "yfinance"

    def get_live_data(self, symbol: str, interval: str = "1day", outputsize: int = 500) -> Optional[pd.DataFrame]:
        """
        Fetches OHLCV data using YFinance with custom headers to avoid blocking.
        """
        # Map intervals
        tf_map = {
            "1day": "1d", 
            "1week": "1wk", 
            "1month": "1mo",
            "daily": "1d",
            "weekly": "1wk",
            "monthly": "1mo"
        }
        yf_interval = tf_map.get(interval.lower(), "1d")
        
        # Determine period correctly
        period = "10y"
        if yf_interval == "1wk": period = "5y"
        if yf_interval == "1mo": period = "max"
        
        try:
            # Let yfinance handle session/headers (it uses curl_cffi now)
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=yf_interval)
            
            if df.empty:
                print(f"YFinance: No data found for {symbol}")
                return None
            
            # Reset index
            df = df.reset_index()
            
            # Normalize column names
            df.columns = [c.lower() for c in df.columns]
            
            # Handle date column name
            if 'date' not in df.columns and 'datetime' in df.columns:
                 df.rename(columns={'datetime': 'date'}, inplace=True)
            
            # Ensure required columns exist
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            
            # Check for missing columns
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                # Some symbols/indices might lack Volume
                if 'volume' in missing and len(missing) == 1:
                     df['volume'] = 0
                else:
                    print(f"YFinance Warning: Missing columns {missing}. Found: {df.columns}")
                    return None
                
            # Filter and Clean
            df = df[required_cols]
            
            # Remove timezone
            if pd.api.types.is_datetime64_any_dtype(df['date']):
                 df['date'] = df['date'].dt.tz_localize(None)
            else:
                 df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
            
            for c in ['open', 'high', 'low', 'close', 'volume']:
                df[c] = pd.to_numeric(df[c])
                
            # Limit output size
            if len(df) > outputsize:
                df = df.iloc[-outputsize:]
            
            # Sort ascending
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"YFinance Exception for {symbol}: {e}")
            return None

    def get_multi_timeframe_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Fetches Daily, Weekly, and Monthly data SEQUENTIALLY.
        Sequential execution is safer for yfinance on shared IPs to avoid 429/Blocking.
        """
        timeframes = {
            "DAILY": "1day",
            "WEEKLY": "1week",
            "MONTHLY": "1month"
        }
        
        results = {}
        # Execute sequentially
        for name, tf in timeframes.items():
            try:
                # Direct call instead of thread pool
                df = self.get_live_data(symbol, interval=tf, outputsize=500)
                results[name] = df
            except Exception as e:
                print(f"Error fetching {name} for {symbol}: {e}")
                results[name] = None
                    
    
    def get_multi_timeframe_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Fetches Daily, Weekly, and Monthly data SEQUENTIALLY.
        Sequential execution is safer for yfinance on shared IPs to avoid 429/Blocking.
        """
        timeframes = {
            "DAILY": "1day",
            "WEEKLY": "1week",
            "MONTHLY": "1month"
        }
        
        results = {}
        # Execute sequentially
        for name, tf in timeframes.items():
            try:
                # Direct call instead of thread pool
                df = self.get_live_data(symbol, interval=tf, outputsize=500)
                results[name] = df
            except Exception as e:
                print(f"Error fetching {name} for {symbol}: {e}")
                results[name] = None
                    
        return results

    def get_earnings_dates(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetches historical earnings dates using yfinance.
        Start/End filtering will be handled by the consumer.
        """
        try:
            ticker = yf.Ticker(symbol)
            # earnings_dates returns a DataFrame with Index as Timestamp (tz-aware)
            df = ticker.earnings_dates
            if df is None or df.empty:
                return None
            return df
        except Exception as e:
            print(f"Error fetching earnings for {symbol}: {e}")
            return None
