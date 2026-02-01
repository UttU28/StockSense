import pandas as pd
import yfinance as yf
import requests
import concurrent.futures
from typing import Optional, Dict
from ..config import API_SOURCE
from .credentials_manager import get_credentials_manager


class YahooFinanceAPI:
    """
    Yahoo Finance API implementation using yfinance library.
    Free tier with no API key required.
    """
    
    def __init__(self):
        self.api_name = "yahoo"
    
    def get_live_data(self, symbol: str, interval: str = "1day", outputsize: int = 500) -> Optional[pd.DataFrame]:
        """
        Fetches OHLCV data using YFinance.
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
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=yf_interval)
            
            if df.empty:
                print(f"Yahoo Finance: No data found for {symbol}")
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
                    print(f"Yahoo Finance Warning: Missing columns {missing}. Found: {df.columns}")
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
            print(f"Yahoo Finance Exception for {symbol}: {e}")
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
                df = self.get_live_data(symbol, interval=tf, outputsize=500)
                results[name] = df
            except Exception as e:
                print(f"Error fetching {name} for {symbol}: {e}")
                results[name] = None
                    
        return results

    def get_earnings_dates(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetches historical earnings dates using yfinance.
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.earnings_dates
            if df is None or df.empty:
                return None
            return df
        except Exception as e:
            print(f"Error fetching earnings for {symbol}: {e}")
            return None


class TwelveDataAPIImplementation:
    """
    Twelve Data API implementation.
    Uses credentials.json for API key rotation.
    """
    
    def __init__(self, api_key: str = None):
        self.api_name = "twelve"
        self.base_url = "https://api.twelvedata.com"
        self.credentials_manager = get_credentials_manager()
        
        # If explicit API key provided, use it (for backward compatibility)
        # Otherwise, use credentials manager for rotation
        if api_key:
            self.api_key = api_key
            self.use_rotation = False
        else:
            self.api_key = None
            self.use_rotation = True
            
            if self.credentials_manager.get_key_count() == 0:
                raise ValueError("No API keys found in credentials.json. Please add keys to use Twelve Data API.")
    
    def _get_next_key(self):
        """Get the next API key using rotation if enabled, otherwise return current key."""
        if self.use_rotation:
            return self.credentials_manager.get_next_key()
        return self.api_key
    
    def get_live_data(self, symbol: str, interval: str = "1day", outputsize: int = 500) -> Optional[pd.DataFrame]:
        """
        Fetches OHLCV data from Twelve Data API.
        """
        # Map intervals to Twelve Data format
        tf_map = {
            "1day": "1day",
            "1week": "1week", 
            "1month": "1month",
            "daily": "1day",
            "weekly": "1week",
            "monthly": "1month"
        }
        td_interval = tf_map.get(interval.lower(), "1day")
        
        try:
            # Get API key (with rotation if enabled)
            api_key = self._get_next_key()
            if not api_key:
                print(f"[Twelve Data] No API key available for {symbol}")
                return None
            
            # Log is handled by credentials manager when key is retrieved
            
            url = f"{self.base_url}/time_series"
            params = {
                "symbol": symbol.upper(),
                "interval": td_interval,
                "apikey": api_key,
                "outputsize": min(outputsize, 5000),  # Twelve Data max is 5000
                "format": "json"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            # Check for HTTP rate limit errors (429 Too Many Requests)
            if response.status_code == 429:
                print(f"[Twelve Data] Rate limit exceeded for key ending in ...{api_key[-4:]}")
                # Mark this key as exhausted
                if self.use_rotation:
                    self.credentials_manager.mark_key_exhausted(api_key)
                return None
            
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if "status" in data and data["status"] == "error":
                error_msg = data.get("message", "Unknown error")
                
                # Check if it's a rate limit error
                error_msg_lower = error_msg.lower()
                if any(phrase in error_msg_lower for phrase in [
                    "rate limit", "rate_limit", "too many requests", 
                    "quota exceeded", "limit exceeded", "429"
                ]):
                    print(f"[Twelve Data] Rate limit error for key ending in ...{api_key[-4:]}: {error_msg}")
                    # Mark this key as exhausted
                    if self.use_rotation:
                        self.credentials_manager.mark_key_exhausted(api_key)
                    return None
                
                print(f"[Twelve Data] API Error for {symbol}: {error_msg}")
                return None
            
            # Check if we have time series data
            if "values" not in data or not data["values"]:
                print(f"[Twelve Data] No data found for {symbol}")
                return None
            
            # Success - no logging needed (only log on errors)
            
            # Convert to DataFrame
            values = data["values"]
            df = pd.DataFrame(values)
            
            # Rename columns to lowercase
            df.columns = [c.lower() for c in df.columns]
            
            # Map Twelve Data column names to our format
            column_mapping = {
                "datetime": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume"
            }
            
            # Rename columns
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df.rename(columns={old_name: new_name}, inplace=True)
            
            # Ensure required columns exist
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                if 'volume' in missing and len(missing) == 1:
                    df['volume'] = 0
                else:
                    print(f"Twelve Data Warning: Missing columns {missing}. Found: {df.columns}")
                    return None
            
            # Filter to required columns
            df = df[required_cols]
            
            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Convert numeric columns
            for c in ['open', 'high', 'low', 'close', 'volume']:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            
            # Remove any rows with NaN values
            df = df.dropna()
            
            # Limit output size
            if len(df) > outputsize:
                df = df.iloc[-outputsize:]
            
            # Sort ascending by date
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Twelve Data API Request Exception for {symbol}: {e}")
            return None
        except Exception as e:
            print(f"Twelve Data API Exception for {symbol}: {e}")
            return None

    def get_multi_timeframe_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Fetches Daily, Weekly, and Monthly data SEQUENTIALLY.
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
                df = self.get_live_data(symbol, interval=tf, outputsize=500)
                results[name] = df
            except Exception as e:
                print(f"Error fetching {name} for {symbol}: {e}")
                results[name] = None
                    
        return results

    def get_earnings_dates(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Twelve Data API doesn't provide earnings dates directly.
        Falls back to Yahoo Finance for earnings data.
        """
        try:
            # Fallback to Yahoo Finance for earnings
            ticker = yf.Ticker(symbol)
            df = ticker.earnings_dates
            if df is None or df.empty:
                return None
            return df
        except Exception as e:
            print(f"Error fetching earnings for {symbol}: {e}")
            return None


def get_api_instance(api_key: str = None):
    """
    Factory function that returns the appropriate API instance based on API_SOURCE.
    
    Args:
        api_key: Optional API key (for Twelve Data). If provided, uses this key instead of rotation.
                 If None and API_SOURCE is "twelve", uses credentials.json with rotation.
    
    Returns:
        API instance (YahooFinanceAPI or TwelveDataAPIImplementation)
    """
    if API_SOURCE == "twelve":
        try:
            return TwelveDataAPIImplementation(api_key=api_key)
        except ValueError as e:
            print(f"Error initializing Twelve Data API: {e}")
            print("Falling back to Yahoo Finance API")
            return YahooFinanceAPI()
    else:
        return YahooFinanceAPI()


# For backward compatibility: TwelveDataAPI class that uses the factory
class TwelveDataAPIWrapper:
    """
    Wrapper class for backward compatibility.
    Automatically selects the correct API based on API_SOURCE environment variable.
    Uses credentials.json for Twelve Data API keys when API_SOURCE=twelve.
    Automatically falls back to Yahoo Finance when all Twelve Data keys are exhausted.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self._twelve_api = None
        self._yahoo_api = None
        self._last_fallback_check = None
        self._fallback_cooldown = 60  # Check every 60 seconds if we can switch back
        
        # Directly instantiate the correct API based on API_SOURCE to avoid recursion
        if API_SOURCE == "twelve":
            try:
                self._twelve_api = TwelveDataAPIImplementation(api_key=api_key)
                # For backward compatibility, provide api_keys attribute
                if hasattr(self._twelve_api, 'credentials_manager'):
                    key_count = self._twelve_api.credentials_manager.get_key_count()
                    self.api_keys = [f"key_{i}" for i in range(key_count)]
                else:
                    self.api_keys = ['twelve-data-key']
            except ValueError as e:
                print(f"Error initializing Twelve Data API: {e}")
                print("Falling back to Yahoo Finance API")
                self._yahoo_api = YahooFinanceAPI()
                self.api_keys = ['yahoo-free-tier']
        else:
            self._yahoo_api = YahooFinanceAPI()
            self.api_keys = ['yahoo-free-tier']
    
    def _get_current_api(self):
        """
        Get the current API to use, with automatic fallback logic.
        Returns Twelve Data API if available, otherwise Yahoo Finance.
        """
        # If API_SOURCE is not "twelve", always use Yahoo
        if API_SOURCE != "twelve":
            if self._yahoo_api is None:
                self._yahoo_api = YahooFinanceAPI()
            return self._yahoo_api
        
        # If we have Twelve Data API configured
        if self._twelve_api is not None:
            # Check if all keys are exhausted
            if hasattr(self._twelve_api, 'credentials_manager'):
                cred_manager = self._twelve_api.credentials_manager
                
                # Check if all keys are exhausted
                if cred_manager.are_all_keys_exhausted():
                    # All keys exhausted, use Yahoo fallback
                    if self._yahoo_api is None:
                        self._yahoo_api = YahooFinanceAPI()
                    
                    # Log fallback only once per cooldown period
                    import time
                    now = time.time()
                    if self._last_fallback_check is None or (now - self._last_fallback_check) >= self._fallback_cooldown:
                        print(f"[API Fallback] All Twelve Data keys exhausted. Using Yahoo Finance (will retry in 1 minute)")
                        self._last_fallback_check = now
                    
                    return self._yahoo_api
                else:
                    # Keys available, use Twelve Data
                    # Check if we were using Yahoo and can switch back
                    if self._yahoo_api is not None and self._last_fallback_check is not None:
                        import time
                        now = time.time()
                        if (now - self._last_fallback_check) >= self._fallback_cooldown:
                            # Cooldown passed, try switching back to Twelve Data
                            if not cred_manager.are_all_keys_exhausted():
                                print(f"[API Fallback] Twelve Data keys available again. Switching back from Yahoo Finance")
                                self._last_fallback_check = None
                                return self._twelve_api
                    
                    return self._twelve_api
        
        # Fallback to Yahoo if Twelve Data not available
        if self._yahoo_api is None:
            self._yahoo_api = YahooFinanceAPI()
        return self._yahoo_api
    
    def _get_next_key(self):
        """For backward compatibility"""
        current_api = self._get_current_api()
        if hasattr(current_api, '_get_next_key'):
            return current_api._get_next_key()
        return getattr(current_api, 'api_key', 'yahoo')
    
    def get_live_data(self, symbol: str, interval: str = "1day", outputsize: int = 500) -> Optional[pd.DataFrame]:
        current_api = self._get_current_api()
        result = current_api.get_live_data(symbol, interval, outputsize)
        
        # If Twelve Data failed and we're using it, try Yahoo as fallback
        if result is None and current_api == self._twelve_api and self._twelve_api is not None:
            if self._yahoo_api is None:
                self._yahoo_api = YahooFinanceAPI()
            print(f"[API Fallback] Twelve Data failed for {symbol}, trying Yahoo Finance")
            return self._yahoo_api.get_live_data(symbol, interval, outputsize)
        
        return result
    
    def get_multi_timeframe_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        current_api = self._get_current_api()
        return current_api.get_multi_timeframe_data(symbol)
    
    def get_earnings_dates(self, symbol: str) -> Optional[pd.DataFrame]:
        current_api = self._get_current_api()
        return current_api.get_earnings_dates(symbol)


# Export the wrapper as TwelveDataAPI for backward compatibility
TwelveDataAPI = TwelveDataAPIWrapper
