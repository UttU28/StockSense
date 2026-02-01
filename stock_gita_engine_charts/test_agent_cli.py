from stock_gita_engine_charts.llm.agent import get_agent_executor
from langchain_core.messages import HumanMessage

def test_agent():
    print("Initializing Gemini Agent (LangGraph)...")
    try:
        agent = get_agent_executor()
        
        query = "Analyze IBM"
        print(f"invoking agent with: '{query}'...")
        
        inputs = {"messages": [HumanMessage(content=query)]}
        result = agent.invoke(inputs)
        
        print("\n--- AGENT RESPONSE ---")
        print(result["messages"][-1].content)
        print("\n✅ AGENT TEST SUCCESS")
        
    except Exception as e:
        print(f"\n❌ AGENT TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent()
