import sys
import os

# Ensure we can import the module
sys.path.append('/app')

try:
    from stock_gita_engine_charts.llm.tools import analyze_stock_tool
    print("Running Analysis for AAPL to verify UI format...")
    # Mocking the input as it expects a dict or object depending on invocation, but .run() usually handles dict
    result = analyze_stock_tool.run({"symbol": "AAPL"})
    
    print("\n--- GENERATED REPORT START ---")
    print(result)
    print("--- GENERATED REPORT END ---")
    
except Exception as e:
    print(f"Error running verification: {e}")
    import traceback
    traceback.print_exc()
