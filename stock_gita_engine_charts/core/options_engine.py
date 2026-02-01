class OptionsExecutionEngine:
    def __init__(self):
        self.dte_ranges = {
            'momentum': (7, 14),
            'swing': (21, 45)
        }

    def generate_options_trade(self, signal, indicators):
        """
        Generate options execution parameters.
        """
        if not signal.get('signal_generated'):
            return None
            
        direction = signal['direction']
        confidence = signal['confidence']
        
        # Determine DTE based on Momentum
        # If ADX > 25, use Momentum DTE
        adx = indicators['directional_movement'].get('trend_strength', 0)
        is_momentum = adx > 25
        
        dte_range = self.dte_ranges['momentum'] if is_momentum else self.dte_ranges['swing']
        
        # Strike Selection (Modified for AutoWave Logic)
        current_price = signal['entry']['ideal_price']
        
        # Check for AutoWave Line 2
        aw = indicators.get('autowaves', {})
        line_2 = aw.get('line_2_level')
        
        target_source = "AutoWave Line 2"
        
        if line_2 and line_2 > 0:
            # Use Line 2 as the structural target
            strike_target = line_2
        else:
            # Fallback
            target_source = "Standard ATM/OTM"
            if direction == 'LONG':
                strike_target = current_price * 1.02 # Slightly OTM
            else:
                strike_target = current_price * 0.98 # Slightly OTM
                
        # Adjust for Call/Put direction vs Target
        # E.g. If Long Call, Target should be above. If Target below (e.g. support), use price.
        if direction == 'LONG' and strike_target < current_price:
             strike_target = current_price * 1.02 # Reset if Line 2 was a support level
             target_source = "Standard (Line 2 invalid for Call)"
        elif direction == 'SHORT' and strike_target > current_price:
             strike_target = current_price * 0.98
             target_source = "Standard (Line 2 invalid for Put)"
                
        return {
            'options_enabled': True,
            'strategy': f"Buy {option_type}", # Simple long option for now
            'option_type': option_type,
            'dte_range': dte_range,
            'strike_target': strike_target,
            'rationale': f"{'Momentum' if is_momentum else 'Swing'} trade structure selected"
        }
