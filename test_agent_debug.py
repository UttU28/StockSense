import sys
import asyncio
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_gita_engine_charts.llm.agent import get_agent_executor
from langchain_core.messages import HumanMessage

async def main():
    print("Initializing Agent...")
    try:
        agent = get_agent_executor()
    except Exception as e:
        print(f"Failed to init agent: {e}")
        return

    msg = HumanMessage(content="Analyze AAPL")
    inputs = {"messages": [msg]}
    
    print("Invoking Agent...")
    try:
        result = await agent.ainvoke(inputs)
        print("Agent Response:")
        print(result["messages"][-1].content)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
