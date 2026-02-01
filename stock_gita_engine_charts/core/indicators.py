import pandas as pd
import pandas_ta as ta
import numpy as np

class TechnicalIndicatorCalculator:
    def __init__(self, config=None):
        self.config = config or {}
        self.ma_periods = self.config.get('moving_averages', [13, 21, 34, 55, 89, 144, 233, 377, 610, 987])

    def calculate_all_indicators(self, df: pd.DataFrame):
        """
        Calculates all technical indicators for the provided DataFrame.
        """
        if df is None or len(df) < 50:
            return None

        # Helper to safely get columns from pandas_ta
        def get_col(d, prefix, *args):
            # pandas_ta column naming can be tricky (int vs float)
            # Try constructing likely names
            # args are usually lengths/stds
            base = f"{prefix}"
            for a in args:
                base += f"_{a}"
            
            # 1. Exact match
            if base in d.columns: return d[base]
            
            # 2. Try ensuring last arg is float (common for std)
            if len(args) > 0:
                args_f = list(args)
                try:
                    args_f[-1] = float(args_f[-1])
                    base_f = f"{prefix}"
                    for a in args_f: base_f += f"_{a}"
                    if base_f in d.columns: return d[base_f]
                except: pass

            # 3. Fuzzy match (start with prefix_arg0...)
            candidates = [c for c in d.columns if c.startswith(f"{prefix}_")]
            if candidates: return d[candidates[-1]] # Return last match (usually latest calc)

            # Return empty series of zeros to avoid crash
            return d.iloc[:, 0] * 0 

        # Helper to safe get last
        def last(s):
            if isinstance(s, pd.Series) and not s.empty: return s.iloc[-1]
            return 0

        # 1. Moving Averages
        mas = {}
        for p in self.ma_periods:
            mas[f'MA_{p}'] = ta.sma(df['close'], length=p)
        
        for k, v in mas.items():
            df[k] = v

        # 2. Bollinger Bands
        bb_period = self.config.get('indicators', {}).get('bollinger_bands_period', 20)
        bb_std = self.config.get('indicators', {}).get('bollinger_bands_std_dev', 2)
        bb = ta.bbands(df['close'], length=bb_period, std=bb_std)
        if bb is None: bb = pd.DataFrame()
        
        bb_data = {
            'upper_band': get_col(bb, 'BBU', bb_period, bb_std),
            'middle_band': get_col(bb, 'BBM', bb_period, bb_std),
            'lower_band': get_col(bb, 'BBL', bb_period, bb_std),
            'width': get_col(bb, 'BBB', bb_period, bb_std),
            'position': get_col(bb, 'BBP', bb_period, bb_std)
        }

        # 3. RSI
        rsi_period = self.config.get('indicators', {}).get('rsi_period', 14)
        rsi = ta.rsi(df['close'], length=rsi_period)

        # 4. MACD
        fast = self.config.get('indicators', {}).get('macd_fast', 12)
        slow = self.config.get('indicators', {}).get('macd_slow', 26)
        signal = self.config.get('indicators', {}).get('macd_signal', 9)
        macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
        if macd is None: macd = pd.DataFrame()

        macd_data = {
            'macd_line': get_col(macd, 'MACD', fast, slow, signal),
            'signal_line': get_col(macd, 'MACDs', fast, slow, signal),
            'histogram': get_col(macd, 'MACDh', fast, slow, signal)
        }
        
        hist = macd_data['histogram']
        expanding = False
        if len(hist) > 1:
            val_now = hist.iloc[-1]
            val_prev = hist.iloc[-2]
            if pd.notna(val_now) and pd.notna(val_prev):
                expanding = abs(val_now) > abs(val_prev)
        macd_data['histogram_expanding'] = expanding

        # 5. Smoothed RSI (Stochastic RSI)
        srsi_period = self.config.get('indicators', {}).get('srsi_period', 14)
        k = self.config.get('indicators', {}).get('srsi_smooth_k', 3)
        d = self.config.get('indicators', {}).get('srsi_smooth_d', 3)
        stochrsi = ta.stochrsi(df['close'], length=srsi_period, rsi_length=srsi_period, k=k, d=d)
        if stochrsi is None: stochrsi = pd.DataFrame()
        
        srsi_data = {
            'srsi_k': get_col(stochrsi, 'STOCHRSIk', srsi_period, srsi_period, k, d),
            'srsi_d': get_col(stochrsi, 'STOCHRSId', srsi_period, srsi_period, k, d),
        }
        srsi_val = srsi_data['srsi_k'].iloc[-1] if not srsi_data['srsi_k'].empty else 50
        srsi_data['extreme'] = srsi_val > 80 or srsi_val < 20
        srsi_data['srsi_value'] = srsi_val

        # 6. Directional Movement (ADX)
        dm_period = self.config.get('indicators', {}).get('dm_period', 14)
        adx = ta.adx(df['high'], df['low'], df['close'], length=dm_period)
        if adx is None: adx = pd.DataFrame()
        
        dm_data = {
            'di_plus': get_col(adx, 'DMP', dm_period),
            'di_minus': get_col(adx, 'DMN', dm_period),
            'adx': get_col(adx, 'ADX', dm_period),
        }
        dm_data['trend_strength'] = dm_data['adx'].iloc[-1] if not dm_data['adx'].empty else 0

        # 7. AutoWaves (Custom)
        aw_data = self._detect_autowaves(df)

        # 8. Tweezers (Custom)
        tweezers_data = self._detect_tweezers(df)

        # 9. Simple Trend Determination
        # Logic: Price > SMA50 ? Bullish
        # Secondary: SMA21 > SMA50 ? Bullish
        
        current_close = df['close'].iloc[-1]
        sma21 = mas.get('MA_21').iloc[-1] if 'MA_21' in mas else 0
        sma50 = mas.get('MA_55').iloc[-1] if 'MA_55' in mas else 0 # Using 55 from standard set
        
        trend_status = "NEUTRAL"
        if current_close > sma50:
            if current_close > sma21: trend_status = "BULLISH"
            else: trend_status = "WEAK_BULLISH"
        else:
            if current_close < sma21: trend_status = "BEARISH"
            else: trend_status = "WEAK_BEARISH"

        # 10. Strict Trend Check (for Weekly/Monthly usage)
        # Prompt: Weekly RSI > 50 AND MACD > 0 -> Positive Trend
        macd_val = macd_data.get('macd_line', 0)
        if isinstance(macd_val, pd.Series): macd_val = macd_val.iloc[-1]
        
        rsi_val = last(rsi)
        
        strict_trend = "NEUTRAL"
        if rsi_val > 50 and macd_val > 0:
            strict_trend = "POSITIVE"
        elif rsi_val < 50 or macd_val < 0:
            strict_trend = "NEGATIVE"
            
        # Helper to safe get last
        def last(s):
            if isinstance(s, pd.Series) and not s.empty: return s.iloc[-1]
            return 0

        # Extract last values
        return {
            'trend': trend_status,
            'strict_trend': strict_trend,
            'moving_averages': {k: last(v) for k, v in mas.items()},
            'bollinger_bands': {k: last(v) for k, v in bb_data.items()},
            'rsi': last(rsi),
            'macd': {k: last(v) if isinstance(v, pd.Series) else v for k, v in macd_data.items()},
            'srsi': srsi_data,
            'directional_movement': dm_data,
            'autowaves': aw_data,
            'tweezers': tweezers_data
        }

    def resample_data(self, df: pd.DataFrame, period='3D'):
        """
        Resamples Daily OHLC data to custom timeframes (e.g., 3D, 8D).
        """
        if df is None or df.empty:
            return None
            
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df = df.copy()
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            else:
                return df # Cannot resample without date
                
        # Resample Logic
        logic = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        # Handle custom strings like '3D', '8D'
        resampled = df.resample(period).agg(logic)
        resampled.dropna(inplace=True)
        
        return resampled

    # ... keeping _detect_autowaves and _detect_tweezers as is for now ...
    def _detect_autowaves(self, df):
        """
        Detects AutoWave Structure (Market Structure).
        Finds the most recent 'Line 2' (Significant Swing High/Low).
        """
        if len(df) < 20:
             return {'wave_type': 'none', 'line_2_level': None}
             
        # Find Swing Points (Fractals) - Window 5
        # We need the LAST significant swing point.
        highs = df['high'].values
        lows = df['low'].values
        
        # Simple Pivot Detection (High > 2 neighbors on each side)
        def is_pivot_high(idx):
            return highs[idx] > highs[idx-1] and highs[idx] > highs[idx-2] and \
                   highs[idx] > highs[idx+1] and highs[idx] > highs[idx+2]

        def is_pivot_low(idx):
            return lows[idx] < lows[idx-1] and lows[idx] < lows[idx-2] and \
                   lows[idx] < lows[idx+1] and lows[idx] < lows[idx+2]
                   
        # Scan backwards from 3rd last candle (to ensure right neighbors exist)
        last_high = None
        last_low = None
        
        for i in range(len(df)-3, 2, -1):
            if last_high is None and is_pivot_high(i):
                last_high = highs[i]
            if last_low is None and is_pivot_low(i):
                last_low = lows[i]
            
            if last_high and last_low:
                break
                
        # Determine current structure
        current_close = df['close'].iloc[-1]
        
        # If Price < Last Pivot High -> Potential Down Wave
        # If Price > Last Pivot Low -> Potential Up Wave
        
        wave_type = 'NEUTRAL'
        line_2 = 0
        
        if last_high and current_close < last_high:
            wave_type = 'DOWN'
            line_2 = last_high
        elif last_low and current_close > last_low:
            wave_type = 'UP'
            line_2 = last_low
            
        return {
            'wave_type': wave_type,
            'wave_strength': 1 if line_2 else 0,
            'line_2_level': line_2
        }

    def _detect_tweezers(self, df):
        """
        Detect Tweezer Top/Bottom patterns.
        """
        if len(df) < 2:
            return {'tweezer_type': 'none'}
            
        h = df['high'].values
        l = df['low'].values
        c = df['close'].values
        
        # Tolerance: 0.05% difference allowed
        tol = c[-1] * 0.0005
        
        # Tweezer Top: Highs align
        if abs(h[-1] - h[-2]) < tol:
             return {'tweezer_type': 'TOP', 'tweezer_strength': 1.0}
        
        # Tweezer Bottom: Lows align
        if abs(l[-1] - l[-2]) < tol:
             return {'tweezer_type': 'BOTTOM', 'tweezer_strength': 1.0}
             
        return {'tweezer_type': 'none', 'tweezer_strength': 0}
