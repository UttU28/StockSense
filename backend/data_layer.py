import requests
import json
import time
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from config import ALPHA_VANTAGE_API_KEY, BASE_URL, CALL_DELAY_SECONDS, DB_PATH
from models import SymbolState, DailyBar, WeeklyBar, IndicatorSet, EarningsRecord

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataLayer:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for caching."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                key TEXT PRIMARY KEY,
                data TEXT,
                timestamp DATETIME
            )
        ''')
        conn.commit()
        conn.close()

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from cache if it exists and is fresh (< 20 hours old)."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT data, timestamp FROM api_cache WHERE key = ?', (key,))
        row = c.fetchone()
        conn.close()

        if row:
            data_str, timestamp_str = row
            cached_time = datetime.fromisoformat(timestamp_str)
            if datetime.now() - cached_time < timedelta(hours=20):
                return json.loads(data_str)
        return None

    def _save_to_cache(self, key: str, data: Dict[str, Any]):
        """Save API response to cache."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('INSERT OR REPLACE INTO api_cache (key, data, timestamp) VALUES (?, ?, ?)',
                  (key, json.dumps(data), now))
        conn.commit()
        conn.close()

    def _fetch_api(self, function: str, symbol: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch data from Alpha Vantage with caching and rate limiting."""
        params = {"function": function, "symbol": symbol, "apikey": ALPHA_VANTAGE_API_KEY, **kwargs}
        cache_key = f"{function}_{symbol}_{json.dumps(kwargs, sort_keys=True)}"
        
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            logger.info(f"Fetching {function} for {symbol} from API...")
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if "Error Message" in data:
                logger.error(f"API Error for {function} ({symbol}): {data['Error Message']}")
                return None
            elif "Note" in data and "rate limit" in data["Note"].lower():
                logger.warning(f"API Rate Limit hit for {function} ({symbol}): {data['Note']}")
                return None
            
            self._save_to_cache(cache_key, data)
            time.sleep(CALL_DELAY_SECONDS)
            return data

        except Exception as e:
            logger.error(f"Request failed for {function} ({symbol}): {e}")
            return None

    def fetch_symbol_data(self, symbol: str) -> SymbolState:
        """Fetch all required data for a symbol and return a SymbolState object."""
        daily_json = self._fetch_api("TIME_SERIES_DAILY", symbol, outputsize="compact")
        daily_bars = self._parse_daily_bars(daily_json)

        weekly_json = self._fetch_api("TIME_SERIES_WEEKLY", symbol)
        weekly_bars = self._parse_weekly_bars(weekly_json)

        rsi_d_json = self._fetch_api("RSI", symbol, interval="daily", time_period=14, series_type="close")
        stoch_d_json = self._fetch_api("STOCHRSI", symbol, interval="daily", time_period=14, series_type="close", fastkperiod=5, fastdperiod=3, fastdmatype=1)
        macd_d_json = self._fetch_api("MACD", symbol, interval="daily", series_type="close")
        rsi_w_json = self._fetch_api("RSI", symbol, interval="weekly", time_period=14, series_type="close")
        macd_w_json = self._fetch_api("MACD", symbol, interval="weekly", series_type="close")

        indicator_set = IndicatorSet(
            daily_rsi=self._parse_technical(rsi_d_json, "RSI"),
            daily_stoch_rsi=self._parse_technical(stoch_d_json, "STOCHRSI"),
            daily_macd=self._parse_technical(macd_d_json, "MACD"),
            weekly_rsi=self._parse_technical(rsi_w_json, "RSI"),
            weekly_macd=self._parse_technical(macd_w_json, "MACD")
        )

        earnings_json = self._fetch_api("EARNINGS", symbol)
        earnings_records = self._parse_earnings(earnings_json)

        return SymbolState(
            symbol=symbol,
            last_updated=datetime.now().isoformat(),
            daily_bars=daily_bars,
            weekly_bars=weekly_bars,
            indicators=indicator_set,
            earnings=earnings_records
        )

    def _parse_daily_bars(self, data: Dict) -> List[DailyBar]:
        bars = []
        if not data or "Time Series (Daily)" not in data:
            return bars
        
        ts = data["Time Series (Daily)"]
        for date_str, values in ts.items():
            bars.append(DailyBar(
                date=date_str,
                open=float(values["1. open"]),
                high=float(values["2. high"]),
                low=float(values["3. low"]),
                close=float(values["4. close"]),
                volume=int(values["5. volume"])
            ))
        return bars

    def _parse_weekly_bars(self, data: Dict) -> List[WeeklyBar]:
        bars = []
        if not data or "Weekly Time Series" not in data:
            return bars
        
        ts = data["Weekly Time Series"]
        for date_str, values in ts.items():
            bars.append(WeeklyBar(
                date=date_str,
                open=float(values["1. open"]),
                high=float(values["2. high"]),
                low=float(values["3. low"]),
                close=float(values["4. close"]),
                volume=int(values["5. volume"])
            ))
        return bars

    def _parse_technical(self, data: Dict, indicator_key: str) -> Dict:
        """Generic parser for technical indicators."""
        if not data:
            return {}
        
        main_key = next((k for k in data.keys() if "Technical Analysis" in k), None)
        if not main_key:
            return {}
        
        result = {}
        ts = data[main_key]
        for date_str, values in ts.items():
            if len(values) == 1 and indicator_key in values:
                 result[date_str] = float(values[indicator_key])
            else:
                result[date_str] = {k: float(v) for k, v in values.items()}
        return result

    def _parse_earnings(self, data: Dict) -> List[EarningsRecord]:
        records = []
        if not data or "quarterlyEarnings" not in data:
            return records
        
        for item in data["quarterlyEarnings"]:
            records.append(EarningsRecord(
                fiscal_date_ending=item.get("fiscalDateEnding"),
                reported_date=item.get("reportedDate"),
                reported_eps=float(item["reportedEPS"]) if item.get("reportedEPS") and item["reportedEPS"] != "None" else None,
                estimated_eps=float(item["estimatedEPS"]) if item.get("estimatedEPS") and item["estimatedEPS"] != "None" else None,
                surprise=float(item["surprise"]) if item.get("surprise") and item["surprise"] != "None" else None,
                surprise_percentage=float(item["surprisePercentage"]) if item.get("surprisePercentage") and item["surprisePercentage"] != "None" else None
            ))
        return records
