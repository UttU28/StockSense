from typing import Dict, List

def check_sli_governance(current_price: float, sli_zones: Dict[str, List[float]], direction: str, tolerance_pct: float = 0.02) -> Dict:
    """
    Enforces the SLI Hard Gate.
    Trade is PERMITTED only if price is within 'tolerance_pct' of a key level.
    """
    if not sli_zones:
        return {'passed': False, 'reason': 'No SLI Zones detected'}
        
    levels = []
    if direction == 'LONG':
        # For Long, we want to be near Support (Dip Buy) or just broke Resistance (Breakout)
        # Simplified: Must be near Support.
        levels = sli_zones.get('support', [])
    elif direction == 'SHORT':
        # For Short, near Resistance.
        levels = sli_zones.get('resistance', [])
        
    if not levels:
         return {'passed': False, 'reason': f'No {direction} levels found'}
         
    # Check proximity
    nearest_dist = float('inf')
    nearest_level = 0
    
    for level in levels:
        dist = abs(current_price - level) / current_price
        if dist < nearest_dist:
            nearest_dist = dist
            nearest_level = level
            
    if nearest_dist <= tolerance_pct:
        return {
            'passed': True, 
            'level': nearest_level, 
            'distance_pct': round(nearest_dist * 100, 2)
        }
        
    return {
        'passed': False,
        'reason': f"Price not at level. Nearest: {nearest_level} (Dist: {round(nearest_dist*100, 2)}% > {tolerance_pct*100}%)"
    }

def check_timeframe_alignment(timeframes: Dict) -> Dict:
    """
    Enforces Multi-Timeframe Validation.
    Weekly Trend must support Daily Signal.
    """
    daily_trend = timeframes.get('DAILY', {}).get('trend', 'NEUTRAL')
    weekly_trend = timeframes.get('WEEKLY', {}).get('trend', 'NEUTRAL')
    
    # Strict alignment
    if daily_trend == weekly_trend and daily_trend in ['BULLISH', 'BEARISH']:
        return {'passed': True, 'trend': daily_trend}
        
    return {
        'passed': False,
        'reason': f"Timeframe Mismatch: Daily {daily_trend} vs Weekly {weekly_trend}"
    }
