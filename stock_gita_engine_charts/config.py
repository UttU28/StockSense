import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# API Keys
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "e5268126b04d4b1b81ad6189ae8cad75")
MASSIVE_API_KEY = os.getenv("MASSIVE_API_KEY", "goq3h_VFUITfqYyeWReAtgsyZv5Y7PVC")

# Trading Settings
DEFAULT_TIMEFRAME = "1day"
MARKET_COUNTRY = "USA"

# Indices to watch
INDICES = {
    "PRIMARY": "SPY", # S&P 500 ETF
    "TECH": "QQQ",    # Nasdaq 100 ETF
    "IND": "DIA"      # Dow Jones ETF
}
