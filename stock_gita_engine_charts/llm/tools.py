from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional, List
from ..core.pipelines import TradingPipeline

# Initialize pipeline once to reuse connections
pipeline = TradingPipeline()

class AnalyzeStockInput(BaseModel):
    symbol: str = Field(description="The stock symbol to analyze (e.g., AAPL, NVDA, TSLA)")

def format_multi_timeframe_results(results: dict) -> str:
    """
    Generates the 'Modern Minimalist' Executive Brief Report.
    Strictly covers all 11 Phases (0-10) in a clean, high-level format.
    """
    if "error" in results:
        return f"ERROR: {results['error']}"

    # Helpers
    def clean(val): return str(val) if val is not None else "—"
    
    def safe_round(val, decimals=2):
        try:
            if isinstance(val, (int, float)):
                return round(val, decimals)
            return val
        except:
            return val
            
    phases = results.get('phases', {})
    
    # Extract Key Data
    meta = results.get('meta', {})
    symbol = meta.get('symbol', 'TARGET')
    date = meta.get('last_updated', 'Unknown')
    
    # Signal (Phase 8/9)
    p8 = phases.get('8_9_signal', {})
    signal_dir = p8.get('direction', 'WAIT').upper()
    confidence = p8.get('confidence', 0)
    
    lines = []
    
    # Extract Qualification & Gates
    qual = results.get('qualification', {})
    q_status = qual.get('qualification_status', 'UNKNOWN')
    q_reason = qual.get('reason', '')
    gate_details = qual.get('details', {})
    
    # Extract Context
    p0 = phases.get('0_calendar', {})
    year_bias = clean(p0.get('year_digit_bias'))
    stock_mem = clean(p0.get('stock_memory'))
    
    # Extract Momentum
    momentum_alert = p8.get('momentum_alert', False)
    
    # Header Update
    lines.append(f"# Analysis: {symbol}")
    lines.append(f"**Verdict**: **{signal_dir}** ({confidence}% Confidence)")
    if q_status == 'BLOCKED':
         lines.append(f"**[BLOCKED]**: {q_reason}\n")
    else:
         lines.append(f"\n")
    lines.append(f"> *Data Date: {date}*")
    lines.append("\n---\n")

    # --- SECTION 1: CONTEXT & GOVERNANCE ---
    lines.append("### 1. Context & Governance")
    
    # Gates Table
    sli_gate = gate_details.get('GATE_1_SLI', {'passed': False})
    tf_gate = gate_details.get('GATE_2_TIMEFRAME', {'passed': False})
    
    lines.append(f"*   **SLI Hard Gate**: {'[PASSED]' if sli_gate['passed'] else '[FAILED]'}")
    if not sli_gate['passed']:
        lines.append(f"    *   *Reason*: {sli_gate.get('reason')}")
        
    lines.append(f"*   **Timeframe Gate**: {'[PASSED]' if tf_gate['passed'] else '[FAILED]'}")
    
    # Context
    lines.append(f"*   **Year Context**: {year_bias}")
    lines.append(f"*   **Stock Memory**: {stock_mem}")
    
    seasonality = clean(p0.get('seasonality', 'Neutral')) 
    earnings = clean(p0.get('earnings_check', {}).get('earnings_date', 'None'))
    lines.append(f"*   **Earnings Next**: {earnings}")
    lines.append("\n")

    # --- SECTION 2: TREND & LEVELS ---
    lines.append("### 2. Trend & Levels")
    
    # Phase 4: HTF Trend
    p4 = phases.get('4_htf_trend', {})
    
    tf_data = results.get('timeframes', {})
    w_inds = tf_data.get('WEEKLY', {}).get('indicators', {})
    w_strict = w_inds.get('strict_trend', 'NEUTRAL')
    
    lines.append(f"*   **Strict Trend (W)**: {w_strict}")
    lines.append(f"*   **Regime**: {clean(phases.get('regime', {}).get('regime'))}")
    
    # Phase 5: Timeframe
    p5 = phases.get('5_timeframe', {})
    exec_tf = clean(p5.get('selected_timeframe', 'DAILY'))
    lines.append(f"*   **Execution**: {exec_tf}")
    
    # Phase 6: SLI
    p6 = phases.get('6_sli', {})
    prox = p6.get('proximity', {})
    zones = p6.get('zones', {})
    sup_level = zones.get('support', ['None'])[0] if zones.get('support') else "None"
    res_level = zones.get('resistance', ['None'])[0] if zones.get('resistance') else "None"
    
    lines.append(f"*   **Key Levels**:")
    lines.append(f"    *   Support: **${sup_level}** ({prox.get('dist_to_support_pct', '-') }%)")
    lines.append(f"    *   Resistance: **${res_level}** ({prox.get('dist_to_resistance_pct', '-') }%)")
    lines.append("\n")

    # --- SECTION 3: TECHNICALS ---
    lines.append("### 3. Technicals")
    
    p7 = phases.get('7_confluence', {})
    inds = p7.get('indicators', {})
    
    rsi = safe_round(inds.get('rsi', 0))
    macd_val = inds.get('macd', {}).get('macd_line', 0) if isinstance(inds.get('macd'), dict) else 0
    adx = safe_round(inds.get('directional_movement', {}).get('trend_strength', 0))
    
    autowave = inds.get('autowaves', {}).get('wave_type', 'NONE')
    autowave_l2 = inds.get('autowaves', {}).get('line_2_level', 0)

    lines.append(f"*   **Indicators**: RSI {rsi} • ADX {adx} • MACD {safe_round(macd_val)}")
    lines.append(f"*   **Momentum Alert**: {'[ACTIVE]' if momentum_alert else 'Normal'}")
    lines.append(f"*   **Market Structure**: AutoWave **{autowave}** (Pivot: {autowave_l2})")
    lines.append("\n")

    # --- SECTION 4: EXECUTION PLAN ---
    lines.append("### 4. Execution Plan")
    
    lines.append(f"*   **Action**: **{signal_dir}**")
    
    if signal_dir != "WAIT":
        # Options - Phase 10
        p10 = phases.get('10_options', {})
        strategy = p10.get('strategy', 'No Options')
        strike = p10.get('strike_target', 0)
        
        lines.append(f"*   **Confidence**: {confidence}%")
        lines.append(f"*   **Rationale**: {clean(p8.get('reason'))}")
        lines.append(f"*   **Options Play**: {strategy} @ ${safe_round(strike)}")
    else:
        lines.append(f"*   **Guidance**: Monitor. {q_reason if q_status == 'BLOCKED' else f'Confidence {confidence}% low.'}")
    
    return "\n".join(lines)

def analyze_stock_func(symbol: str) -> str:
    """
    Analyzes a specific stock symbol using the full Stock Gita trading framework.
    Returns a detailed report including Calendar checks, SLI, Indicators, Confidence, and Signals.
    """
    try:
        # Pass symbol to result for formatting context
        result = pipeline.run_full_analysis(symbol.upper())
        if result and "symbol" not in result:
             result["symbol"] = symbol.upper()
             
        # Format the complex dict into a readable markdown/text prompt for the LLM
        formatted_output = format_multi_timeframe_results(result)

        # Append Static Chart Image (Bypassing Sandbox) with Link to Interactive
        img_url = f"http://18.215.117.40/chart_img?symbol={symbol.upper()}"
        interactive_url = f"http://18.215.117.40/chart_v2?symbol={symbol.upper()}"
        
        iframe_code = f"""
---
### Interactive Technical Chart
[![Chart Preview]({img_url})]({interactive_url})
*Click the chart above to open the full interactive view.*
"""
        formatted_output += iframe_code
        
        print(f"DEBUG: Tool Output (First 200 chars): {formatted_output[:200]}...")
        return formatted_output
        
    except Exception as e:
        return f"Error analyzing {symbol}: {str(e)}"

analyze_stock_tool = StructuredTool.from_function(
    func=analyze_stock_func,
    name="analyze_stock",
    description="Useful for analyzing a specific stock to get a comprehensive trading report including buy/sell signals, confidence scores, and risk parameters.",
    args_schema=AnalyzeStockInput
)

class MarketScanInput(BaseModel):
    watchlist: Optional[List[str]] = Field(description="Optional list of symbols to scan. If omitted, scans default major tech stocks.")

def market_scan_func(watchlist: Optional[List[str]] = None) -> str:
    """
    Scans the market (or a watchlist) for trading opportunities.
    Returns a list of symbols with their current signal status (ACCUMULATE, WAIT, DISTRIBUTE).
    """
    try:
        results = pipeline.run_scanner(watchlist)
        # Format as a simple summary for the LLM
        summary = "Market Scan Results:\n"
        for r in results:
            summary += f"- {r['Symbol']}: {r['Signal']} (Conf: {r['Confidence']}, Regime: {r['Regime']})\n"
        return summary
    except Exception as e:
        return f"Error scanning market: {str(e)}"

market_scan_tool = StructuredTool.from_function(
    func=market_scan_func,
    name="scan_market",
    description="Useful for scanning the market to find potential trading opportunities across multiple stocks.",
    args_schema=MarketScanInput
)

from ..core.seasonality_engine import SeasonalityAnalyzer
from ..data.usa_api import TwelveDataAPI as USMarketAPI

class AnalyzeSeasonalityInput(BaseModel):
    symbol: str = Field(description="The stock symbol to analyze for seasonality (e.g., AAPL).")

def analyze_seasonality_func(symbol: str) -> str:
    """
    Performs a deterministic month-by-month seasonality analysis for 2021-2025.
    Returns tables of phases, opportunities, and summary statistics.
    """
    try:
        api = USMarketAPI()
        # Fetch sufficient history (5 years ~ 1260 days + buffer), daily interval
        df = api.get_live_data(symbol.upper(), interval="1day", outputsize=2000)
        
        if df is None or df.empty:
            return f"Error: No data found for {symbol}."
            
        # Fetch Earnings (Best Effort)
        earnings_df = api.get_earnings_dates(symbol.upper())
            
        analyzer = SeasonalityAnalyzer(df, earnings_df=earnings_df)
        report = analyzer.analyze(start_year=2021, end_year=2025)
        return report
        
    except Exception as e:
        return f"Error analyzing seasonality for {symbol}: {str(e)}"

analyze_seasonality_tool = StructuredTool.from_function(
    func=analyze_seasonality_func,
    name="analyze_seasonality",
    description="Generates a detailed year-by-year seasonality and opportunity report (2021-2025) for a given stock.",
    args_schema=AnalyzeSeasonalityInput
)
