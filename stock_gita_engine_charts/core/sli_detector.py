import pandas as pd
import numpy as np

def detect_sli(df: pd.DataFrame, lookback=20):
    """
    Detects Support, Resistance, and Liquidity zones.
    """
    if df is None or len(df) < lookback:
        return {}
    
    # --- Support & Resistance (Swing Highs/Lows) ---
    # A simple swing is a high surrounded by lower highs, or low surrounded by higher lows
    # We use a window to find local min/max
    df['min_low'] = df['low'].rolling(window=5, center=True).min()
    df['max_high'] = df['high'].rolling(window=5, center=True).max()
    
    # Identify swing points from the last 'lookback' periods
    recent_df = df.iloc[-lookback:].copy()
    
    supports = recent_df[recent_df['low'] == recent_df['min_low']]['low'].tolist()
    resistances = recent_df[recent_df['high'] == recent_df['max_high']]['high'].tolist()
    
    # Filter nearby levels (clustering)
    supports = _cluster_levels(supports)
    resistances = _cluster_levels(resistances)
    
    # --- Liquidity (Fair Value Gaps - FVG) ---
    # Bullish FVG: Low of candle 1 > High of candle 3
    # Bearish FVG: High of candle 1 < Low of candle 3
    liquidity_zones = []
    
    if len(df) > 3:
        # Check last few candles for gaps
        for i in range(len(df)-3, len(df)-1):
            idx = df.index[i]
            # Bullish FVG
            if df.iloc[i-2]['high'] < df.iloc[i]['low']:
                gap_low = df.iloc[i-2]['high']
                gap_high = df.iloc[i]['low']
                if gap_high - gap_low > (df.iloc[i]['close'] * 0.001): # Min gap size
                    liquidity_zones.append(f"Bullish FVG at {gap_low:.2f}-{gap_high:.2f}")
            
            # Bearish FVG
            if df.iloc[i-2]['low'] > df.iloc[i]['high']:
                gap_high = df.iloc[i-2]['low']
                gap_low = df.iloc[i]['high']
                if gap_high - gap_low > (df.iloc[i]['close'] * 0.001):
                    liquidity_zones.append(f"Bearish FVG at {gap_low:.2f}-{gap_high:.2f}")

    return {
        "support": supports,
        "resistance": resistances,
        "liquidity": liquidity_zones
    }

def _cluster_levels(levels, threshold=0.02):
    """Clusters nearby support/resistance levels to avoid noise."""
    if not levels:
        return []
    
    levels.sort()
    clusters = []
    if levels:
        current_cluster = [levels[0]]
        
        for i in range(1, len(levels)):
            if levels[i] <= current_cluster[-1] * (1 + threshold):
                current_cluster.append(levels[i])
            else:
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [levels[i]]
        clusters.append(sum(current_cluster) / len(current_cluster))
    
    return [round(x, 2) for x in clusters]
