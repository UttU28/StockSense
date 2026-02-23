import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
import traceback
import time
import re

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from stock_gita_engine_usa.data.usa_api import TwelveDataAPI
    from stock_gita_engine_usa.core.trend_engine import analyze_trend
    from stock_gita_engine_usa.core.forecast_engine import generate_forecast
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

st.set_page_config(page_title="Stock Gita AI", layout="centered")

# --- CUSTOM CSS FOR CHAT ---
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
    }
    .user-msg {
        background-color: #2b313e;
    }
    .bot-msg {
        background-color: #0e1117;
    }
</style>
""", unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am **Stock Gita AI**. \n\nYou can ask me:\n- *\"Analyze AAPL\"* (Full breakdown)\n- *\"Scan market\"* (Find opportunities)\n- *\"Risk 10000 on GOOGL\"* (Position Sizing)"}
    ]

# --- HELPER FUNCTIONS ---

def get_api():
    # Use environment var or default if not set in UI (simple for chat)
    return TwelveDataAPI()

def create_chart(symbol, df, forecast):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_width=[0.2, 0.7])

    # OHLC
    fig.add_trace(go.Candlestick(x=df['date'],
                    open=df['open'], high=df['high'],
                    low=df['low'], close=df['close'], name='Price'), row=1, col=1)

    # MAs
    if 'EMA_21' in df.columns: fig.add_trace(go.Scatter(x=df['date'], y=df['EMA_21'], line=dict(color='yellow', width=1), name='EMA 21'), row=1, col=1)
    if 'EMA_55' in df.columns: fig.add_trace(go.Scatter(x=df['date'], y=df['EMA_55'], line=dict(color='cyan', width=1), name='EMA 55'), row=1, col=1)

    # FORECAST CONE
    if forecast:
        last_date = pd.to_datetime(df['date'].iloc[-1])
        future_dates = [last_date + pd.Timedelta(days=i) for i in [1, 5, 20]]
        targets = {t.horizon: t for t in forecast.targets}
        
        upper_y = [forecast.current_price, targets["1 Day"].range_high, targets["1 Week"].range_high, targets["1 Month"].range_high]
        lower_y = [forecast.current_price, targets["1 Day"].range_low, targets["1 Week"].range_low, targets["1 Month"].range_low]
        mid_y =   [forecast.current_price, targets["1 Day"].target_price, targets["1 Week"].target_price, targets["1 Month"].target_price]
        x_dates = [last_date] + future_dates
        
        fig.add_trace(go.Scatter(x=x_dates, y=upper_y, line=dict(width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
        fig.add_trace(go.Scatter(x=x_dates, y=lower_y, fill='tonexty', fillcolor='rgba(0, 255, 255, 0.1)', 
                                    line=dict(width=0), name='Forecast Cone', hoverinfo='skip'), row=1, col=1)
        fig.add_trace(go.Scatter(x=x_dates, y=mid_y, line=dict(color='white', dash='dot', width=1), name='Target'), row=1, col=1)

    # Momentum
    if 'MACD_LINE' in df.columns:
            fig.add_trace(go.Bar(x=df['date'], y=df['MACD_HIST'], marker_color='gray', name='Hist'), row=2, col=1)

    fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0))
    return fig

def handle_analyze(symbol):
    api = get_api()
    with st.spinner(f"Analyzing {symbol}..."):
        df = api.get_live_data(symbol, interval="1day", outputsize=500)
        if df is None or df.empty:
            return f"❌ Could not fetch data for **{symbol}**."
        
        # Logic
        trend = analyze_trend(df)
        forecast = generate_forecast(df, trend['bias'], trend['confidence'], lookback_days=63)
        
        # Response Construction
        bias_color = "🟢" if trend['bias'] == "BULLISH" else "🔴" if trend['bias'] == "BEARISH" else "⚪"
        price = trend['indicators']['price']
        
        msg = f"### {bias_color} {symbol} Analysis\n"
        msg += f"**Price**: ${price:.2f} | **Trend**: {trend['bias']} ({trend['confidence']}%)\n\n"
        
        if forecast:
            drift = (forecast.targets[2].target_price - price) / price * 100
            msg += f"**Forecast (1M)**: Target ${forecast.targets[2].target_price:.2f} (Drift: {drift:+.1f}%)\n"
            msg += f"_The market suggests price will move between ${forecast.targets[2].range_low:.0f} and ${forecast.targets[2].range_high:.0f}._"
        
        st.session_state.messages.append({"role": "assistant", "content": msg})
        
        # Chart is special, we don't put it in text content usually but Streamlit chat allows widgets
        # We will append a special "chart" type message or just render it immediately?
        # Better: Render it immediately after appending text
        # But to keep history, we need to store it? Streamlit reruns.
        # Strategy: Store the figure in session state? No, to heavy.
        # Strategy: Just Re-render? 
        # For simplicity in this v1 chat: We will just output the chart to the stream now.
        # If we scroll up, it might be lost on refresh unless we persist 'actions'.
        # Let's persist basic text response, and interactive chart is ephemeral for the last request?
        # NO, user wants history.
        # Actually, st.chat_message container can hold charts.
        
        return {"type": "analysis", "symbol": symbol, "content": msg, "chart_data": (df, forecast)}

def handle_scan():
    watchlist = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META']
    api = get_api()
    results = []
    
    status_msg = st.empty()
    status_msg.write("🔎 Scanning 'Mag 7' assets...")
    
    progress = st.progress(0)
    
    for i, s in enumerate(watchlist):
        df = api.get_live_data(s, interval="1day", outputsize=200)
        if df is not None and not df.empty:
            t = analyze_trend(df)
            f = generate_forecast(df, t['bias'], t['confidence'], lookback_days=63)
            
            drift = 0
            if f:
                target_1m = [tgt for tgt in f.targets if tgt.horizon == "1 Month"][0]
                drift = (target_1m.target_price - f.current_price) / f.current_price * 100
            
            sig = "⚪ WAIT"
            if drift > 2 and t['bias'] == "BULLISH": sig = "🟢 BUY"
            elif drift < -2 and t['bias'] == "BEARISH": sig = "🔴 SELL"
            
            results.append({"Symbol": s, "Signal": sig, "Drift": f"{drift:+.1f}%", "Bias": t['bias']})
        progress.progress((i + 1) / len(watchlist))
    
    progress.empty()
    status_msg.empty()
    
    df_res = pd.DataFrame(results)
    return {"type": "table", "content": "### 📡 Market Scan Results", "data": df_res}

def handle_risk(text):
    # Try to parse "Risk 50000 on AAPL"
    match = re.search(r"risk\s+(\d+)\s+(?:on\s+)?([a-zA-Z]+)", text.lower())
    if match:
        capital = float(match.group(1))
        symbol = match.group(2).upper()
        
        api = get_api()
        df = api.get_live_data(symbol, interval="1day", outputsize=100)
        if df is None: return "Could not fetch data."
        
        # Get Volatility
        import pandas_ta as ta
        atr = ta.atr(df['high'], df['low'], df['close'], length=14).iloc[-1]
        price = df['close'].iloc[-1]
        
        # Logic: 1% Risk
        risk_amount = capital * 0.01
        stop_dist = 2 * atr
        shares = int(risk_amount / stop_dist)
        
        msg = f"### 🛡️ Risk Calculation: {symbol}\n"
        msg += f"**Account**: ${capital:,.0f} | **Risk**: 1% (${risk_amount:.0f})\n"
        msg += f"**Volatility (ATR)**: ${atr:.2f}\n\n"
        msg += f"👉 **BUY {shares} SHARES**\n"
        msg += f"🛑 **Stop Loss**: ${price - stop_dist:.2f} (Long) or ${price + stop_dist:.2f} (Short)"
        
        return {"type": "text", "content": msg}
        
    return {"type": "text", "content": "⚠️ Please use format: *Risk [AMOUNT] on [SYMBOL]*"}


# --- MAIN LOOP ---

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], str):
            st.markdown(msg["content"])
        elif isinstance(msg["content"], dict):
            # Complex message reconstruction
            if msg["content"]["type"] == "analysis":
                st.markdown(msg["content"]["content"])
                # We can't regenerate chart easily without data. 
                # For V1, we only show text history.
            elif msg["content"]["type"] == "table":
                st.markdown(msg["content"]["content"])
                st.dataframe(msg["content"]["data"])

# Input
if prompt := st.chat_input("Ask Stock Gita AI..."):
    # User Msg
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Bot Msg
    with st.chat_message("assistant"):
        response = None
        
        # ROUTER
        prompt_lower = prompt.lower()
        
        if "scan" in prompt_lower:
            response = handle_scan()
            st.markdown(response["content"])
            st.dataframe(response["data"])
            
        elif "risk" in prompt_lower:
            response = handle_risk(prompt)
            st.markdown(response["content"])
            
        elif "analyze" in prompt_lower or len(prompt.split()) == 1:
            # Assume symbol if 1 word, or explict analyze
            sym = prompt.split()[-1].upper() if "analyze" in prompt_lower else prompt.upper()
            response = handle_analyze(sym)
            if isinstance(response, str):
                st.markdown(response) # Error
            else:
                st.markdown(response["content"])
                # Render Chart Live
                fig = create_chart(response["symbol"], response["chart_data"][0], response["chart_data"][1])
                st.plotly_chart(fig, use_container_width=True)
                
                # We simplify the history storage for analysis to just text to save memory/complexity
                response = {"type": "text", "content": response["content"] + "\n\n*(Chart generated in live session)*"}
        
        else:
            response = {"type": "text", "content": "I didn't understand. Try **Analyze AAPL**, **Scan**, or **Risk 10000 on MSFT**."}
            st.markdown(response["content"])
            
        st.session_state.messages.append({"role": "assistant", "content": response})
