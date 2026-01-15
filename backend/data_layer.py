import sqlite3
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List

from config import DB_PATH
from models import SymbolState, DailyBar, IndicatorSet, EarningsRecord

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
            CREATE TABLE IF NOT EXISTS daily_indicators (
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                rsi_1day REAL,
                rsi_1week REAL,
                rsi_1month REAL,
                macd_1day REAL,
                macd_signal_1day REAL,
                macd_hist_1day REAL,
                macd_1week REAL,
                macd_signal_1week REAL,
                macd_hist_1week REAL,
                macd_1month REAL,
                macd_signal_1month REAL,
                macd_hist_1month REAL,
                bb_upper_1day REAL,
                bb_middle_1day REAL,
                bb_lower_1day REAL,
                bb_upper_1week REAL,
                bb_middle_1week REAL,
                bb_lower_1week REAL,
                bb_upper_1month REAL,
                bb_middle_1month REAL,
                bb_lower_1month REAL,
                sma_55 REAL,
                sma_89 REAL,
                sma_144 REAL,
                sma_233 REAL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, date)
            )
        ''')
        
        try:
            c.execute('PRAGMA table_info(daily_indicators)')
            existingCols = [col[1] for col in c.fetchall()]
            expectedCols = ['symbol', 'date', 'rsi_1day', 'rsi_1week', 'rsi_1month',
                          'macd_1day', 'macd_signal_1day', 'macd_hist_1day',
                          'macd_1week', 'macd_signal_1week', 'macd_hist_1week',
                          'macd_1month', 'macd_signal_1month', 'macd_hist_1month',
                          'bb_upper_1day', 'bb_middle_1day', 'bb_lower_1day',
                          'bb_upper_1week', 'bb_middle_1week', 'bb_lower_1week',
                          'bb_upper_1month', 'bb_middle_1month', 'bb_lower_1month',
                          'sma_55', 'sma_89', 'sma_144', 'sma_233', 'last_updated']
            
            if len(existingCols) != 28 or set(existingCols) != set(expectedCols):
                logger.warning(f"Table schema mismatch. Existing: {len(existingCols)} cols")
                logger.warning(f"Recreating daily_indicators table")
                c.execute('DROP TABLE IF EXISTS daily_indicators')
                c.execute('''
                    CREATE TABLE daily_indicators (
                        symbol TEXT NOT NULL,
                        date DATE NOT NULL,
                        rsi_1day REAL,
                        rsi_1week REAL,
                        rsi_1month REAL,
                        macd_1day REAL,
                        macd_signal_1day REAL,
                        macd_hist_1day REAL,
                        macd_1week REAL,
                        macd_signal_1week REAL,
                        macd_hist_1week REAL,
                        macd_1month REAL,
                        macd_signal_1month REAL,
                        macd_hist_1month REAL,
                        bb_upper_1day REAL,
                        bb_middle_1day REAL,
                        bb_lower_1day REAL,
                        bb_upper_1week REAL,
                        bb_middle_1week REAL,
                        bb_lower_1week REAL,
                        bb_upper_1month REAL,
                        bb_middle_1month REAL,
                        bb_lower_1month REAL,
                        sma_55 REAL,
                        sma_89 REAL,
                        sma_144 REAL,
                        sma_233 REAL,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (symbol, date)
                    )
                ''')
                logger.info("Recreated daily_indicators table with correct schema")
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not verify table schema: {e}")
        
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
        c.execute('CREATE INDEX IF NOT EXISTS idx_daily_ind_symbol_date ON daily_indicators(symbol, date DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_earnings_symbol_date ON earnings(symbol, fiscal_date_ending DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_earnings_reported_date ON earnings(reported_date)')
        
        conn.commit()
        conn.close()


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

        dailyIndicators = {}
        
        if use_db:
            dailyIndicators = self.getDailyIndicators(symbol)
            logger.info(f"Using indicators from database for {symbol} (Daily: {len(dailyIndicators)})")
        
        indicatorSet = IndicatorSet(
            daily_rsi=dailyIndicators,
            daily_stoch_rsi={},
            daily_macd={},
            weekly_rsi={},
            weekly_macd={}
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
            indicators=indicatorSet,
            earnings=earnings_records
        )

    def parseTwelveDataBars(self, values: List[Dict]) -> List[DailyBar]:
        bars = []
        for item in values:
            dateStr = item.get('datetime', '')
            if dateStr:
                bars.append(DailyBar(
                    date=dateStr.split(' ')[0],
                    open=float(item.get('open', 0)),
                    high=float(item.get('high', 0)),
                    low=float(item.get('low', 0)),
                    close=float(item.get('close', 0)),
                    volume=int(item.get('volume', 0))
                ))
        return bars

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
    
    def storeDailyIndicators(self, symbol: str, indicatorsDf):
        """Store daily indicators from DataFrame with all timeframes, including SMAs fetched from API."""
        if indicatorsDf is None or indicatorsDf.empty:
            return
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            df = indicatorsDf.copy()
            if df.index.name == 'Date' or (isinstance(df.index, pd.DatetimeIndex) and df.index.name is None):
                df = df.reset_index()
            
            if 'Date' not in df.columns:
                logger.error(f"Date column not found in DataFrame for {symbol}. Columns: {list(df.columns)}")
                return
            
            if 'Close' not in df.columns:
                logger.error(f"Close column not found in DataFrame for {symbol}.")
                return
            
            logger.info(f"DataFrame columns for {symbol}: {list(df.columns)}")
            logger.info(f"DataFrame shape: {df.shape}")
            
            requiredCols = [
                'RSI_1day', 'RSI_1week', 'RSI_1month',
                'MACD_1day', 'MACD_Signal_1day', 'MACD_Hist_1day',
                'MACD_1week', 'MACD_Signal_1week', 'MACD_Hist_1week',
                'MACD_1month', 'MACD_Signal_1month', 'MACD_Hist_1month',
                'BB_Upper_1day', 'BB_Middle_1day', 'BB_Lower_1day',
                'BB_Upper_1week', 'BB_Middle_1week', 'BB_Lower_1week',
                'BB_Upper_1month', 'BB_Middle_1month', 'BB_Lower_1month'
            ]
            
            missingCols = []
            for col in requiredCols:
                if col not in df.columns:
                    df[col] = None
                    missingCols.append(col)
            
            if missingCols:
                logger.warning(f"Added missing columns for {symbol}: {missingCols}")
            
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            
            if 'SMA_55' not in df.columns:
                df['SMA_55'] = None
            if 'SMA_89' not in df.columns:
                df['SMA_89'] = None
            if 'SMA_144' not in df.columns:
                df['SMA_144'] = None
            if 'SMA_233' not in df.columns:
                df['SMA_233'] = None
            
            logger.info(f"After adding missing columns, DataFrame has {len(df.columns)} columns")
            
            storedCount = 0
            for _, row in df.iterrows():
                dateVal = row['Date']
                
                if pd.isna(dateVal):
                    continue
                
                if hasattr(dateVal, 'date'):
                    dateStr = str(dateVal.date())
                elif hasattr(dateVal, 'strftime'):
                    dateStr = dateVal.strftime("%Y-%m-%d")
                else:
                    dateStr = str(dateVal).split(' ')[0]
                
                def getValue(colName):
                    if colName not in row.index:
                        return None
                    val = row[colName]
                    if val is None:
                        return None
                    if isinstance(val, float) and pd.isna(val):
                        return None
                    try:
                        if isinstance(val, str) and val.lower() in ['nan', 'none', '']:
                            return None
                        return float(val) if isinstance(val, (int, float, str)) else None
                    except (ValueError, TypeError):
                        return None
                
                values = (
                    symbol, dateStr,
                    getValue('RSI_1day'),
                    getValue('RSI_1week'),
                    getValue('RSI_1month'),
                    getValue('MACD_1day'),
                    getValue('MACD_Signal_1day'),
                    getValue('MACD_Hist_1day'),
                    getValue('MACD_1week'),
                    getValue('MACD_Signal_1week'),
                    getValue('MACD_Hist_1week'),
                    getValue('MACD_1month'),
                    getValue('MACD_Signal_1month'),
                    getValue('MACD_Hist_1month'),
                    getValue('BB_Upper_1day'),
                    getValue('BB_Middle_1day'),
                    getValue('BB_Lower_1day'),
                    getValue('BB_Upper_1week'),
                    getValue('BB_Middle_1week'),
                    getValue('BB_Lower_1week'),
                    getValue('BB_Upper_1month'),
                    getValue('BB_Middle_1month'),
                    getValue('BB_Lower_1month'),
                    getValue('SMA_55'),
                    getValue('SMA_89'),
                    getValue('SMA_144'),
                    getValue('SMA_233')
                )
                
                if len(values) != 27:
                    logger.error(f"Expected 27 values, got {len(values)} for {symbol} on {dateStr}")
                    logger.error(f"Values tuple: {values}")
                    continue
                
                try:
                    sql = '''
                        INSERT OR REPLACE INTO daily_indicators
                        (symbol, date, rsi_1day, rsi_1week, rsi_1month,
                         macd_1day, macd_signal_1day, macd_hist_1day,
                         macd_1week, macd_signal_1week, macd_hist_1week,
                         macd_1month, macd_signal_1month, macd_hist_1month,
                         bb_upper_1day, bb_middle_1day, bb_lower_1day,
                         bb_upper_1week, bb_middle_1week, bb_lower_1week,
                         bb_upper_1month, bb_middle_1month, bb_lower_1month,
                         sma_55, sma_89, sma_144, sma_233)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    c.execute(sql, values)
                    storedCount += 1
                except Exception as e:
                    logger.error(f"Error inserting row for {symbol} on {dateStr}: {e}")
                    logger.error(f"SQL: {sql.strip()}")
                    logger.error(f"Values count: {len(values)}, Values: {values}")
                    logger.error(f"Row data: {dict(row)}")
                    raise
            
            conn.commit()
            logger.info(f"Stored {storedCount} daily indicator records for {symbol} (out of {len(df)} rows)")
        except Exception as e:
            logger.error(f"Error storing daily indicators for {symbol}: {e}", exc_info=True)
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
            "daily_indicators": "daily_indicators"
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
    
    def getDailyIndicators(self, symbol: str) -> Dict[str, Dict[str, Any]]:
        """Get daily indicators from database with all timeframes, including SMAs fetched from API."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute('''
                SELECT date, rsi_1day, rsi_1week, rsi_1month,
                       macd_1day, macd_signal_1day, macd_hist_1day,
                       macd_1week, macd_signal_1week, macd_hist_1week,
                       macd_1month, macd_signal_1month, macd_hist_1month,
                       bb_upper_1day, bb_middle_1day, bb_lower_1day,
                       bb_upper_1week, bb_middle_1week, bb_lower_1week,
                       bb_upper_1month, bb_middle_1month, bb_lower_1month,
                       sma_55, sma_89, sma_144, sma_233
                FROM daily_indicators
                WHERE symbol = ?
                ORDER BY date ASC
            ''', (symbol,))
            
            rows = c.fetchall()
            indicators = {}
            for row in rows:
                dateStr = row[0]
                indicators[dateStr] = {
                    "RSI_1day": row[1],
                    "RSI_1week": row[2],
                    "RSI_1month": row[3],
                    "MACD_1day": row[4],
                    "MACD_Signal_1day": row[5],
                    "MACD_Hist_1day": row[6],
                    "MACD_1week": row[7],
                    "MACD_Signal_1week": row[8],
                    "MACD_Hist_1week": row[9],
                    "MACD_1month": row[10],
                    "MACD_Signal_1month": row[11],
                    "MACD_Hist_1month": row[12],
                    "BB_Upper_1day": row[13],
                    "BB_Middle_1day": row[14],
                    "BB_Lower_1day": row[15],
                    "BB_Upper_1week": row[16],
                    "BB_Middle_1week": row[17],
                    "BB_Lower_1week": row[18],
                    "BB_Upper_1month": row[19],
                    "BB_Middle_1month": row[20],
                    "BB_Lower_1month": row[21],
                    "SMA_55": row[22],
                    "SMA_89": row[23],
                    "SMA_144": row[24],
                    "SMA_233": row[25]
                }
            return indicators
        except Exception as e:
            logger.error(f"Error getting daily indicators for {symbol}: {e}")
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
