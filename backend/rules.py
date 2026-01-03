from typing import Dict, Any, List
from models import SymbolState

class RulesEngine:
    def run_rules(self, state: SymbolState):
        """Run all active rule trees and update state."""
        state.bias = self._tree_a_bias(state)
        # Tree B (Alert) - integrated slightly differently in Phase 2 context? 
        # Plan says "evaluate_alert". Let's keep it consistent.
        state.alerts = self._tree_b_alert(state)
        
        # New Trees
        state.regime = self._tree_c_regime(state)
        
        # Entry requires Bias and Alert inputs
        bias_val = state.bias.get("bias", "NEUTRAL")
        alert_on = state.alerts.get("alert_on", False)
        
        # Tree D returns a dict we can put in 'plan' or separate field
        entry_result = self._tree_d_entry(state, bias_val, alert_on)
        
        # Tree E Options selection
        options_result = self._tree_e_options(state, bias_val, state.regime.get("regime"), entry_result.get("entry_confidence"))
        
        # Combine into Plan
        state.plan = {
            "entry_analysis": entry_result,
            "options_strategy": options_result
        }
        
    def _tree_a_bias(self, state: SymbolState) -> Dict[str, Any]:
        """Tree A: Determine Market Bias (Weekly + Earnings)"""
        features = state.features
        bias = "NEUTRAL"
        confidence = 50
        note = []

        # 1. Earnings Check
        days_to_earnings = features.get("days_to_earnings")
        if days_to_earnings is not None and days_to_earnings <= 5:
            return {
                "bias": "EVENT_SENSITIVE", 
                "confidence": 0, 
                "note": f"Earnings in {days_to_earnings} days. Reduce risk."
            }

        # 2. Technical Check
        w_rsi = features.get("weekly_rsi")
        w_macd_regime = features.get("weekly_macd_regime")
        structure = features.get("structure_score", "NEUTRAL")
        
        if w_rsi is None or w_macd_regime is None:
             return {"bias": "UNKNOWN", "confidence": 0, "note": "Insufficient weekly data"}

        # Logic: MACD Bullish + RSI > 50 + Structure High = STRONG BULLISH
        if w_macd_regime == "BULLISH" and w_rsi > 50:
            if structure == "HIGH":
                bias = "BULLISH"
                confidence = 90
                note.append("Weekly Trend Strong (Structure + MACD + RSI)")
            else:
                bias = "BULLISH"
                confidence = 75
                note.append("Weekly Momentum Bullish (MACD + RSI)")
        elif w_macd_regime == "BEARISH" or w_rsi < 45:
            if structure == "LOW":
                bias = "BEARISH"
                confidence = 80
                note.append("Weekly Trend Bearish")
            else:
                bias = "BEARISH"
                confidence = 60
                note.append("Weekly Momentum Bearish")
        else:
            bias = "NEUTRAL"
            note.append("Mixed signals")

        return {
            "bias": bias,
            "confidence": confidence,
            "note": "; ".join(note)
        }

    def _tree_b_alert(self, state: SymbolState) -> Dict[str, Any]:
        """Tree B: Excellent Move Alert (Short Term daily triggers)"""
        features = state.features
        alert_on = False
        direction = "NONE"
        confidence = 0
        triggers = []

        # RSI Triggers
        d_rsi = features.get("daily_rsi")
        if d_rsi:
            if d_rsi < 30: 
                triggers.append("RSI Oversold")
                direction = "BULLISH_REVERSAL_WATCH"
            elif d_rsi > 70:
                triggers.append("RSI Overbought")
                direction = "BEARISH_REVERSAL_WATCH"
        
        # MACD
        d_regime = features.get("daily_macd_regime")
        bias = state.bias.get("bias")
        if d_regime == "BULLISH" and bias == "BULLISH":
             # This is momentum continuation, not necessarily an "Alert" unless fresh
             # For now, let's treat strong alignment as a trigger
             pass 

        # Candle Triggers
        if features.get("is_tweezer_bottom"):
            triggers.append("Tweezer Bottom")
            direction = "BULLISH_REversal"
            
        if features.get("is_hammer"):
            triggers.append("Hammer Candle")
            direction = "BULLISH_REVERSAL"
        
        if len(triggers) >= 1:
            alert_on = True
            confidence = 60 + (len(triggers) * 10)
        
        # If no explicit direction yet but alert on, default based on trigger type
        if alert_on and direction == "NONE":
            # Just a placeholder, ideally logic maps trigger -> direction
            pass

        return {
            "alert_on": alert_on,
            "direction": direction,
            "confidence": min(confidence, 100),
            "triggers": triggers
        }

    def _tree_c_regime(self, state: SymbolState) -> Dict[str, Any]:
        """Tree C: Volatility Regime (Compression vs Trending)"""
        # Ideally uses Bandwidth or DM. We use ATR and MACD hist as proxy.
        features = state.features
        
        # Proxy: If MACD Hist is flat/small -> Compression/Sideways
        # If Structure is High and MACD Bullish -> Trending
        
        structure = features.get("structure_score", "NEUTRAL")
        d_regime = features.get("daily_macd_regime", "NEUTRAL")
        hist = abs(features.get("daily_macd_hist", 0))
        
        regime = "SIDEWAYS"
        action = "WAIT"
        
        if structure == "HIGH" and d_regime == "BULLISH":
            regime = "TRENDING_UP"
            action = "ACT BOLDLY"
        elif structure == "LOW" and d_regime == "BEARISH":
            regime = "TRENDING_DOWN"
            action = "ACT BOLDLY"
        elif hist < 0.1: # Very low momentum
            regime = "COMPRESSION"
            action = "WAIT / CREDIT SPREADS"
            
        return {"regime": regime, "action": action}

    def _tree_d_entry(self, state: SymbolState, bias: str, alert: bool) -> Dict[str, Any]:
        """Tree D: Master Entry Checklist & Confidence"""
        features = state.features
        points = 0
        checklist = []
        
        # Level 1: RSI Zone
        rsi_zone = features.get("daily_rsi_zone")
        if rsi_zone == "CLEAN_ENTRY" or rsi_zone == "DEEP_RESET":
            points += 20
            checklist.append("RSI in Entry Zone")
        elif rsi_zone == "RISING" and bias == "BULLISH":
            points += 10
            checklist.append("RSI Rising in Trend")

        # Level 2: Structure
        if features.get("structure_score") == "HIGH" and bias == "BULLISH":
            points += 20
            checklist.append("Structure Bullish (>50>200)")

        # Level 3: Candles
        if features.get("is_tweezer_bottom") or features.get("is_hammer"):
            points += 15
            checklist.append("Bullish Candle Pattern")

        # Level 4: MACD Turn (Simplified: Histogram positive or crossed up)
        if features.get("daily_macd_hist", 0) > 0 and features.get("daily_macd_regime") == "BULLISH":
            points += 15
            checklist.append("MACD Momentum Positive")
            
        # Bonus: Weekly Alignment
        if bias == "BULLISH":
            points += 20
            checklist.append("Weekly Bias Alignment")
            
        # Deductions
        if features.get("earnings_status") in ["UPCOMING_5"]:
            points -= 100 # No entry entry before earnings
            checklist.append("WARNING: Earnings Imminent")
            
        entry_confidence = max(0, min(points, 100))
        
        tier = "C"
        if entry_confidence >= 90: tier = "S"
        elif entry_confidence >= 80: tier = "A"
        elif entry_confidence >= 60: tier = "B"
        
        return {
            "entry_allowed": entry_confidence >= 60,
            "entry_confidence": entry_confidence,
            "tier": tier,
            "checklist": checklist
        }

    def _tree_e_options(self, state: SymbolState, bias: str, regime: str, confidence: int) -> Dict[str, Any]:
        """Tree E: Options Selection"""
        features = state.features
        strat_type = "NONE"
        dte = "N/A"
        strike = "N/A"
        
        # 1. Earnings Check
        earnings_status = features.get("earnings_status")
        if earnings_status in ["UPCOMING_5", "UPCOMING_5_10"]:
            return {"strategy": "SKIP / DEFINED RISK ONLY", "note": "Earnings too close"}

        # 2. Strategy Selection
        if bias == "BULLISH":
            if confidence >= 80:
                strat_type = "LONG CALL (Debit)"
                strike = "ATM or ITM (70 delta)"
            elif confidence >= 60:
                strat_type = "BULL CALL SPREAD"
                strike = "Buy ITM / Sell OTM"
            else:
                strat_type = "CREDIT SPREAD (Put)"
                strike = "Sell OTM Support"
        elif bias == "BEARISH":
            strat_type = "LONG PUT / PUT SPREAD"
            strike = "ATM"
        else:
            strat_type = "IRON CONDOR / CREDIT SPREAD"
            strike = "Far OTM"

        # 3. DTE Selection based on Regime
        if regime == "TRENDING_UP" or regime == "TRENDING_DOWN":
             dte = "45-60 Days (Swing)"
        elif regime == "COMPRESSION":
             dte = "Wait or 21-30 Days"
        else:
             dte = "30-45 Days"
             
        return {
            "type": strat_type,
            "dte": dte,
            "strike_selection": strike
        }
