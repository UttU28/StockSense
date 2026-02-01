import chainlit as cl
import sys
import os

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from stock_gita_engine_usa.llm.agent import get_agent_executor
from langchain_core.messages import HumanMessage

@cl.on_chat_start
async def start():
    # Initialize the Agent
    try:
        agent_executor = get_agent_executor()
        cl.user_session.set("agent", agent_executor)
        
        await cl.Message(
            content="**Hello! I am Stock Gita AI (Agent Mode).**\nI can analyze stocks using the comprehensive 10-module framework.\n\nTry asking:\n- *Analyze NVDA*\n- *Scan the market for opportunities*\n- *Is it a good time to buy AAPL?*"
        ).send()
    except Exception as e:
        await cl.Message(
            content=f"**Error Initializing Agent**: {e}\n\nPlease ensure `OPENAI_API_KEY` is set in your environment."
        ).send()

@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")
    if not agent:
        await cl.Message(content="Agent not initialized.").send()
        return

    # Call the Agent (LangGraph)
    # Input: dictionary with 'messages'
    # We use HumanMessage for better typing
    from langchain_core.messages import HumanMessage
    
    inputs = {"messages": [HumanMessage(content=message.content)]}
    
    res = await cl.make_async(agent.invoke)(
        inputs,
        config={"callbacks": [cl.LangchainCallbackHandler()]}
    )
    
    # LangGraph returns state dict with 'messages' list
    # The last message is the AI response
    last_message = res["messages"][-1]
    response_content = last_message.content
    
    
    await cl.Message(content=response_content).send()
    
    # --- Chart Integration ---
    import re
    from stock_gita_engine_charts.ui.chart_gen import get_tradingview_chart
    
    # Try Regex detection for "Analyze SYMBOL" or similar intent
    match = re.search(r'\b(?:Analyze|Chart|Check)\s+([A-Za-z]{1,5})\b', message.content, re.IGNORECASE)
    if match:
        symbol = match.group(1).upper()
        # Generates the HTML
        html_content = get_tradingview_chart(symbol)
        
        # Send as a separate message containing the HTML
        # We rely on Chainlit markdown rendering HTML (requires unsafe_allow_html=true)
        await cl.Message(
            content=html_content
        ).send()

