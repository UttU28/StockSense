import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from dataclasses import replace

from models import SymbolState, DailyBar, WeeklyBar
from features import FeatureEngineer
from rules import RulesEngine
from position_risk import PositionSizer

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, start_days_ago: int = None, account_size: float = 10000.0):
        self.start_days_ago = start_days_ago
        self.account_size = account_size
        self.fe = FeatureEngineer()
        self.re = RulesEngine()
        self.ps = PositionSizer(account_size)
        
        self.trades = []
        self.equity_curve = []
        self.current_equity = account_size
        self.active_position = None

    def run_backtest(self, full_state: SymbolState) -> Dict[str, Any]:
        if not full_state.daily_bars:
            return {"error": "No daily data"}

        all_daily = sorted(full_state.daily_bars, key=lambda x: x.date)
        all_weekly = sorted(full_state.weekly_bars, key=lambda x: x.date)
        
        # Use all available data if start_days_ago is None
        if self.start_days_ago is None:
            # Use all data, but skip first 35 days to ensure we have enough data for indicators
            sim_indices = list(range(35, len(all_daily)))
            logger.info(f"Using all available data: {len(sim_indices)} days (skipping first 35 for indicator calculation)")
        else:
            end_date_str = all_daily[-1].date
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            start_date = end_date - timedelta(days=self.start_days_ago)
            
            sim_indices = [i for i, b in enumerate(all_daily) 
                           if datetime.strptime(b.date, "%Y-%m-%d") >= start_date]

        if not sim_indices:
            return {"error": "Not enough data for backtesting (need at least 35 days for indicators)"}
        
        logger.info(f"Backtesting on {len(sim_indices)} days of data")

        for idx in sim_indices:
            current_bar = all_daily[idx]
            current_date_str = current_bar.date
            current_date_dt = datetime.strptime(current_date_str, "%Y-%m-%d")
            
            if self.active_position:
                self._check_exit(current_bar, self.active_position)
            
            pit_daily = all_daily[:idx+1][::-1]
            pit_weekly = [w for w in all_weekly if datetime.strptime(w.date, "%Y-%m-%d") < current_date_dt]
            pit_weekly = pit_weekly[::-1]
            
            pit_state = SymbolState(
                symbol=full_state.symbol,
                last_updated=current_date_str,
                daily_bars=pit_daily,
                weekly_bars=pit_weekly,
                earnings=full_state.earnings
            )
            pit_state.indicators = full_state.indicators
            
            self._fill_indicators_placeholders(pit_state)
            self.fe.compute_features(pit_state)
            self.re.run_rules(pit_state)
            
            if not self.active_position:
                self._check_entry(pit_state, current_bar)
            self.equity_curve.append({
                "date": current_date_str, 
                "equity": self.current_equity
            })

        if self.active_position:
            last_bar = all_daily[sim_indices[-1]]
            exit_price = last_bar.close
            pnl = (exit_price - self.active_position["entry_price"]) * self.active_position["units"]
            self.current_equity += pnl
            self._record_trade(self.active_position, last_bar.date, exit_price, "END_OF_SIM", pnl)
            
        return self._generate_report()

    def _fill_indicators_placeholders(self, state: SymbolState):
        """Features.py reads state.indicators. Indicators are passed from full_state."""
        pass

    def _check_entry(self, state: SymbolState, current_bar: DailyBar):
        plan = state.plan.get("entry_analysis", {})
        if plan.get("entry_allowed") and plan.get("entry_confidence", 0) >= 60:
            atr = state.features.get("atr_14", 0)
            bias = state.bias.get("bias", "BULLISH")
            
            # Calculate stop based on bias
            if bias == "BEARISH":
                stop_price = current_bar.close + (atr * 2)  # Stop above for short
            else:
                stop_price = current_bar.close - (atr * 2)  # Stop below for long
            
            # Get structural level for stop
            struct_lvl = None
            if bias == "BULLISH":
                struct_lvl = state.features.get("nearest_support")
            else:
                struct_lvl = state.features.get("nearest_resistance")
            
            size_res = self.ps.calculate_position(
                entry_price=current_bar.close,
                stop_loss=stop_price,
                confidence=plan.get("entry_confidence"),
                bias=bias,
                structural_lvl=struct_lvl
            )
            
            units = size_res.get("units", 0)
            if units > 0:
                options_strategy = state.plan.get("options_strategy", {})
                
                self.active_position = {
                    "entry_date": current_bar.date,
                    "entry_price": current_bar.close,
                    "units": units,
                    "stop_loss": stop_price,
                    "initial_risk": size_res.get("risk_amount"),
                    "tier": plan.get("tier"),
                    "bias": bias,
                    "options_strategy": options_strategy.get("type", "NONE")
                }
                logger.info(f"[{current_bar.date}] BUY {units} @ {current_bar.close} (Tier {plan.get('tier')})")

    def _check_exit(self, current_bar: DailyBar, pos: Dict):
        if current_bar.low <= pos["stop_loss"]:
            exit_price = pos["stop_loss"]
            pnl = (exit_price - pos["entry_price"]) * pos["units"]
            self.current_equity += pnl
            self._record_trade(pos, current_bar.date, exit_price, "STOP_LOSS", pnl)
            self.active_position = None
            return

        risk = pos["entry_price"] - pos["stop_loss"]
        target = pos["entry_price"] + (2 * risk)
        
        if current_bar.high >= target:
            exit_price = target
            pnl = (exit_price - pos["entry_price"]) * pos["units"]
            self.current_equity += pnl
            self._record_trade(pos, current_bar.date, exit_price, "TAKE_PROFIT_2R", pnl)
            self.active_position = None

    def _record_trade(self, pos, date, price, reason, pnl):
        entry_price = pos["entry_price"]
        exit_price = price
        units = pos["units"]
        price_change = exit_price - entry_price
        price_change_pct = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        # Calculate duration in days
        entry_date_dt = datetime.strptime(pos["entry_date"], "%Y-%m-%d")
        exit_date_dt = datetime.strptime(date, "%Y-%m-%d")
        duration_days = (exit_date_dt - entry_date_dt).days
        
        bias = pos.get("bias", "BULLISH")
        options_strategy = pos.get("options_strategy", "NONE")
        
        # Determine trade type
        trade_type = "STOCK"
        action = "BUY"  # Backtester only does long positions
        direction = bias
        
        # Determine options equivalent
        call_or_put = "N/A"
        if options_strategy and options_strategy != "NONE":
            if "CALL" in options_strategy.upper() or "BULL" in options_strategy.upper():
                call_or_put = "CALL"
            elif "PUT" in options_strategy.upper() or "BEAR" in options_strategy.upper():
                call_or_put = "PUT"
        
        self.trades.append({
            "entry_date": pos["entry_date"],
            "exit_date": date,
            "duration_days": duration_days,
            "units": units,
            "entry_price": round(entry_price, 2),
            "exit_price": round(exit_price, 2),
            "price_change": round(price_change, 2),
            "price_change_pct": round(price_change_pct, 2),
            "pnl": round(pnl, 2),
            "reason": reason,
            "return_pct": round((exit_price - entry_price) / entry_price * 100, 2),
            "total_value": round(units * entry_price, 2),
            "action": action,
            "trade_type": trade_type,
            "direction": direction,
            "options_strategy": options_strategy,
            "call_or_put": call_or_put
        })
        logger.info(f"[{date}] SELL {units} @ {exit_price} ({reason}) PnL: {pnl}")

    def _generate_report(self):
        df = pd.DataFrame(self.trades)
        win_rate = 0
        total_pnl = 0
        if not df.empty:
            total_pnl = df["pnl"].sum()
            wins = df[df["pnl"] > 0]
            win_rate = (len(wins) / len(df)) * 100
        
        return {
            "total_trades": len(df),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "final_equity": self.current_equity,
            "trades": self.trades
        }
