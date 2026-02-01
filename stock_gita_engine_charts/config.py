import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration
API_SOURCE = os.getenv("API_SOURCE", "yahoo").lower()  # yahoo or twelve

# Validate API_SOURCE
if API_SOURCE not in ["yahoo", "twelve"]:
    print(f"Warning: Invalid API_SOURCE '{API_SOURCE}'. Defaulting to 'yahoo'")
    API_SOURCE = "yahoo"

# Load credentials manager for Twelve Data (lazy import to avoid circular dependency)
TWELVE_DATA_KEY_COUNT = 0
if API_SOURCE == "twelve":
    try:
        from stock_gita_engine_charts.data.credentials_manager import get_credentials_manager
        cred_manager = get_credentials_manager()
        TWELVE_DATA_KEY_COUNT = cred_manager.get_key_count()
        
        if TWELVE_DATA_KEY_COUNT == 0:
            print("Warning: API_SOURCE is set to 'twelve' but no API keys found in credentials.json. Falling back to 'yahoo'")
            API_SOURCE = "yahoo"
        else:
            print(f"[OK] API Source: Twelve Data (using {TWELVE_DATA_KEY_COUNT} API key(s) from credentials.json)")
    except Exception as e:
        print(f"Error loading credentials: {e}. Falling back to 'yahoo'")
        API_SOURCE = "yahoo"

if API_SOURCE == "yahoo":
    print("[OK] API Source: Yahoo Finance (free tier)")

# Trading Settings
DEFAULT_TIMEFRAME = "1day"
MARKET_COUNTRY = "USA"

# Indices to watch
INDICES = {
    "PRIMARY": "SPY", # S&P 500 ETF
    "TECH": "QQQ",    # Nasdaq 100 ETF
    "IND": "DIA"      # Dow Jones ETF
}
