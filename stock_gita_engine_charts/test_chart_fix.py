
import sys
import os

# Add project root to path
sys.path.append("/Users/vits/Desktop/trading")

try:
    from stock_gita_engine_charts.ui.chart_gen import get_chart_html_content
    html = get_chart_html_content("NVDA")
    if "<!DOCTYPE html>" in html and "new TradingView.widget" in html:
        print("SUCCESS: Chart generation works correctly.")
    else:
        print("FAILURE: Chart generation output seems incorrect.")
except Exception as e:
    print(f"CRITICAL FAILURE: {e}")
    sys.exit(1)
