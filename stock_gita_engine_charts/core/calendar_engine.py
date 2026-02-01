from datetime import datetime
import json
from ..db.database import get_db_connection

class CalendarProcessingEngine:
    def __init__(self):
        pass
    
    def _get_year_profile(self, year):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM year_behavior WHERE year = ?", (year,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    def _get_current_season(self, date_obj):
        conn = get_db_connection()
        c = conn.cursor()
        date_str = date_obj.strftime("%Y-%m-%d")
        year = date_obj.year
        
        # Find zone where current date falls between start and end
        c.execute("""
            SELECT * FROM seasonal_zones 
            WHERE year = ? AND start_date <= ? AND end_date >= ?
        """, (year, date_str, date_str))
        
        row = c.fetchone()
        conn.close()
        if row:
            data = dict(row)
            # Parse JSON fields
            if data.get('key_events'):
                data['key_events'] = json.loads(data['key_events'])
            return data
        return None

    def _check_expansion_window(self, date_obj):
        conn = get_db_connection()
        c = conn.cursor()
        date_str = date_obj.strftime("%Y-%m-%d")
        year = date_obj.year
        
        # Check if date is inside a registered expansion window
        c.execute("""
            SELECT * FROM stock_gita_windows
            WHERE year = ? AND expansion_start <= ? AND expansion_end >= ?
        """, (year, date_str, date_str))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "active": True,
                "window": dict(row)
            }
        return {"active": False}

    def _get_monthly_pattern(self, symbol, date_obj):
        conn = get_db_connection()
        c = conn.cursor()
        month_name = date_obj.strftime("%B").lower()
        year = date_obj.year
        
        c.execute("""
            SELECT * FROM monthly_patterns 
            WHERE year = ? AND symbol = ? AND month_name = ?
        """, (year, symbol, month_name))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            data = dict(row)
            # Parse JSON fields
            if data.get('typical_entry_zones'):
                 data['typical_entry_zones'] = json.loads(data['typical_entry_zones'])
            if data.get('typical_profit_taking'):
                 data['typical_profit_taking'] = json.loads(data['typical_profit_taking'])
            return data
        return None

    def _check_earnings_sensitivity(self, symbol, date_obj):
        conn = get_db_connection()
        c = conn.cursor()
        
        # Look for earnings within +/- 5 days
        # This is a simplified SQL check; proper date math usually done in Python or DB functions
        # For SQLite simplicity, we just fetch all earnings for the symbol/year and check in Python
        c.execute("""
            SELECT * FROM earnings_calendar 
            WHERE symbol = ? AND year = ?
        """, (symbol, date_obj.year))
        
        rows = c.fetchall()
        conn.close()
        
        for row in rows:
            earnings_date = datetime.strptime(row['earnings_date'], "%Y-%m-%d").date()
            delta = abs((date_obj.date() - earnings_date).days)
            if delta <= 5:
                return {
                    "is_sensitive": True,
                    "earnings_date": row['earnings_date'],
                    "days_diff": delta
                }
        
        return {"is_sensitive": False}

    def _check_year_digit_bias(self, year):
        """
        Returns bias based on the last digit of the year.
        Standard Decennial Cycle Theory.
        """
        digit = year % 10
        # Simple lore map
        # 5: Strong Bullish, 8: Bullish, 0: Bearish/Crisis, 7: Crash/Volatile
        bias_map = {
            0: "BEARISH_TRANSITION",
            1: "NEUTRAL_BEARISH",
            2: "BEARISH_BOTTOM",
            3: "BULLISH_START",
            4: "NEUTRAL_CHOP",
            5: "STRONG_BULLISH",
            6: "BULLISH",
            7: "VOLATILE_CRASH_RISK",
            8: "BULLISH",
            9: "BULLISH_EXTENDED"
        }
        return bias_map.get(digit, "NEUTRAL")

    def _check_stock_memory(self, symbol, month):
        """
        Checks historical monthly probability for specific tickers.
        Hardcoded knowledge base for key assets.
        """
        # 1=Jan, 12=Dec
        memory = {
            'NVDA': {
                'bullish_months': [1, 2, 5, 10, 11],
                'bearish_months': [4, 9]
            },
            'AAPL': {
                'bullish_months': [4, 7, 8, 10, 11, 12],
                'bearish_months': [1, 2, 5, 9]
            },
            'TSLA': {
                'bullish_months': [1, 6, 11, 12],
                'bearish_months': [2, 3, 5, 9]
            },
            'MSFT': {
                'bullish_months': [4, 7, 10, 11, 12],
                'bearish_months': [3, 9]
            }
        }
        
        sym_data = memory.get(symbol.upper())
        if not sym_data:
            return "NEUTRAL"
            
        if month in sym_data['bullish_months']:
            return "BULLISH_SEASONALITY"
        if month in sym_data['bearish_months']:
            return "BEARISH_SEASONALITY"
            
        return "NEUTRAL"

    def phase_0_scan(self, symbol, date_str=None):
        """
        Execute Phase 0: Calendar-First Scan
        """
        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            date_obj = datetime.utcnow()

        results = {}
        
        # 1. Year Profile
        results['year_profile'] = self._get_year_profile(date_obj.year)
        results['year_digit_bias'] = self._check_year_digit_bias(date_obj.year)
        
        # 2. Seasonal Zone
        results['current_season'] = self._get_current_season(date_obj)
        
        # 3. Expansion Window
        results['expansion_window'] = self._check_expansion_window(date_obj)
        
        # 4. Monthly Pattern & Stock Memory
        results['monthly_pattern'] = self._get_monthly_pattern(symbol, date_obj)
        results['stock_memory'] = self._check_stock_memory(symbol, date_obj.month)
        
        # 5. Earnings Check
        results['earnings_check'] = self._check_earnings_sensitivity(symbol, date_obj)
        
        # Overall Phase 0 Status logic
        # Pass if: Expansion Active OR (Season Good AND No Earnings Risk)
        
        is_expansion = results['expansion_window']['active']
        is_risky_earnings = results['earnings_check']['is_sensitive']
        
        status = "PASSED"
        note = "Normal conditions."
        
        if is_risky_earnings:
            status = "WARNING"
            note = "Earnings risk detected."
        elif results['stock_memory'] == "BEARISH_SEASONALITY":
            status = "CAUTION"
            note = f"Historically weak month for {symbol}."
        elif not is_expansion:
             # Just a basic pass if no major risks, but maybe 'NEUTRAL'
             status = "PASSED" 
             
        results['phase_status'] = status
        results['note'] = note
        
        return results
