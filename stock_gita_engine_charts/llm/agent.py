from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent
from .tools import analyze_stock_tool, market_scan_tool, analyze_seasonality_tool
import os
import boto3

# Credentials from environment / default profile
REGION = "us-east-1" # Defaulting to us-east-1

def get_agent_executor():
    # Setup Boto3 Client using default profile/credentials
    client = boto3.client(
        service_name="bedrock-runtime",
        region_name=REGION
    )

    # Load LLM (Claude 3 Haiku or Sonnet is good standard for Bedrock)
    # Using 'anthropic.claude-3-sonnet-20240229-v1:0'
    llm = ChatBedrock(
        client=client,
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        model_kwargs={"temperature": 0, "max_tokens": 8000}
    )
    
    tools = [analyze_stock_tool, market_scan_tool, analyze_seasonality_tool]
    
    # Create Agent using LangGraph
    graph = create_react_agent(llm, tools)
    
    return graph
