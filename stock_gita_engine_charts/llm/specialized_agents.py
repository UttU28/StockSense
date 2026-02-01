from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent
# Import shared tools
from .tools import analyze_stock_tool, market_scan_tool, analyze_seasonality_tool
from .agent_prompts import MASTER_TRADER_PROMPT
import boto3

REGION = "us-east-1"

def get_master_agent():
    """
    Returns a pre-configured LangGraph agent with the Master Trader system prompt.
    Uses 'prompt' kwarg if available, otherwise falls back.
    """
    client = boto3.client(
        service_name="bedrock-runtime",
        region_name=REGION
    )

    llm = ChatBedrock(
        client=client,
        model_id="us.anthropic.claude-opus-4-5-20251101-v1:0",
        model_kwargs={"temperature": 0.1, "max_tokens": 8000}
    )
    
    tools = [analyze_stock_tool, market_scan_tool, analyze_seasonality_tool]
    
    # Try different kwarg names depending on LangGraph version
    try:
        # Newer LangGraph might use 'prompt'
        graph = create_react_agent(llm, tools, prompt=MASTER_TRADER_PROMPT)
    except TypeError:
        try:
            # Older might use 'state_modifier'
            graph = create_react_agent(llm, tools, state_modifier=MASTER_TRADER_PROMPT)
        except TypeError:
            # Fallback: no system prompt baked in, will rely on api_bridge
            graph = create_react_agent(llm, tools)
    
    return graph

# Also export the prompt so api_bridge can use it as fallback
MASTER_PROMPT_EXPORT = MASTER_TRADER_PROMPT
