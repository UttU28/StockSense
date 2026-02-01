import sys
import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import time
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import re
import json
import io
import pandas as pd
import mplfinance as mpf

# Add parent path import logic if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import config FIRST to ensure credentials are loaded at startup
# This will trigger credentials loading and logging immediately
from stock_gita_engine_charts.config import API_SOURCE

# Force credentials initialization at module import time if using Twelve Data
# This ensures logs appear BEFORE FastAPI startup messages
if API_SOURCE == "twelve":
    try:
        from stock_gita_engine_charts.data.credentials_manager import get_credentials_manager
        # Force initialization now, not later
        _ = get_credentials_manager()
        sys.stdout.flush()
    except Exception as e:
        print(f"Warning: Could not initialize credentials at import time: {e}")
        sys.stdout.flush()

from stock_gita_engine_charts.llm.agent import get_agent_executor
from stock_gita_engine_charts.llm.specialized_agents import get_master_agent, MASTER_PROMPT_EXPORT
from stock_gita_engine_charts.api_ticker import router as ticker_router
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from stock_gita_engine_charts.core.sli_detector import detect_sli
from stock_gita_engine_charts.data.usa_api import TwelveDataAPI as USMarketAPI

app = FastAPI(title="Stock Gita Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount ticker API router
app.include_router(ticker_router)

# Initialize credentials and API at startup
@app.on_event("startup")
async def startup_event():
    """Initialize credentials manager and API on startup."""
    import sys
    # Force initialization of credentials manager if using Twelve Data
    if API_SOURCE == "twelve":
        try:
            from stock_gita_engine_charts.data.credentials_manager import get_credentials_manager
            # This will trigger the credentials loading and logging
            # Flush stdout to ensure logs appear immediately
            sys.stdout.flush()
            cred_manager = get_credentials_manager()
            key_count = cred_manager.get_key_count()
            sys.stdout.flush()
            if key_count > 0:
                # Pre-initialize the API to ensure credentials are loaded
                _ = USMarketAPI()
                sys.stdout.flush()
        except Exception as e:
            print(f"Warning: Could not initialize credentials at startup: {e}")
            sys.stdout.flush()

# Initialize Agents
print("Initializing Agents...")
agents = {}
try:
    agents["default"] = get_agent_executor()
    agents["master"] = get_master_agent()
    print("All Agents Initialized Successfully.")
except Exception as e:
    print(f"FAILED to initialize agents: {e}")
    agents = {}

class Message(BaseModel):
    role: str
    content: str
    
    # Handle OpenAI-style messages where content might be missing or optional
    # Using Pydantic to ensure at least type integrity

class ChatCompletionRequest(BaseModel):
    model: str = "stock-gita-model"
    messages: List[Message]
    stream: bool = False

@app.get("/chart_v2", response_class=HTMLResponse)
async def get_chart_v2(symbol: str):
    print(f"Server HIT: /chart_v2?symbol={symbol}")
    
    # 1. Fetch Data
    api = USMarketAPI()
    try:
        df = api.get_live_data(symbol, interval="1day", outputsize=100)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return f"<html><body><h1>Error fetching data for {symbol}: {e}</h1></body></html>"
    
    if df is None or df.empty:
        return f"<html><body><h1>No data found for {symbol}</h1></body></html>"
    
    # 2. Detect Zones
    try:
        sli = detect_sli(df)
    except Exception as e:
        print(f"Error detecting zones: {e}")
        sli = {}
    
    # 3. Format Data for Lightweight Charts
    chart_data = []
    for index, row in df.iterrows():
        # Handle date. It might be timestamp or string.
        # usa_api.py returns 'date' column with datetime objects (tz-naive)
        dt_val = row['date']
        if hasattr(dt_val, 'strftime'):
            t_str = dt_val.strftime('%Y-%m-%d')
        else:
            t_str = str(dt_val).split(' ')[0] # Fallback for string
            
        chart_data.append({
            "time": t_str,
            "open": row['open'],
            "high": row['high'],
            "low": row['low'],
            "close": row['close']
        })
        
    data_json = json.dumps(chart_data)
    zones_json = json.dumps(sli)
    
    # 4. Render Template
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'chart_v2.html')
    if not os.path.exists(template_path):
        return "<html><body><h1>Template chart_v2.html not found</h1></body></html>"
        
    with open(template_path, 'r') as f:
        html_template = f.read()
        
    # Simple String Replacement
    html_content = html_template.replace('{{ tv_symbol }}', symbol) \
                                .replace('{{ data_json | safe }}', data_json) \
                                .replace('{{ zones_json | safe }}', zones_json)
                                
    return HTMLResponse(content=html_content)

import pandas_ta as ta
import mplfinance as mpf
import io
from fastapi.responses import StreamingResponse

# ... (Existing imports)

from stock_gita_engine_charts.core.sli_detector import detect_sli

@app.get("/chart_img")
async def get_chart_img(symbol: str):
    print(f"Server HIT: /chart_img?symbol={symbol}")
    
    # 1. Fetch Data
    api = USMarketAPI()
    try:
        df = api.get_live_data(symbol, interval="1day", outputsize=150) # Need more data for indicators
    except Exception as e:
        print(f"Error fetching data: {e}")
        return StreamingResponse(io.BytesIO(b""), media_type="image/png")

    if df is None or df.empty:
        return StreamingResponse(io.BytesIO(b""), media_type="image/png")

    # 2. Prepare Data
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Calculate Indicators
    # Bollinger Bands
    bb = df.ta.bbands(length=20, std=2)
    if bb is not None:
        df = pd.concat([df, bb], axis=1)
        
    # MACD
    macd = df.ta.macd(fast=12, slow=26, signal=9)
    if macd is not None:
        df = pd.concat([df, macd], axis=1)

    # Support/Resistance
    levels = detect_sli(df)
    supports = levels.get('support', [])
    resistances = levels.get('resistance', [])
    
    # Slice for plotting (Last 60 candles)
    plot_df = df.tail(60)

    # 3. Create AddPlots
    apds = []
    
    # Bollinger Bands (Panel 0 - Main)
    if bb is not None:
        # Columns: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
        # Use plot_df to ensure alignment
        apds.append(mpf.make_addplot(plot_df[bb.columns[0]], panel=0, color='gray', alpha=0.5, width=0.8)) # Lower
        apds.append(mpf.make_addplot(plot_df[bb.columns[2]], panel=0, color='gray', alpha=0.5, width=0.8)) # Upper

    # MACD (Panel 1)
    if macd is not None:
        # Columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        macd_col = macd.columns[0]
        hist_col = macd.columns[1]
        sig_col  = macd.columns[2]
        
        apds.append(mpf.make_addplot(plot_df[macd_col], panel=1, color='cyan', width=1, ylabel='MACD'))
        apds.append(mpf.make_addplot(plot_df[sig_col], panel=1, color='orange', width=1))
        apds.append(mpf.make_addplot(plot_df[hist_col], panel=1, type='bar', color='dimgray', alpha=0.5))

    # 4. Plot to Buffer
    buf = io.BytesIO()
    
    # Custom Style
    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
    s  = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, rc={'axes.labelsize': 8, 'grid.linestyle': ':'})
    
    # Prepare HLines
    h_lines = []
    h_colors = []
    
    # Use unique/clustered levels from the FULL calculation, but only plot if in range? 
    # Actually hlines are global Y-levels, so they work regardless of X-axis. Used calculated supports.
    
    for s_level in supports[-3:]: 
        h_lines.append(s_level)
        h_colors.append('lime')
        
    for r_level in resistances[-3:]:
        h_lines.append(r_level)
        h_colors.append('red')

    # Kwargs
    filesave_args = dict(fname=buf, dpi=100, bbox_inches='tight')
    
    try:
        if h_lines:
             mpf.plot(plot_df, type='candle', style=s, volume=False, addplot=apds,
                     hlines=dict(hlines=h_lines, colors=h_colors, linewidths=1.0, alpha=0.7),
                     title=f"\n{symbol} Analysis (MACD + BB + Levels)",
                     panel_ratios=(6, 2),
                     savefig=filesave_args)
        else:
             mpf.plot(plot_df, type='candle', style=s, volume=False, addplot=apds,
                     title=f"\n{symbol} Analysis (MACD + BB)",
                     panel_ratios=(6, 2),
                     savefig=filesave_args)
    except Exception as ie:
        print(f"Plot Error: {ie}")
        # Fallback basic plot
        mpf.plot(plot_df, type='candle', style=s, savefig=filesave_args)

    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@app.get("/")
async def root():
    return {"message": "Stock Gita API Root"}

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "stock-gita-pro",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "stock-gita",
                "permission": [{"id": "modelperm-default"}]
            },
            {
                "id": "stock-gita-seasonality",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "stock-gita",
                 "permission": [{"id": "modelperm-seas"}]
            },
            {
                "id": "stock-gita-master",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "stock-gita",
                 "permission": [{"id": "modelperm-master"}]
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    # Extract last user message
    last_user_msg_content = "Unknown"
    for m in reversed(request.messages):
        if m.role == 'user':
            last_user_msg_content = m.content
            break
            
    print(f"Received Request: {last_user_msg_content[:50]}... Model: {request.model}")
    
    # 1. Select Agent and System Prompt Injection logic
    selected_agent = agents.get("default")
    override_system_prompt = None

    if request.model == "stock-gita-master":
        selected_agent = agents.get("master")
        # Fallback: Inject system prompt manually in case create_react_agent didn't accept it
        override_system_prompt = MASTER_PROMPT_EXPORT
    elif "seasonality" in request.model:
        # Fallback for legacy request - Seasonality logic is actually baked into tools or handled via prompt override
        # Wait, get_agent_executor returns the generic agent.
        # Seasonality logic IS usually applied via override prompt on the DEFAULT agent unless we made a dedicated one.
        # The previous code used override_system_prompt on default agent for seasonality. We'll keep that.
        selected_agent = agents.get("default")
        override_system_prompt = """You are a stock behavior analyst.
        
        The user wants a deterministic seasonality report.
        
        **YOUR JOB:**
        1. Call the tool `analyze_seasonality` with the requested symbol.
        2. OUTPUT THE RESULT EXACTLY AS IS.
        3. Do NOT change the table formats or text.
        
        If the user asks for a market scan or technical analysis, politely redirect them to use the 'stock-gita-pro' model.
        """
    else:
        # Default PRO
        selected_agent = agents.get("default")
        override_system_prompt = """You are the Stock Gita AI.
        
        The tool `analyze_stock` returns a pre-formatted, PROFESSIONAL MARKDOWN REPORT.
        
        **YOUR JOB:**
        1. Call the tool `analyze_stock`.
        2. OUTPUT THE RESULT EXACTLY AS IS.
        3. Do NOT change the formatting, tables, or icons.
        4. Do NOT summarize or "prettify" it. The tool output is already perfect.
        
        Just present the report to the user.
        """

    if not selected_agent:
        return {
            "id": "error",
            "choices": [{"message": {"content": "Agent initialization failed. Check server logs."}}]
        }

    # CMS: Convert OpenAI messages to LangChain messages
    lc_messages = []
    
    # Inject override system prompt if needed (for default agents)
    # The specialized agents have it baked in via _create_base_agent
    if override_system_prompt:
         lc_messages.append(SystemMessage(content=override_system_prompt))

    for m in request.messages:
        content = m.content
        if m.role == 'user':
            lc_messages.append(HumanMessage(content=content))
        elif m.role == 'assistant':
            lc_messages.append(AIMessage(content=content))
        elif m.role == 'system':
             # If using specialized agent (Master), ignore external system prompt if it conflicts?
             # Actually, Master agent has state_modifier baked in. 
             # LangGraph handles appending prompts. But if we append SystemMessage here, it might act as a second system message.
             # Safe to append.
             lc_messages.append(SystemMessage(content=content))
            
    # Invoke Agent
    inputs = {"messages": lc_messages}
    
    import random
    import asyncio
    
    max_retries = 5
    base_delay = 1
    response_content = "Error processing request."
    
    for attempt in range(max_retries):
        try:
            if not selected_agent:
                response_content = "Agent not initialized."
                break
                
            result = await selected_agent.ainvoke(inputs)
            last_message = result["messages"][-1]
            response_content = last_message.content
            break # Success
        except Exception as e:
            if "ThrottlingException" in str(e) and attempt < max_retries - 1:
                delay = (base_delay * (2 ** attempt)) + (random.randint(0, 1000) / 1000)
                print(f"Throttling detected. Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(delay)
            else:
                print(f"Error executing agent: {e}")
                response_content = f"Error executing agent (after {attempt+1} attempts): {str(e)}"
                if "ThrottlingException" in str(e):
                    response_content += "\n\n**System Note:** The AI model is currently experiencing high load. Please wait a moment and try again."
                break
    
    # --- Chart Injection ---
    # Moved to tools.py for deterministic rendering inside the tool output.
    # match = re.search(r'\b(?:Analyze|Chart|Check)\s+([A-Za-z]{1,5})\b', last_user_msg_content, re.IGNORECASE)
    # ... code removed ...

    # Construct OpenAI Response Object
    response = {
        "id": "chatcmpl-" + str(int(time.time())),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }
    
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
