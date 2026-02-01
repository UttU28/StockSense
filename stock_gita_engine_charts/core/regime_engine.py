class RegimeIdentificationEngine:
    def __init__(self):
        pass

    def identify_regime(self, indicators):
        """
        Determine market regime based on multi-timeframe analysis.
        """
        # 1. MA Crossover (55 vs 233)
        ma_55 = indicators['moving_averages'].get('MA_55', 0)
        ma_233 = indicators['moving_averages'].get('MA_233', 0)
        
        ma_signal = 'neutral'
        if ma_55 and ma_233:
            if ma_55 > ma_233:
                ma_signal = 'bullish'
            elif ma_55 < ma_233:
                ma_signal = 'bearish'

        # 2. Trend Strength from ADX
        dm = indicators.get('directional_movement', {})
        dm_strength = dm.get('trend_strength', 0) # ADX value
        
        # 3. Regime Logic
        # Simplified per spec:
        if dm_strength < 8: # ADX < 8 (Was 10)
             return {
                'regime': 'SIDEWAYS',
                'confidence': 0.6,
                'reason': 'Low ADX (<8) indicates sideways/chop'
            }

        # Check MACD Hist for confirmation
        macd_hist = indicators['macd'].get('histogram', 0)
        
        if ma_signal == 'bullish':
            if macd_hist > 0:
                return {'regime': 'BULLISH', 'confidence': 0.85, 'reason': '55>233 MA + Positive MACD'}
            else:
                return {'regime': 'TRANSITION', 'confidence': 0.5, 'reason': 'Bullish MA but Negative Momentum'}
        
        elif ma_signal == 'bearish':
            if macd_hist < 0:
                return {'regime': 'BEARISH', 'confidence': 0.85, 'reason': '55<233 MA + Negative MACD'}
            else:
                return {'regime': 'TRANSITION', 'confidence': 0.5, 'reason': 'Bearish MA but Positive Momentum'}

        return {'regime': 'SIDEWAYS', 'confidence': 0.4, 'reason': 'Neutral MA structure'}
