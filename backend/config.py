import os

ALPHA_VANTAGE_API_KEY = "94JNVF7WRZI5SUAO" # Hardcoded from workspace for now, or use os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query?"

# Rate Limiting
# Free tier: 25 calls/day (actually often 5/min, 500/day, but user requested respecting strict limits)
# User mentioned "respect 25 calls/day free tier" in requirements, but standard free is usually higher.
# We will be conservative to avoid issues.
CALL_DELAY_SECONDS = 15 

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
DB_PATH = os.path.join(CACHE_DIR, "gs_data.db")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)
