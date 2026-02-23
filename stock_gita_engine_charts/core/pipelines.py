from datetime import datetime
import pandas as pd
from .calendar_engine import CalendarProcessingEngine
from .scanner_engine import MarketIndexScanner
from .indicators import TechnicalIndicatorCalculator
from .regime_engine import RegimeIdentificationEngine
from .qualifier import PreTradeQualificationSystem
from .confidence import ConfidenceScoringEngine
from .signal_generator import TradeSignalGenerator
from .options_engine import OptionsExecutionEngine
from .output_api import TradeSignalAPI
from ..data.usa_api import TwelveDataAPI
from .sli_detector import detect_sli

class TradingPipeline:
    def __init__(self):
        self.api = TwelveDataAPI()
        
        # Initialize Modules
        self.calendar_engine = CalendarProcessingEngine()
        self.scanner_engine = MarketIndexScanner()
        self.indicator_engine = TechnicalIndicatorCalculator()
        self.regime_engine = RegimeIdentificationEngine()
        self.qualifier_engine = PreTradeQualificationSystem()
        self.confidence_engine = ConfidenceScoringEngine()
        self.signal_engine = TradeSignalGenerator()
        self.options_engine = OptionsExecutionEngine()
        self.output_api = TradeSignalAPI()

    def run_full_analysis(self, symbol):
        """
        Executes the full Phase 0 -> Phase 10 pipeline for a single symbol.
        Strict 11-Phase Implementation.
        """
        results = {}
        
        # 0. Fetch Data (Multi-timeframe) - Pre-requisite
        print(f"DEBUG: Fetching data for {symbol}...")
        try:
            data_frames = self.api.get_multi_timeframe_data(symbol)
            print(f"DEBUG: Got data_frames: {type(data_frames)}, keys: {list(data_frames.keys()) if data_frames else 'None'}")
            
            if not data_frames:
                return {"error": f"Could not fetch data for {symbol} - API returned None"}
            
            df_daily = data_frames.get("DAILY")
            print(f"DEBUG: df_daily type: {type(df_daily)}, is None: {df_daily is None}, is empty: {df_daily.empty if df_daily is not None else 'N/A'}")
            
            if df_daily is None or df_daily.empty:
                return {"error": f"Could not fetch daily data for {symbol}"}
        except Exception as e:
            print(f"DEBUG: Exception in data fetch: {e}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return {"error": f"Exception fetching data for {symbol}: {str(e)}"}
        
        # Meta Data
        last_date = df_daily.iloc[-1]['date']
        from datetime import datetime
        data_date = pd.to_datetime(last_date).date()
        today_date = datetime.now().date()
        market_status = "Open/Live" if data_date == today_date else "Closed (Previous Day)"
        
        results["meta"] = {
            "symbol": symbol,
            "last_updated": str(last_date),
            "market_status": market_status
        }

        # --- PHASE 0: Calendar-First Scan ---
        # Now using live data from APIs
        try:
            print(f"DEBUG: Running calendar engine phase_0_scan...")
            results['phase_0_calendar'] = self.calendar_engine.phase_0_scan(symbol)
            print(f"DEBUG: Calendar scan completed")
        except Exception as e:
            print(f"DEBUG: Calendar scan failed: {e}")
            results['phase_0_calendar'] = {"status": "ERROR", "error": str(e)}
        
        # --- PHASE 1: Stock-Specific Historical Behavior ---
        # Simple Logic: Check returns for current month in historical data (5y)
        print(f"DEBUG: Starting Phase 1...")
        current_month = datetime.now().month
        df_monthly = data_frames.get("MONTHLY")
        print(f"DEBUG: df_monthly type: {type(df_monthly)}, is None: {df_monthly is None}")
        phase_1_status = "NEUTRAL"
        avg_return = 0.0
        if df_monthly is not None and len(df_monthly) > 12:
            monthly_returns = df_monthly[df_monthly['date'].dt.month == current_month]['close'].pct_change()
            avg_return = monthly_returns.mean()
            if avg_return > 0.02: phase_1_status = "BULLISH_SEASONALITY"
            elif avg_return < -0.02: phase_1_status = "BEARISH_SEASONALITY"
        print(f"DEBUG: Phase 1 completed")
            
        results['phase_1_history'] = {
            "status": phase_1_status,
            "avg_monthly_return_pct": round(avg_return * 100, 2)
        }
        
        # --- PHASE 2: Market Index Confirmation ---
        # Checks SPY, QQQ, DIA alignment
        # Scanner engine returns phase 2 and 3 info combined, we split strictly here
        print(f"DEBUG: Starting Phase 2 - Market Index Confirmation")
        try:
            scanner_res = self.scanner_engine.phase_2_3_scan(symbol)
            print(f"DEBUG: scanner_res type: {type(scanner_res)}, value: {scanner_res}")
            
            if scanner_res is None:
                print(f"DEBUG: scanner_res is None, using defaults")
                scanner_res = {'phase_2': {}, 'phase_3': {}}
                
            results['phase_2_market'] = scanner_res.get('phase_2', {})
            
            # --- PHASE 3: Independent Stock Check ---
            # Checks if stock is an "Independent Mover" (e.g. NVDA, TSLA)
            results['phase_3_independent'] = scanner_res.get('phase_3', {})
            print(f"DEBUG: Phase 2 & 3 completed")
        except Exception as phase2_error:
            print(f"DEBUG: Phase 2/3 error: {phase2_error}")
            import traceback
            print(f"DEBUG: Phase 2/3 traceback: {traceback.format_exc()}")
            results['phase_2_market'] = {"error": str(phase2_error)}
            results['phase_3_independent'] = {"error": str(phase2_error)}
        
        # --- PHASE 4: Higher-Timeframe Trend Assessment ---
        # Analyze Weekly/Monthly trends to align with lower timeframes
        htf_trend = "NEUTRAL"
        if data_frames.get("WEEKLY") is not None:
             w_inds = self.indicator_engine.calculate_all_indicators(data_frames['WEEKLY'])
             htf_trend = w_inds.get('trend', 'NEUTRAL')
        
        results['phase_4_htf'] = {
            "weekly_trend": htf_trend,
            "monthly_trend": "BULLISH" if df_monthly is not None and df_monthly.iloc[-1]['close'] > df_monthly.iloc[-1]['open'] else "BEARISH"
        }
        
        # --- PHASE 5: Trade Timeframe Selection ---
        # Logic to decide execution timeframe. 
        # Default: Stocks -> Daily, Options -> Daily/Hourly (Code supports Daily mainly)
        execution_tf = "DAILY"
        results['phase_5_timeframe'] = {
            "selected_timeframe": execution_tf,
            "rationale": "Standard Equities/Options Swing"
        }
        
        # --- PHASE 6: SLI (Support/Resistance/Liquidity) ---
        # Primary Trigger Check
        sli_zones = detect_sli(df_daily)
        current_price = df_daily.iloc[-1]['close']
        nearest_support = max([s for s in sli_zones.get('support', []) if s < current_price], default=0)
        nearest_resistance = min([r for r in sli_zones.get('resistance', []) if r > current_price], default=float('inf'))
        
        results['phase_6_sli'] = {
            "zones": sli_zones,
            "proximity": {
                "dist_to_support_pct": round(((current_price - nearest_support)/current_price)*100, 2),
                "dist_to_resistance_pct": round(((nearest_resistance - current_price)/current_price)*100, 2)
            }
        }
        
        # --- PHASE 7: Indicator Confluence ---
        # Calculate Daily Indicators
        indicators = self.indicator_engine.calculate_all_indicators(df_daily)
        results['phase_7_confluence'] = {
            "indicators": indicators,
            "status": "CONFLUENT" if indicators.get('trend') == htf_trend else "DIVERGENT"
        }
        
        # --- PHASE 8, 9, 10: Execution Pipeline ---
        
        # Phase 5b/8 (Regime) - often mapped to Phase 4 or 8 in different docs, placing here as pre-signal
        regime = self.regime_engine.identify_regime(indicators)
        results['regime'] = regime # Keeping legacy key for compatibility
        
        # Qualification (Internal Confluence Check)
        
        # Helper: Populate timeframes dict early for qualification
        # (Was previously done at end of pipeline)
        results['timeframes'] = {}
        for tf_name in ['DAILY', 'WEEKLY', 'MONTHLY']:
            df = data_frames.get(tf_name)
            if df is not None and not df.empty:
                # Calculate indicators for report context
                # Note: re-calculating daily here is slightly redundant but safe
                if tf_name == 'DAILY':
                    inds = indicators
                else:
                    inds = self.indicator_engine.calculate_all_indicators(df)
                
                # Check if indicators calculation succeeded
                if inds is None:
                    print(f"DEBUG: calculate_all_indicators returned None for {tf_name}")
                    inds = {'trend': 'NEUTRAL', 'error': 'Indicator calculation failed'}
                    
                results['timeframes'][tf_name] = {
                    "indicators": inds,
                    "trend": inds.get('trend', 'NEUTRAL')
                }

        qualification = self.qualifier_engine.qualify_for_trade(
            indicators, 
            results['phase_0_calendar'],
            results['phase_6_sli'],
            regime,
            results['timeframes'],
            current_price
        )
        results['qualification'] = qualification

        # Confidence Scoring
        confidence = self.confidence_engine.calculate_confidence(
            results['phase_0_calendar'],
            qualification,
            regime,
            indicators
        )
        
        # Signal Generation (Phase 8/9)
        signal = self.signal_engine.generate_signal(symbol, confidence, regime, indicators)
        results['phase_8_9_signal'] = signal
        # Keep legacy key
        results['signal'] = signal 

        # Options Execution (Phase 10)
        options = self.options_engine.generate_options_trade(signal, indicators)
        results['phase_10_options'] = options
        results['options'] = options
        
        # Final Output Gen
        
        # Populate timeframes for output (Fix for tools.py iteration error)
        results['timeframes'] = {}
        for tf_name in ['DAILY', 'WEEKLY', 'MONTHLY']:
            df = data_frames.get(tf_name)
            if df is not None and not df.empty:
                # Calculate indicators for report context
                # Note: re-calculating daily here is slightly redundant but safe
                inds = self.indicator_engine.calculate_all_indicators(df)
                
                # Check if indicators calculation succeeded
                if inds is None:
                    print(f"DEBUG: calculate_all_indicators returned None for {tf_name} (duplicate section)")
                    inds = {'trend': 'NEUTRAL', 'error': 'Indicator calculation failed'}
                    
                results['timeframes'][tf_name] = {
                    "indicators": inds,
                    "trend": inds.get('trend', 'NEUTRAL')
                }
        final_output = self.output_api.generate_json_output(results)
        
        # Attach raw data for context
        final_output['_raw_indicators'] = indicators
        final_output['_raw_df'] = df_daily
        
        return final_output

    def run_scanner(self, watchlist=None):
        if not watchlist:
            watchlist = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META']
            
        results = []
        for sym in watchlist:
             res = self.run_full_analysis(sym)
             if "error" not in res:
                 sig = res['trade_signal']
                 results.append({
                     "Symbol": sym,
                     "Signal": sig.get('direction', 'NEUTRAL') if sig['signal_generated'] else "WAIT",
                     "Confidence": f"{res['analysis']['confidence']['final_confidence']}%",
                     "Regime": res['analysis']['regime']['regime']
                 })
                 
        return results
