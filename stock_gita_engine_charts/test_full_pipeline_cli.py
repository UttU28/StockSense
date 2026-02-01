from stock_gita_engine_charts.core.pipelines import TradingPipeline
import json

def test_pipeline():
    print("Initializing Pipeline...")
    pipeline = TradingPipeline()
    
    symbol = "AAPL"
    print(f"Running analysis for {symbol}...")
    
    result = pipeline.run_full_analysis(symbol)
    
    # Remove raw data for printing
    if "_raw_df" in result: del result["_raw_df"]
    if "_raw_indicators" in result: del result["_raw_indicators"]
    
    print("\n--- ANALYSIS RESULT ---")
    print(json.dumps(result, indent=2, default=str))
    
    if "error" in result:
        print("\n❌ PIPELINE FAILED")
    else:
        print("\n✅ PIPELINE SUCCESS")

if __name__ == "__main__":
    test_pipeline()
