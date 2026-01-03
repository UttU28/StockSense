from typing import Dict, Any, Tuple

class PositionSizer:
    def __init__(self, account_size: float = 10000.0, risk_per_trade: float = 0.01):
        self.account_size = account_size
        self.risk_per_trade = risk_per_trade

    def calculate_position(self, 
                         entry_price: float, 
                         stop_loss: float, 
                         confidence: float,
                         bias: str = "BULLISH",
                         structural_lvl: float = None) -> Dict[str, Any]:
        """
        Calculate position size based on risk and confidence scaling.
        Rule: Base Unit = (Account * Risk) / Stop Distance
        """
        if entry_price <= 0 or stop_loss <= 0:
             return {"units": 0, "risk_amount": 0, "note": "Invalid entry/stop"}

        stop_source = "ATR"
        final_stop = stop_loss

        # Structural Stop Logic
        if structural_lvl:
            if bias == "BULLISH" and structural_lvl < entry_price:
                 # Buffer: 0.2% below support
                 struct_stop = structural_lvl * 0.998
                 # Sanity Check: Don't use if it risks < 0.5% (too tight) or > 15% (too wide)
                 risk_pct = (entry_price - struct_stop) / entry_price
                 if 0.005 < risk_pct < 0.15:
                     final_stop = struct_stop
                     stop_source = "STRUCTURE"
            elif bias == "BEARISH" and structural_lvl > entry_price:
                 struct_stop = structural_lvl * 1.002
                 risk_pct = (struct_stop - entry_price) / entry_price
                 if 0.005 < risk_pct < 0.15:
                     final_stop = struct_stop
                     stop_source = "STRUCTURE"

        stop_distance = abs(entry_price - final_stop)
        if stop_distance == 0:
             return {"units": 0, "note": "Stop equals entry"}

        # Calculate Targets
        if bias == "BEARISH":
            tp_1r = entry_price - (1 * stop_distance)
            tp1 = entry_price - (2 * stop_distance)
            tp2 = entry_price - (3 * stop_distance)
        else:
            tp_1r = entry_price + (1 * stop_distance)
            tp1 = entry_price + (2 * stop_distance)
            tp2 = entry_price + (3 * stop_distance)

        dollar_risk = self.account_size * self.risk_per_trade # 1% of account
        
        # Base units (how many shares to lose exactly 1% if stopped out)
        # Formula: Units * Distance = Dollar_Risk  => Units = Dollar_Risk / Distance
        base_units = dollar_risk / stop_distance
        
        # Scale by confidence
        scaling_factor = 0.0
        if confidence >= 90: scaling_factor = 2.5
        elif confidence >= 75: scaling_factor = 2.0
        elif confidence >= 65: scaling_factor = 1.5
        elif confidence >= 60: scaling_factor = 1.0 # Base size for standard entry
        else: scaling_factor = 0.0 # Skip trade
        
        final_units = int(base_units * scaling_factor)
        
        # Cap max position value (Optional - e.g. max 25% of account in one stock)
        max_allocation = self.account_size * 0.25 
        if (final_units * entry_price) > max_allocation:
             final_units = int(max_allocation / entry_price)
             scaling_factor = -1 # Flag that it was capped
        
        return {
            "units": final_units,
            "entry": entry_price,
            "stop": round(final_stop, 2),
            "stop_source": stop_source,
            "take_profit_1r": round(tp_1r, 2),
            "take_profit_1": round(tp1, 2),
            "take_profit_2": round(tp2, 2),
            "risk_amount": round(dollar_risk, 2),
            "scaling_factor": scaling_factor,
            "total_exposure": round(final_units * entry_price, 2)
        }

class ExitManager:
    def evaluate_exits(self, current_price: float, entry_price: float, indicators: Dict[str, Any]) -> str:
        """
        Simple checker for exit conditions.
        Returns: HOLD, TRIM, EXIT
        """
        rsi = indicators.get("daily_rsi", 50)
        regime = indicators.get("daily_macd_regime", "NEUTRAL")
        
        if rsi >= 80:
            return "TRIM (RSI Overbought)"
        
        # Divergence logic would go here (requires history)
        
        # Trend break check (price closes below 50MA if we had access to it here)
        # For now, just RSI and MACD check
        if regime == "BEARISH":
             return "EXIT (Trend Break / Bearish MACD)"
             
        if current_price < entry_price * 0.95: # Hard 5% trailing stop thought
             return "EXIT (Stop Hit)"
             
        return "HOLD"
