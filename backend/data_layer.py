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
        """Initialize SQLite database for caching and historical data storage."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # API cache table
        c.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                key TEXT PRIMARY KEY,
                data TEXT,
                timestamp DATETIME
            )
        ''')
        
        # Historical data tables
        c.execute('''
            CREATE TABLE IF NOT EXISTS daily_bars (
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, date)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS weekly_bars (
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, date)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS daily_indicators (
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                rsi REAL,
                stoch_rsi_fastk REAL,
                stoch_rsi_fastd REAL,
                macd REAL,
                macd_signal REAL,
                macd_histogram REAL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, date)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS weekly_indicators (
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                rsi REAL,
                macd REAL,
                macd_signal REAL,
                macd_histogram REAL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, date)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS earnings (
                symbol TEXT NOT NULL,
                fiscal_date_ending DATE NOT NULL,
                reported_date DATE,
                reported_eps REAL,
                estimated_eps REAL,
                surprise REAL,
                surprise_percentage REAL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, fiscal_date_ending)
            )
        ''')
        
        # Create indexes
        c.execute('CREATE INDEX IF NOT EXISTS idx_daily_symbol_date ON daily_bars(symbol, date DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_bars(date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_weekly_symbol_date ON weekly_bars(symbol, date DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_daily_ind_symbol_date ON daily_indicators(symbol, date DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_weekly_ind_symbol_date ON weekly_indicators(symbol, date DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_earnings_symbol_date ON earnings(symbol, fiscal_date_ending DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_earnings_reported_date ON earnings(reported_date)')
        
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

    def fetch_symbol_data(self, symbol: str, use_db: bool = True) -> SymbolState:
        """
        Fetch all required data for a symbol from database only.
        No API calls are made - data must exist in database.
        
        Args:
            symbol: Stock symbol
            use_db: If True, fetch from database only (default). If False, returns empty data.
        """
        symbol = symbol.upper()
        
        # Get daily bars from database only
        daily_bars = self.get_daily_bars(symbol) if use_db else []
        if daily_bars:
            logger.info(f"Using {len(daily_bars)} daily bars from database for {symbol}")
        else:
            logger.warning(f"No daily bars found in database for {symbol}")

        # Get weekly bars from database only
        weekly_bars = self.get_weekly_bars(symbol) if use_db else []
        if weekly_bars:
            logger.info(f"Using {len(weekly_bars)} weekly bars from database for {symbol}")
        else:
            logger.warning(f"No weekly bars found in database for {symbol}")

        # Get indicators from database only
        daily_rsi = {}
        daily_stoch_rsi = {}
        daily_macd = {}
        weekly_rsi = {}
        weekly_macd = {}
        
        if use_db:
            # Get daily indicators from DB
            daily_indicators_db = self.get_daily_indicators(symbol)
            weekly_indicators_db = self.get_weekly_indicators(symbol)
            
            # Convert DB format to IndicatorSet format
            for date, ind_data in daily_indicators_db.items():
                if ind_data.get("RSI") is not None:
                    daily_rsi[date] = ind_data["RSI"]
                if ind_data.get("STOCHRSI") and isinstance(ind_data["STOCHRSI"], dict):
                    daily_stoch_rsi[date] = ind_data["STOCHRSI"]
                if ind_data.get("MACD") and isinstance(ind_data["MACD"], dict):
                    # Convert MACD format: {MACD: val, MACD_Signal: val, MACD_Hist: val}
                    macd_dict = ind_data["MACD"]
                    daily_macd[date] = {
                        "MACD": macd_dict.get("MACD"),
                        "MACD_Signal": macd_dict.get("MACD_Signal"),
                        "MACD_Hist": macd_dict.get("MACD_Hist")
                    }
            
            for date, ind_data in weekly_indicators_db.items():
                if ind_data.get("RSI") is not None:
                    weekly_rsi[date] = ind_data["RSI"]
                if ind_data.get("MACD") and isinstance(ind_data["MACD"], dict):
                    macd_dict = ind_data["MACD"]
                    weekly_macd[date] = {
                        "MACD": macd_dict.get("MACD"),
                        "MACD_Signal": macd_dict.get("MACD_Signal"),
                        "MACD_Hist": macd_dict.get("MACD_Hist")
                    }
            
            logger.info(f"Using indicators from database for {symbol} (RSI: {len(daily_rsi)}, STOCH: {len(daily_stoch_rsi)}, MACD: {len(daily_macd)})")
        
        indicator_set = IndicatorSet(
            daily_rsi=daily_rsi,
            daily_stoch_rsi=daily_stoch_rsi,
            daily_macd=daily_macd,
            weekly_rsi=weekly_rsi,
            weekly_macd=weekly_macd
        )

        # Get earnings from database only
        earnings_records = self.get_earnings(symbol) if use_db else []
        if earnings_records:
            logger.info(f"Using {len(earnings_records)} earnings records from database for {symbol}")
        else:
            logger.warning(f"No earnings found in database for {symbol}")

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
    
    def store_daily_bars(self, symbol: str, bars: List[DailyBar]):
        """Store daily bars in database (batch insert/upsert)."""
        if not bars:
            return
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.executemany('''
                INSERT OR REPLACE INTO daily_bars 
                (symbol, date, open, high, low, close, volume, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', [
                (symbol, bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
                for bar in bars
            ])
            conn.commit()
            logger.info(f"Stored {len(bars)} daily bars for {symbol}")
        except Exception as e:
            logger.error(f"Error storing daily bars for {symbol}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def store_weekly_bars(self, symbol: str, bars: List[WeeklyBar]):
        """Store weekly bars in database (batch insert/upsert)."""
        if not bars:
            return
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.executemany('''
                INSERT OR REPLACE INTO weekly_bars 
                (symbol, date, open, high, low, close, volume, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', [
                (symbol, bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
                for bar in bars
            ])
            conn.commit()
            logger.info(f"Stored {len(bars)} weekly bars for {symbol}")
        except Exception as e:
            logger.error(f"Error storing weekly bars for {symbol}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def store_daily_indicators(self, symbol: str, rsi_data: Dict, stoch_rsi_data: Dict, macd_data: Dict):
        """Store daily indicators (RSI, STOCHRSI, MACD) in database."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            # Get all unique dates from all indicators
            all_dates = set()
            if rsi_data:
                all_dates.update(rsi_data.keys())
            if stoch_rsi_data:
                all_dates.update(stoch_rsi_data.keys())
            if macd_data:
                all_dates.update(macd_data.keys())
            
            if not all_dates:
                logger.warning(f"No dates found for daily indicators for {symbol}")
                return
            
            stored_count = 0
            for date_str in all_dates:
                rsi_val = rsi_data.get(date_str) if isinstance(rsi_data.get(date_str), (int, float)) else None
                stoch_vals = stoch_rsi_data.get(date_str, {})
                stoch_fastk = stoch_vals.get("FastK") if isinstance(stoch_vals, dict) else None
                stoch_fastd = stoch_vals.get("FastD") if isinstance(stoch_vals, dict) else None
                
                # MACD keys from Alpha Vantage: "MACD", "MACD_Signal", "MACD_Hist"
                macd_vals = macd_data.get(date_str, {})
                if isinstance(macd_vals, dict):
                    # Try different possible key names
                    macd_line = macd_vals.get("MACD") or macd_vals.get("macd")
                    macd_sig = macd_vals.get("MACD_Signal") or macd_vals.get("MACDsignal") or macd_vals.get("macd_signal")
                    macd_hist = macd_vals.get("MACD_Hist") or macd_vals.get("MACD_Histogram") or macd_vals.get("MACDhist") or macd_vals.get("macd_hist")
                else:
                    macd_line = macd_sig = macd_hist = None
                
                c.execute('''
                    INSERT OR REPLACE INTO daily_indicators
                    (symbol, date, rsi, stoch_rsi_fastk, stoch_rsi_fastd, macd, macd_signal, macd_histogram, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (symbol, date_str, rsi_val, stoch_fastk, stoch_fastd, macd_line, macd_sig, macd_hist))
                stored_count += 1
            
            conn.commit()
            logger.info(f"Stored {stored_count} daily indicator records for {symbol} (RSI: {len(rsi_data)}, STOCHRSI: {len(stoch_rsi_data)}, MACD: {len(macd_data)})")
        except Exception as e:
            logger.error(f"Error storing daily indicators for {symbol}: {e}", exc_info=True)
            conn.rollback()
        finally:
            conn.close()
    
    def store_weekly_indicators(self, symbol: str, rsi_data: Dict, macd_data: Dict):
        """Store weekly indicators (RSI, MACD) in database."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            all_dates = set()
            if rsi_data:
                all_dates.update(rsi_data.keys())
            if macd_data:
                all_dates.update(macd_data.keys())
            
            if not all_dates:
                logger.warning(f"No dates found for weekly indicators for {symbol}")
                return
            
            stored_count = 0
            for date_str in all_dates:
                rsi_val = rsi_data.get(date_str) if isinstance(rsi_data.get(date_str), (int, float)) else None
                
                # MACD keys from Alpha Vantage: "MACD", "MACD_Signal", "MACD_Hist"
                macd_vals = macd_data.get(date_str, {})
                if isinstance(macd_vals, dict):
                    # Try different possible key names
                    macd_line = macd_vals.get("MACD") or macd_vals.get("macd")
                    macd_sig = macd_vals.get("MACD_Signal") or macd_vals.get("MACDsignal") or macd_vals.get("macd_signal")
                    macd_hist = macd_vals.get("MACD_Hist") or macd_vals.get("MACD_Histogram") or macd_vals.get("MACDhist") or macd_vals.get("macd_hist")
                else:
                    macd_line = macd_sig = macd_hist = None
                
                c.execute('''
                    INSERT OR REPLACE INTO weekly_indicators
                    (symbol, date, rsi, macd, macd_signal, macd_histogram, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (symbol, date_str, rsi_val, macd_line, macd_sig, macd_hist))
                stored_count += 1
            
            conn.commit()
            logger.info(f"Stored {stored_count} weekly indicator records for {symbol} (RSI: {len(rsi_data)}, MACD: {len(macd_data)})")
        except Exception as e:
            logger.error(f"Error storing weekly indicators for {symbol}: {e}", exc_info=True)
            conn.rollback()
        finally:
            conn.close()
    
    def store_earnings(self, symbol: str, earnings: List[EarningsRecord]):
        """Store earnings data in database."""
        if not earnings:
            return
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.executemany('''
                INSERT OR REPLACE INTO earnings
                (symbol, fiscal_date_ending, reported_date, reported_eps, estimated_eps, surprise, surprise_percentage, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', [
                (symbol, e.fiscal_date_ending, e.reported_date, e.reported_eps, 
                 e.estimated_eps, e.surprise, e.surprise_percentage)
                for e in earnings
            ])
            conn.commit()
            logger.info(f"Stored {len(earnings)} earnings records for {symbol}")
        except Exception as e:
            logger.error(f"Error storing earnings for {symbol}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_latest_date(self, symbol: str, table_type: str) -> Optional[str]:
        """Get the latest date for a symbol in a specific table."""
        table_map = {
            "daily_bars": "daily_bars",
            "weekly_bars": "weekly_bars",
            "daily_indicators": "daily_indicators",
            "weekly_indicators": "weekly_indicators"
        }
        
        table = table_map.get(table_type)
        if not table:
            return None
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute(f'SELECT MAX(date) FROM {table} WHERE symbol = ?', (symbol,))
            result = c.fetchone()
            return result[0] if result and result[0] else None
        except Exception as e:
            logger.error(f"Error getting latest date for {symbol} from {table}: {e}")
            return None
        finally:
            conn.close()
    
    def update_daily_data_incremental(self, symbol: str) -> Dict[str, Any]:
        """
        Incremental update: Fetch latest ~100 days from API and store only new/missing days.
        This is the day-to-day update method.
        
        Returns:
            dict with 'new_days_added', 'total_days_fetched', 'latest_date_before', 'latest_date_after'
        """
        symbol = symbol.upper()
        result = {
            "new_days_added": 0,
            "total_days_fetched": 0,
            "latest_date_before": None,
            "latest_date_after": None,
            "updated": False
        }
        
        # Check what we already have
        latest_date = self.get_latest_date(symbol, "daily_bars")
        result["latest_date_before"] = latest_date
        
        # Fetch latest ~100 days from API (compact)
        daily_json = self._fetch_api("TIME_SERIES_DAILY", symbol, outputsize="compact")
        if not daily_json or "Time Series (Daily)" not in daily_json:
            logger.warning(f"No daily data returned from API for {symbol}")
            return result
        
        # Parse the bars
        fetched_bars = self._parse_daily_bars(daily_json)
        if not fetched_bars:
            logger.warning(f"Failed to parse daily bars for {symbol}")
            return result
        
        result["total_days_fetched"] = len(fetched_bars)
        
        # Filter to only new bars (if we have existing data)
        if latest_date:
            latest_date_dt = datetime.strptime(latest_date, "%Y-%m-%d")
            new_bars = [b for b in fetched_bars if datetime.strptime(b.date, "%Y-%m-%d") > latest_date_dt]
        else:
            # No existing data, store all
            new_bars = fetched_bars
        
        if new_bars:
            # Store new bars (INSERT OR REPLACE handles updates if dates overlap)
            self.store_daily_bars(symbol, new_bars)
            result["new_days_added"] = len(new_bars)
            result["updated"] = True
            logger.info(f"Incremental update for {symbol}: Added {len(new_bars)} new days (fetched {len(fetched_bars)} total)")
        else:
            logger.info(f"Incremental update for {symbol}: No new data (already up to date)")
        
        # Get new latest date
        result["latest_date_after"] = self.get_latest_date(symbol, "daily_bars")
        
        return result
    
    def calculate_macd_for_all_dates(self, bars: List[DailyBar]) -> Dict[str, Dict[str, float]]:
        """
        Calculate MACD (12, 26, 9) for all dates in the bars list.
        Returns dict: {date: {MACD: val, MACD_Signal: val, MACD_Hist: val}}
        """
        if len(bars) < 35:  # Need at least 35 bars for MACD calculation
            return {}
        
        try:
            import pandas as pd
            # Sort bars by date ascending
            sorted_bars = sorted(bars, key=lambda x: x.date, reverse=False)
            df = pd.DataFrame([vars(b) for b in sorted_bars])
            close = df['close']
            
            # Calculate MACD components
            exp12 = close.ewm(span=12, adjust=False).mean()
            exp26 = close.ewm(span=26, adjust=False).mean()
            macd = exp12 - exp26
            signal = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal
            
            # Build result dict for all dates
            result = {}
            for i, bar in enumerate(sorted_bars):
                result[bar.date] = {
                    "MACD": float(macd.iloc[i]),
                    "MACD_Signal": float(signal.iloc[i]),
                    "MACD_Hist": float(hist.iloc[i])
                }
            
            return result
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {}
    
    def calculate_macd_for_weekly(self, bars: List[WeeklyBar]) -> Dict[str, Dict[str, float]]:
        """Calculate MACD for weekly bars."""
        if len(bars) < 35:
            return {}
        
        try:
            import pandas as pd
            sorted_bars = sorted(bars, key=lambda x: x.date, reverse=False)
            df = pd.DataFrame([vars(b) for b in sorted_bars])
            close = df['close']
            
            exp12 = close.ewm(span=12, adjust=False).mean()
            exp26 = close.ewm(span=26, adjust=False).mean()
            macd = exp12 - exp26
            signal = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal
            
            result = {}
            for i, bar in enumerate(sorted_bars):
                result[bar.date] = {
                    "MACD": float(macd.iloc[i]),
                    "MACD_Signal": float(signal.iloc[i]),
                    "MACD_Hist": float(hist.iloc[i])
                }
            
            return result
        except Exception as e:
            logger.error(f"Error calculating weekly MACD: {e}")
            return {}
    
    def get_daily_bars(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[DailyBar]:
        """
        Get daily bars from database for a date range.
        If no dates specified, returns all bars for the symbol.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            if start_date and end_date:
                c.execute('''
                    SELECT date, open, high, low, close, volume
                    FROM daily_bars
                    WHERE symbol = ? AND date >= ? AND date <= ?
                    ORDER BY date ASC
                ''', (symbol, start_date, end_date))
            elif start_date:
                c.execute('''
                    SELECT date, open, high, low, close, volume
                    FROM daily_bars
                    WHERE symbol = ? AND date >= ?
                    ORDER BY date ASC
                ''', (symbol, start_date))
            else:
                c.execute('''
                    SELECT date, open, high, low, close, volume
                    FROM daily_bars
                    WHERE symbol = ?
                    ORDER BY date ASC
                ''', (symbol,))
            
            rows = c.fetchall()
            bars = []
            for row in rows:
                bars.append(DailyBar(
                    date=row[0],
                    open=row[1],
                    high=row[2],
                    low=row[3],
                    close=row[4],
                    volume=row[5]
                ))
            return bars
        except Exception as e:
            logger.error(f"Error getting daily bars for {symbol}: {e}")
            return []
        finally:
            conn.close()
    
    def get_weekly_bars(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[WeeklyBar]:
        """Get weekly bars from database for a date range."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            if start_date and end_date:
                c.execute('''
                    SELECT date, open, high, low, close, volume
                    FROM weekly_bars
                    WHERE symbol = ? AND date >= ? AND date <= ?
                    ORDER BY date ASC
                ''', (symbol, start_date, end_date))
            elif start_date:
                c.execute('''
                    SELECT date, open, high, low, close, volume
                    FROM weekly_bars
                    WHERE symbol = ? AND date >= ?
                    ORDER BY date ASC
                ''', (symbol, start_date))
            else:
                c.execute('''
                    SELECT date, open, high, low, close, volume
                    FROM weekly_bars
                    WHERE symbol = ?
                    ORDER BY date ASC
                ''', (symbol,))
            
            rows = c.fetchall()
            bars = []
            for row in rows:
                bars.append(WeeklyBar(
                    date=row[0],
                    open=row[1],
                    high=row[2],
                    low=row[3],
                    close=row[4],
                    volume=row[5]
                ))
            return bars
        except Exception as e:
            logger.error(f"Error getting weekly bars for {symbol}: {e}")
            return []
        finally:
            conn.close()
    
    def get_daily_indicators(self, symbol: str) -> Dict[str, Dict[str, Any]]:
        """Get daily indicators from database. Returns dict: {date: {rsi, stoch_rsi_fastk, stoch_rsi_fastd, macd, macd_signal, macd_histogram}}"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute('''
                SELECT date, rsi, stoch_rsi_fastk, stoch_rsi_fastd, macd, macd_signal, macd_histogram
                FROM daily_indicators
                WHERE symbol = ?
                ORDER BY date ASC
            ''', (symbol,))
            
            rows = c.fetchall()
            indicators = {}
            for row in rows:
                date_str = row[0]
                indicators[date_str] = {
                    "RSI": row[1],
                    "STOCHRSI": {
                        "FastK": row[2],
                        "FastD": row[3]
                    } if row[2] is not None or row[3] is not None else None,
                    "MACD": {
                        "MACD": row[4],
                        "MACD_Signal": row[5],
                        "MACD_Hist": row[6]
                    } if row[4] is not None or row[5] is not None or row[6] is not None else None
                }
            return indicators
        except Exception as e:
            logger.error(f"Error getting daily indicators for {symbol}: {e}")
            return {}
        finally:
            conn.close()
    
    def get_weekly_indicators(self, symbol: str) -> Dict[str, Dict[str, Any]]:
        """Get weekly indicators from database. Returns dict: {date: {rsi, macd, macd_signal, macd_histogram}}"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute('''
                SELECT date, rsi, macd, macd_signal, macd_histogram
                FROM weekly_indicators
                WHERE symbol = ?
                ORDER BY date ASC
            ''', (symbol,))
            
            rows = c.fetchall()
            indicators = {}
            for row in rows:
                date_str = row[0]
                indicators[date_str] = {
                    "RSI": row[1],
                    "MACD": {
                        "MACD": row[2],
                        "MACD_Signal": row[3],
                        "MACD_Hist": row[4]
                    } if row[2] is not None or row[3] is not None or row[4] is not None else None
                }
            return indicators
        except Exception as e:
            logger.error(f"Error getting weekly indicators for {symbol}: {e}")
            return {}
        finally:
            conn.close()
    
    def get_earnings(self, symbol: str) -> List[EarningsRecord]:
        """Get earnings records from database."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute('''
                SELECT fiscal_date_ending, reported_date, reported_eps, estimated_eps, 
                       surprise, surprise_percentage
                FROM earnings
                WHERE symbol = ?
                ORDER BY fiscal_date_ending DESC
            ''', (symbol,))
            
            rows = c.fetchall()
            earnings = []
            for row in rows:
                earnings.append(EarningsRecord(
                    fiscal_date_ending=row[0],
                    reported_date=row[1],
                    reported_eps=row[2],
                    estimated_eps=row[3],
                    surprise=row[4],
                    surprise_percentage=row[5]
                ))
            return earnings
        except Exception as e:
            logger.error(f"Error getting earnings for {symbol}: {e}")
            return []
        finally:
            conn.close()
