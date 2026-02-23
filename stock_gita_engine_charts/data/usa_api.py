import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
import time

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


class MassiveAPI:
    """
    Wrapper for Massive API - provides OHLC data and technical indicators.
    """
    
    BASE_URL = "https://api.massive.com"
    
    def __init__(self, api_key: str = None):
        from config import MASSIVE_API_KEY, TWELVE_DATA_API_KEY
        self.api_key = api_key or MASSIVE_API_KEY
        self.twelve_data_api_key = TWELVE_DATA_API_KEY
    
    def _request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make API request with error handling."""
        params = params or {}
        params["apiKey"] = self.api_key
        
        try:
            url = f"{self.BASE_URL}{endpoint}"
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            print(f"Massive API error: {resp.status_code} - {resp.text}")
            return None
        except Exception as e:
            print(f"Massive API exception: {e}")
            return None

    def _fetch_twelvedata_earnings(self, symbol: str) -> Optional[dict]:
        """
        Fetches earnings data from TwelveData API as fallback.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Raw API response dict or None if request fails
        """
        try:
            url = "https://api.twelvedata.com/earnings"
            params = {
                "symbol": symbol,
                "apikey": self.twelve_data_api_key
            }
            resp = requests.get(url, params=params, timeout=30)

            if resp.status_code == 200:
                return resp.json()

            print(f"TwelveData API error: {resp.status_code} - {resp.text}")
            return None

        except Exception as e:
            print(f"TwelveData API exception: {e}")
            return None

    def _normalize_earnings_data(self, data: dict, source: str) -> Optional[pd.DataFrame]:
        """
        Normalizes earnings data from different API sources into consistent DataFrame format.

        Args:
            data: Raw API response dictionary
            source: API source identifier ("tmx" or "twelvedata")

        Returns:
            Normalized DataFrame with consistent schema or None if data is invalid

        Output Schema:
            - date: datetime - The earnings date (normalized from various source formats)
        """
        try:
            dates = []

            if source == "tmx":
                # Parse TMX response format: extract earnings dates from results array
                if not data or "results" not in data:
                    print(f"Failed to normalize earnings data from {source}: missing 'results' field")
                    return None

                results = data.get("results", [])
                if not results:
                    print(f"Failed to normalize earnings data from {source}: empty results array")
                    return None

                for event in results:
                    event_date = event.get("event_date")
                    if event_date:
                        dates.append(event_date)

            elif source == "twelvedata":
                # Parse TwelveData response format: extract dates from earnings array
                if not data or "earnings" not in data:
                    print(f"Failed to normalize earnings data from {source}: missing 'earnings' field")
                    return None

                earnings = data.get("earnings", [])
                if not earnings:
                    print(f"Failed to normalize earnings data from {source}: empty earnings array")
                    return None

                for earning in earnings:
                    date = earning.get("date")
                    if date:
                        dates.append(date)

            else:
                print(f"Failed to normalize earnings data: unknown source '{source}'")
                return None

            if not dates:
                print(f"Failed to normalize earnings data from {source}: no valid dates found")
                return None

            # Convert date strings to pandas datetime and create DataFrame
            df = pd.DataFrame({"date": dates})
            df["date"] = pd.to_datetime(df["date"])

            return df

        except Exception as e:
            print(f"Failed to normalize earnings data from {source}: {e}")
            return None



    def get_live_data(self, symbol: str, interval: str = "1day", outputsize: int = 500) -> Optional[pd.DataFrame]:
        """
        Fetches OHLCV data from Massive API.
        """
        # Map intervals
        tf_map = {
            "1day": "day", "daily": "day",
            "1week": "week", "weekly": "week", 
            "1month": "month", "monthly": "month",
            "1hour": "hour", "hourly": "hour"
        }
        timespan = tf_map.get(interval.lower(), "day")
        
        # Date range - request recent data based on outputsize
        to_date = datetime.now().strftime("%Y-%m-%d")
        if timespan == "day":
            # For daily, request outputsize * 1.5 days to account for weekends/holidays
            days_back = int(outputsize * 1.5)
        elif timespan == "week":
            days_back = outputsize * 7 * 2  # weeks * 7 days * 2 for buffer
        elif timespan == "month":
            days_back = outputsize * 30 * 2  # months * 30 days * 2 for buffer
        else:
            days_back = outputsize * 2
        
        # Cap at 2 years max to avoid API issues
        days_back = min(days_back, 730)
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        endpoint = f"/v2/aggs/ticker/{symbol}/range/1/{timespan}/{from_date}/{to_date}"
        params = {"adjusted": "true", "sort": "asc", "limit": min(outputsize, 5000)}
        
        data = self._request(endpoint, params)
        if not data or data.get("status") != "OK" or not data.get("results"):
            print(f"Massive API: No data for {symbol}")
            return None
        
        # Parse results
        df = pd.DataFrame(data["results"])
        df.rename(columns={
            "t": "date", "o": "open", "h": "high", 
            "l": "low", "c": "close", "v": "volume"
        }, inplace=True)
        
        # Convert timestamp to datetime
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        
        # Select and order columns
        df = df[["date", "open", "high", "low", "close", "volume"]]
        
        # Limit to outputsize
        if len(df) > outputsize:
            df = df.iloc[-outputsize:]
        
        return df.reset_index(drop=True)

    def get_rsi(self, symbol: str, window: int = 14, limit: int = 100) -> Optional[pd.DataFrame]:
        """Get RSI indicator from Massive API."""
        endpoint = f"/v1/indicators/rsi/{symbol}"
        params = {"timespan": "day", "window": window, "series_type": "close", "adjusted": "true", "limit": limit, "order": "desc"}
        
        data = self._request(endpoint, params)
        if not data or not data.get("results", {}).get("values"):
            return None
        
        df = pd.DataFrame(data["results"]["values"])
        df.rename(columns={"timestamp": "date", "value": "rsi"}, inplace=True)
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        return df

    def get_macd(self, symbol: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """Get MACD indicator from Massive API."""
        endpoint = f"/v1/indicators/macd/{symbol}"
        params = {"timespan": "day", "adjusted": "true", "limit": limit, "order": "desc"}
        
        data = self._request(endpoint, params)
        if not data or not data.get("results", {}).get("values"):
            return None
        
        df = pd.DataFrame(data["results"]["values"])
        df.rename(columns={"timestamp": "date", "value": "macd", "signal": "macd_signal", "histogram": "macd_hist"}, inplace=True)
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        return df

    def get_sma(self, symbol: str, window: int = 50, limit: int = 100) -> Optional[pd.DataFrame]:
        """Get SMA indicator from Massive API."""
        endpoint = f"/v1/indicators/sma/{symbol}"
        params = {"timespan": "day", "window": window, "series_type": "close", "adjusted": "true", "limit": limit, "order": "desc"}
        
        data = self._request(endpoint, params)
        if not data or not data.get("results", {}).get("values"):
            return None
        
        df = pd.DataFrame(data["results"]["values"])
        df.rename(columns={"timestamp": "date", "value": f"sma_{window}"}, inplace=True)
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        return df

    def get_ema(self, symbol: str, window: int = 20, limit: int = 100) -> Optional[pd.DataFrame]:
        """Get EMA indicator from Massive API."""
        endpoint = f"/v1/indicators/ema/{symbol}"
        params = {"timespan": "day", "window": window, "series_type": "close", "adjusted": "true", "limit": limit, "order": "desc"}
        
        data = self._request(endpoint, params)
        if not data or not data.get("results", {}).get("values"):
            return None
        
        df = pd.DataFrame(data["results"]["values"])
        df.rename(columns={"timestamp": "date", "value": f"ema_{window}"}, inplace=True)
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        return df

    def get_all_indicators(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Fetch all available indicators for a symbol."""
        indicators = {}
        
        # Fetch each indicator
        rsi = self.get_rsi(symbol)
        if rsi is not None:
            indicators["rsi"] = rsi
        
        macd = self.get_macd(symbol)
        if macd is not None:
            indicators["macd"] = macd
        
        sma_50 = self.get_sma(symbol, window=50)
        if sma_50 is not None:
            indicators["sma_50"] = sma_50
        
        sma_200 = self.get_sma(symbol, window=200)
        if sma_200 is not None:
            indicators["sma_200"] = sma_200
        
        ema_20 = self.get_ema(symbol, window=20)
        if ema_20 is not None:
            indicators["ema_20"] = ema_20
        
        return indicators

    def get_multi_timeframe_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Fetches Daily, Weekly, and Monthly data."""
        timeframes = {"DAILY": "1day", "WEEKLY": "1week", "MONTHLY": "1month"}
        results = {}
        
        for name, tf in timeframes.items():
            df = self.get_live_data(symbol, interval=tf, outputsize=500)
            results[name] = df
            time.sleep(0.2)  # Rate limit protection
        
        return results

    def get_earnings_dates(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetches earnings dates - falls back to yfinance."""
        if not YFINANCE_AVAILABLE:
            return None
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.earnings_dates
            if df is None or df.empty:
                return None
            return df
        except Exception as e:
            print(f"Error fetching earnings for {symbol}: {e}")
            return None


# Alias for backward compatibility
TwelveDataAPI = MassiveAPI
