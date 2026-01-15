import argparse
import json
import logging
from dataclasses import asdict

from data_layer import DataLayer
from features import FeatureEngineer
from rules import RulesEngine
from position_risk import PositionSizer
from backtester import Backtester

# Ensure logging is configured to show our info
logging.basicConfig(level=logging.INFO, format='%(message)s')   
logger = logging.getLogger(__name__)

def analyze_symbol(symbol: str, account_size: float = 10000, silent: bool = False):
    if not silent:
        print(f"\n--- Analyzing {symbol} (Account: ${account_size}) ---")
    
    # 1. Data Layer
    dl = DataLayer()
    state = dl.fetch_symbol_data(symbol)
    
    if not state.daily_bars:
        if not silent: logger.error(f"Failed to fetch data for {symbol}")
        return None, None

    # 2. Features
    fe = FeatureEngineer()
    fe.compute_features(state)
    
    # 3. Rules
    re = RulesEngine()
    re.run_rules(state)
    
    # 4. Position Sizing
    ps = PositionSizer(account_size=account_size)
    atr = state.features.get("atr_14", 0)
    current_price = state.daily_bars[0].close
    stop_price = current_price - (atr * 2) if atr > 0 else current_price * 0.95
    
    entry_conf = state.plan.get("entry_analysis", {}).get("entry_confidence", 0)
    bias = state.bias.get("bias", "BULLISH")
    
    # Determine relevant structural level for stop
    struct_lvl = None
    if bias == "BULLISH":
        struct_lvl = state.features.get("nearest_support")
    else:
        struct_lvl = state.features.get("nearest_resistance")

    position_result = ps.calculate_position(
        entry_price=current_price,
        stop_loss=stop_price,
        confidence=entry_conf,
        bias=bias,
        structural_lvl=struct_lvl
    )
    
    # 5. Output
    if not silent:
        print_report(state, position_result)
    
    return state, position_result

def backtest_symbol(symbol: str, account_size: float = 10000, days: int = None):
    if days is None:
        print(f"\n--- Backtesting {symbol} (All Available Data - 5 Years) ---")
    else:
        print(f"\n--- Backtesting {symbol} (Last {days} Days) ---")
    
    # 1. Data Layer (Fetch once)
    dl = DataLayer()
    state = dl.fetch_symbol_data(symbol)
    if not state.daily_bars:
        logger.error("Data fetch failed")
        return

    # 2. Run Backtest
    bt = Backtester(start_days_ago=days, account_size=account_size)
    results = bt.run_backtest(state)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return

    # 3. Report
    print(f"\n[Backtest Results for {symbol}]")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Total PnL: ${results['total_pnl']:.2f}")
    print(f"Final Equity: ${results['final_equity']:.2f}")
    
    print("\n[Trade Log]")
    for t in results['trades']:
        duration = t.get('duration_days', 0)
        print(f"{t['entry_date']} -> {t['exit_date']} ({duration} days): {t['reason']} | PnL: ${t['pnl']} ({t['return_pct']}%)")


def scan_market(account_size: float, custom_list_str: str = None):
    # Default list
    default_watchlist = ['AAPL', 'NVDA', 'PANW', 'AVGO', 'ADBE', 'MDB', 'ASML', 'TSLA', 'BLK', 'RH', 'MSTR', 'COIN']
    
    if custom_list_str:
        # Split by comma or space and strip
        watchlist = [s.strip().upper() for s in custom_list_str.replace(',', ' ').split() if s.strip()]
    else:
        watchlist = default_watchlist

    opportunities = []
    
    print(f"\n--- Scanning Watchlist: {', '.join(watchlist)} ---")
    print("Checking signals...")
    
    for sym in watchlist:
        try:
            state, pos = analyze_symbol(sym, account_size, silent=True)
            if not state: continue
            
            entry_conf = state.plan.get("entry_analysis", {}).get("entry_confidence", 0)
            checklist = state.plan.get("entry_analysis", {}).get("checklist", [])
            # Convert checklist to short reason string
            # Take top 3 reasons
            reason_str = ", ".join(checklist[:3]) if checklist else "None"
            
            print(f" > {sym}: Conf {entry_conf}/100")
            
            # Use 40 as filter to allow 'Wait' signals to be shown if they have some data
            if entry_conf >= 40:
                 opportunities.append({
                     "symbol": sym,
                     "bias": state.bias.get("bias"),
                     "conf": entry_conf,
                     "strategy": state.plan.get("options_strategy", {}).get("type"),
                     "tp_1r": pos.get("take_profit_1r"),
                     "tp_2r": pos.get("take_profit_1"), # Using 2R (TP1) as 2nd target column
                     "units": pos.get("units"),
                     "reason": reason_str
                 })
                 
        except Exception as e:
            logger.error(f"Error scanning {sym}: {e}")
            
    # Print Table
    print("\n\n=== TOP OPPORTUNITIES ===")
    if not opportunities:
        print("No high-confidence setups found right now.")
    else:
        # Columns: SYMBOL | BIAS | CONF | STRATEGY | TARGET (1R) | TARGET (2R) | UNITS | REASON
        header = f"{'SYMBOL':<8} | {'BIAS':<8} | {'CONF':<5} | {'STRATEGY':<20} | {'TGT (1R)':<10} | {'TGT (2R)':<10} | {'UNITS':<5} | {'REASON'}"
        print(header)
        print("-" * len(header))
        for op in opportunities:
             # Truncate reason to 40 chars
             reason_trunc = (op['reason'][:45] + '..') if len(op['reason']) > 45 else op['reason']
             row = f"{op['symbol']:<8} | {op['bias']:<8} | {op['conf']:<5} | {op['strategy']:<20} | {str(op['tp_1r']):<10} | {str(op['tp_2r']):<10} | {op['units']:<5} | {reason_trunc}"
             print(row)


def print_report(state, position_result):
    print(f"\n[Analysis Report for {state.symbol}]")
    print(f"Data Date: {state.features.get('current_date')}")
    print(f"Price: {state.daily_bars[0].close}")
    
    print("\n--- Technicals ---")
    print(f"RSI (14): {round(state.features.get('daily_rsi', 0), 2)}")
    print(f"StochRSI: K={round(state.features.get('daily_stoch_k', 0), 2)} D={round(state.features.get('daily_stoch_d', 0), 2)}")
    
    macd_line = state.features.get('daily_macd_line')
    macd_hist = state.features.get('daily_macd_hist')
    if macd_line is not None:
         print(f"MACD: {round(macd_line, 3)} | Hist: {round(macd_hist, 3)} ({state.features.get('daily_macd_regime')})")
    else:
         print(f"MACD: N/A")

    print(f"ATR (14): {round(state.features.get('atr_14', 0), 2)}")
    
    print("\n--- Structure & Patterns ---")
    print(f"Structure Score: {state.features.get('structure_score')}")
    print(f"SMA 55: {round(state.features.get('sma_55', 0), 2)} | SMA 89: {round(state.features.get('sma_89', 0), 2)} | SMA 144: {round(state.features.get('sma_144', 0), 2)} | SMA 233: {round(state.features.get('sma_233', 0), 2)}")
    
    patterns = []
    if state.features.get("is_hammer"): patterns.append("HAMMER")
    if state.features.get("is_tweezer_bottom"): patterns.append("TWEEZER BOTTOM")
    if not patterns: patterns.append("None")
    print(f"Candle Patterns: {', '.join(patterns)}")
    
    print("\n--- Market Context ---")
    print(f"BIAS: {state.bias.get('bias')} (Conf: {state.bias.get('confidence')})")
    print(f"REGIME: {state.regime.get('regime')} -> Action: {state.regime.get('action')}")
    print(f"KEY LEVELS: Support {state.features.get('nearest_support')} | Resistance {state.features.get('nearest_resistance')}")
    
    print("\n--- Trade Plan ---")
    plan = state.plan
    entry = plan.get("entry_analysis", {})
    print(f"ENTRY: {'ALLOWED' if entry.get('entry_allowed') else 'WAIT'}")
    print(f"Confidence: {entry.get('entry_confidence')} (Tier: {entry.get('tier')})")
    print(f"Checklist: {', '.join(entry.get('checklist', []))}")
    
    opts = plan.get("options_strategy", {})
    print(f"STRATEGY: {opts.get('type')}")
    print(f"Options: {opts.get('dte')} DTE | Strike: {opts.get('strike_selection')}")
    
    print("\n--- Position Sizing (1% Risk) ---")
    print(f"Units: {position_result.get('units')} shares")
    print(f"Stop Loss: {round(position_result.get('stop'), 2)} (Type: {position_result.get('stop_source')}) - Risk: ${position_result.get('risk_amount')}")
    print(f"Targets: TP1 {position_result.get('take_profit_1')} | TP2 {position_result.get('take_profit_2')}")
    print(f"Total Exposure: ${position_result.get('total_exposure')}")

    if state.alerts.get("alert_on"):
        print(f"\n[!] ALERTS: {', '.join(state.alerts.get('triggers'))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GS System Agent CLI")
    parser.add_argument("command", choices=["analyze", "backtest", "scan"], help="Command to run")
    parser.add_argument("symbol", nargs="?", help="Stock symbol (e.g., AAPL) - Required for analyze/backtest")
    parser.add_argument("--account", type=float, default=10000, help="Account size used for position sizing")
    parser.add_argument("--days", type=int, default=None, help="Number of days to backtest (default: all available data - 5 years)")
    
    args = parser.parse_args()
    
    if args.command == "scan":
        scan_market(args.account, args.symbol)
    elif not args.symbol:
        print("Error: Symbol required for analyze/backtest")
    elif args.command == "analyze":
        analyze_symbol(args.symbol.upper(), args.account)
    elif args.command == "backtest":
        # Use all available data (5 years) by default, or specified days
        backtest_symbol(args.symbol.upper(), args.account, days=args.days)
