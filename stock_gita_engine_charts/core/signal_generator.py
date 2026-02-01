from datetime import datetime

class TradeSignalGenerator:
    def __init__(self):
        pass

    def generate_signal(self, symbol, confidence_data, regime_data, indicators):
        """
        Generate actionable trade signal with entry/exit/risk parameters.
        """
        if not confidence_data['is_approved']:
            return {
                'signal_generated': False,
                'reason': f"Confidence too low ({confidence_data['final_confidence']}%)",
                'confidence': confidence_data['final_confidence'],
                'direction': 'WAIT'
            }

        regime = regime_data['regime']
        direction = 'NEUTRAL'
        
        if regime == 'BULLISH':
            direction = 'LONG'
        elif regime == 'BEARISH':
            direction = 'SHORT'
        else:
            return {
                'signal_generated': False,
                'reason': f"Regime {regime} not suitable for trade",
                'confidence': confidence_data['final_confidence'],
                'direction': 'WAIT'
            }

        # Entry Range (Using BB)
        bb = indicators['bollinger_bands']
        middle = bb.get('middle_band', 0)
        
        if direction == 'LONG':
            entry_low = bb.get('lower_band', 0)
            entry_high = middle
        else:
            entry_low = middle
            entry_high = bb.get('upper_band', 0)
            
        entry_price = (entry_low + entry_high) / 2
        
        # Risk Management (ATR Based)
        atr = bb.get('width', 0) / 4 
        
        if direction == 'LONG':
            stop_loss = entry_low - atr
            tp1 = entry_price + (entry_price - stop_loss) * 1.5
            tp2 = entry_price + (entry_price - stop_loss) * 3.0
        else:
            stop_loss = entry_high + atr
            tp1 = entry_price - (stop_loss - entry_price) * 1.5
            tp2 = entry_price - (stop_loss - entry_price) * 3.0

        # Momentum Alert Check
        momentum_active = self._check_momentum_alert(indicators)
            
        return {
            'signal_generated': True,
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence_data['final_confidence'],
            'momentum_alert': momentum_active,
            'timestamp': datetime.utcnow().isoformat(),
            'entry': {
                'range_low': entry_low,
                'range_high': entry_high,
                'ideal_price': entry_price
            },
            'exit': {
                'take_profit_1': tp1,
                'take_profit_2': tp2,
                'stop_loss': stop_loss
            },
            'risk_metrics': {
                'risk_reward_ratio': 1.5,
                'volatility_atr': atr
            }
        }

    def _check_momentum_alert(self, indicators):
        """
        Checks for Momentum Burst (1-3 bars).
        Triggers: RSI > 70/ < 30 approach, MACD expanding, ADX > 25.
        """
        triggers = 0
        
        # 1. RSI Extreme/Rapid
        rsi = indicators.get('rsi', 50)
        if rsi > 65 or rsi < 35: 
            triggers += 1
            
        # 2. MACD Expansion
        macd = indicators.get('macd', {})
        if macd.get('histogram_expanding'):
            triggers += 1
            
        # 3. ADX Trend
        dm = indicators.get('directional_movement', {})
        if dm.get('trend_strength', 0) > 25:
            triggers += 1
            
        return triggers >= 2
