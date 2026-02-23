import sys
import os

# Ensure we can import from the deploy directory
sys.path.append(os.getcwd())

from stock_gita_engine_charts.llm.tools import analyze_stock_func

def test_pro_output(symbol="AAPL"):
    print(f"Running Stock Gita Pro Analysis for {symbol}...")
    try:
        report = analyze_stock_func(symbol)
        print("\n--- FINAL REPORT ---\n")
        print(report)
        print("\n--------------------\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_pro_output()
