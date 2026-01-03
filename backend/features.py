from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
import numpy as np
from models import SymbolState, EarningsRecord, WeeklyBar, DailyBar

class FeatureEngineer:
    def compute_features(self, state: SymbolState) -> Dict[str, Any]:
        """Compute all features for the valid symbol state."""
        features = {}
        
        # 1. Date Features
        features["current_date"] = state.last_updated
        
        # 2. Earnings Features
        features.update(self._compute_earnings_features(state.earnings))
        
        # 3. Technical Features (Daily)
        latest_date = state.daily_bars[0].date if state.daily_bars else None
        if latest_date:
            # RSI
            rsi_val = state.indicators.daily_rsi.get(latest_date)
            if rsi_val is not None:
                features["daily_rsi"] = rsi_val
                features["daily_rsi_zone"] = self._get_rsi_zone(rsi_val)
            
            # MACD (Calculate Locally due to API Premium Limit)
            daily_bars_sorted = sorted(state.daily_bars, key=lambda x: x.date, reverse=False) # Oldest first
            if len(daily_bars_sorted) > 35:
                macd_vals = self._calculate_macd_from_bars(daily_bars_sorted)
                if macd_vals:
                    features["daily_macd_regime"] = self._get_macd_regime(macd_vals)
                    features["daily_macd_line"] = macd_vals.get("MACD")
                    features["daily_macd_signal"] = macd_vals.get("MACD_Signal")
                    features["daily_macd_hist"] = macd_vals.get("MACD_Hist")

            # StochRSI
            stoch_vals = state.indicators.daily_stoch_rsi.get(latest_date)
            if stoch_vals:
                features["daily_stoch_k"] = stoch_vals.get("FastK")
                features["daily_stoch_d"] = stoch_vals.get("FastD")
            
            # Candle Patterns
            features.update(self._compute_candle_features(state.daily_bars))
            
            # Structure (SMAs) & ATR
            features.update(self._compute_structure_and_volatility(state.daily_bars, state.weekly_bars))
            
            # Key Levels
            features.update(self._compute_supply_demand_levels(state.daily_bars))

        # 4. Technical Features (Weekly)
        # We need to find the latest available weekly data point
        latest_week = state.weekly_bars[0].date if state.weekly_bars else None
        if latest_week:
            rsi_w_val = state.indicators.weekly_rsi.get(latest_week)
            if rsi_w_val is not None:
                features["weekly_rsi"] = rsi_w_val
            
            # Weekly MACD Local Calc
            weekly_bars_sorted = sorted(state.weekly_bars, key=lambda x: x.date, reverse=False)
            macd_w_vals = self._calculate_macd_from_bars(weekly_bars_sorted)
            
            if macd_w_vals:
                 features["weekly_macd_regime"] = self._get_macd_regime(macd_w_vals)

        state.features = features
        return features

    def _calculate_macd_from_bars(self, bars: List[Any]) -> Dict[str, float]:
        """Calculate MACD (12, 26, 9) on the fly using pandas."""
        try:
            # Expect bars sorted ASCENDING by date
            df = pd.DataFrame([vars(b) for b in bars])
            close = df['close']
            
            exp12 = close.ewm(span=12, adjust=False).mean()
            exp26 = close.ewm(span=26, adjust=False).mean()
            macd = exp12 - exp26
            signal = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal
            
            # Get last value
            return {
                "MACD": macd.iloc[-1],
                "MACD_Signal": signal.iloc[-1],
                "MACD_Hist": hist.iloc[-1]
            }
        except Exception as e:
            return {}

    def _get_rsi_zone(self, value: float) -> str:
        if value < 20: return "EXTREME_OVERSOLD"
        if 20 <= value < 30: return "DEEP_RESET"
        if 30 <= value < 45: return "CLEAN_ENTRY"
        if 45 <= value < 50: return "NEUTRAL"
        if 50 <= value < 70: return "RISING"
        if 70 <= value < 80: return "EXTENDED"
        return "EXTREME_OVERBOUGHT"

    def _get_macd_regime(self, values: Dict[str, float]) -> str:
        macd = values.get("MACD")
        if macd is None: return "UNKNOWN"
        if macd > 0.1: return "BULLISH" # Threshold can be tuned
        if macd < -0.1: return "BEARISH"
        return "NEUTRAL"

    def _compute_earnings_features(self, earnings: List[EarningsRecord]) -> Dict[str, Any]:
        """Find days to next earnings."""
        if not earnings:
            return {"days_to_earnings": None, "earnings_status": "NONE"}
        
        today = datetime.now()
        upcoming = []
        
        for e in earnings:
            if not e.reported_date: continue
            try:
                r_date = datetime.strptime(e.reported_date, "%Y-%m-%d")
                if r_date > today:
                    upcoming.append(r_date)
            except ValueError:
                continue
                
        if not upcoming:
            return {"days_to_earnings": 999, "earnings_status": "UNKNOWN"}

        next_date = min(upcoming)
        days = (next_date - today).days
        
        status = "NONE"
        if days <= 5: status = "UPCOMING_5"
        elif days <= 10: status = "UPCOMING_5_10"
        elif days <= 21: status = "UPCOMING_10_21"
        
        return {"days_to_earnings": days, "earnings_status": status}

    def _compute_candle_features(self, bars: List[DailyBar]) -> Dict[str, Any]:
        """Detect Tweezers, Hammers, etc."""
        if len(bars) < 3:
            return {}
            
        today = bars[0]
        yesterday = bars[1]
        
        is_tweezer_bottom = False
        # Tweezer Bottom: Consecutive lows nearly equal, second candle closes strong (green or high in range)
        # "Nearly equal" = within small tolerance (e.g. 0.1% of price)
        tolerance = today.low * 0.001
        if abs(today.low - yesterday.low) < tolerance:
            # Check if today closed strong (upper half of range)
            range_len = today.high - today.low
            if range_len > 0 and (today.close - today.low) / range_len > 0.5:
                 is_tweezer_bottom = True

        # Hammer: Small body near top of range, long lower shadow (2x body)
        is_hammer = False
        body = abs(today.open - today.close)
        lower_shadow = min(today.open, today.close) - today.low
        total_range = today.high - today.low
        # Hammer criteria: Lower shadow >= 2*body, Close in upper 25% of range
        if total_range > 0 and lower_shadow >= 2 * body:
             # Check if close is near high
             if (today.high - max(today.open, today.close)) < 0.2 * total_range: 
                 is_hammer = True
                 
        return {
            "is_tweezer_bottom": is_tweezer_bottom,
            "is_hammer": is_hammer
        }

    def _compute_structure_and_volatility(self, daily_bars: List[DailyBar], weekly_bars: List[WeeklyBar]) -> Dict[str, Any]:
        """
        Compute ATR from Daily data.
        Compute Structure (Long trend) from Weekly data (40-week SMA ~ 200-day SMA).
        Compute Short trend (50-day SMA proxy -> 10-week SMA).
        """
        result = {"structure_score": "UNKNOWN", "atr_14": 0, "sma_50": 0, "sma_200": 0}
        
        # 1. ATR (Daily)
        if len(daily_bars) >= 15:
            try:
                # DF sorted ascending
                df_d = pd.DataFrame([vars(b) for b in daily_bars])
                df_d['date'] = pd.to_datetime(df_d['date'])
                df_d = df_d.sort_values('date')
                
                high = df_d['high']
                low = df_d['low']
                close = df_d['close']
                prev_close = close.shift(1)
                tr1 = high - low
                tr2 = (high - prev_close).abs()
                tr3 = (low - prev_close).abs()
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                result["atr_14"] = tr.rolling(window=14).mean().iloc[-1]
            except Exception as e:
                print(f"ATR Calc Failed: {e}")

        # 2. Structure (Weekly)
        # 10-week SMA ~ 50-day SMA
        # 40-week SMA ~ 200-day SMA
        if len(weekly_bars) >= 40:
            try:
                df_w = pd.DataFrame([vars(b) for b in weekly_bars])
                df_w['date'] = pd.to_datetime(df_w['date'])
                df_w = df_w.sort_values('date')
                
                close_w = df_w['close']
                sma10_w = close_w.rolling(window=10).mean().iloc[-1]
                sma40_w = close_w.rolling(window=40).mean().iloc[-1]
                current_price = close_w.iloc[-1]
                
                # Update result with proxies
                result["sma_50"] = sma10_w # Proxy
                result["sma_200"] = sma40_w # Proxy
                
                if current_price > sma10_w and sma10_w > sma40_w:
                    result["structure_score"] = "HIGH"
                elif current_price < sma10_w and sma10_w < sma40_w:
                    result["structure_score"] = "LOW"
                else:
                    result["structure_score"] = "NEUTRAL"
            except Exception as e:
                print(f"Structure Calc Failed: {e}")
                
        return result

    def _compute_supply_demand_levels(self, bars: List[DailyBar]) -> Dict[str, Any]:
        """
        Identify Key Levels (Support/Resistance) using Swing Highs/Lows.
        Look back ~60 days.
        """
        if len(bars) < 20:
             return {"nearest_support": None, "nearest_resistance": None}
             
        # Use last 60 bars max, oldest to newest
        bars_sorted = sorted(bars, key=lambda x: x.date, reverse=False)
        subset = bars_sorted[-60:]
        
        swings = [] # List of (price, type='high'|'low')
        
        # Simple Fractal: High > 2 left, > 2 right
        for i in range(2, len(subset) - 2):
            curr = subset[i]
            prev1 = subset[i-1]; prev2 = subset[i-2]
            next1 = subset[i+1]; next2 = subset[i+2]
            
            # Swing High
            if curr.high > prev1.high and curr.high > prev2.high and \
               curr.high > next1.high and curr.high > next2.high:
                   swings.append((curr.high, 'RESISTANCE'))
                   
            # Swing Low
            if curr.low < prev1.low and curr.low < prev2.low and \
               curr.low < next1.low and curr.low < next2.low:
                   swings.append((curr.low, 'SUPPORT'))
                   
        if not swings:
             return {"nearest_support": None, "nearest_resistance": None}
             
        current_price = bars_sorted[-1].close
        
        # Find nearest Support (Below price)
        # Filter for 'SUPPORT' swings below current price
        # Sort by distance to price (descending price, less than current)
        supports = [p for p, t in swings if t == 'SUPPORT' and p < current_price]
        nearest_support = max(supports) if supports else None
        
        # Find nearest Resistance (Above price)
        resistances = [p for p, t in swings if t == 'RESISTANCE' and p > current_price]
        nearest_resistance = min(resistances) if resistances else None
        
        return {
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance
        }
