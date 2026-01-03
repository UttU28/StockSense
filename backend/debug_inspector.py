import sqlite3
import json
from config import DB_PATH

def debug():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check TIME_SERIES_DAILY
    # Key format: TIME_SERIES_DAILY_AAPL_{"outputsize": "full"}
    key_suffix = '{"outputsize": "full"}'
    c.execute("SELECT key, data FROM api_cache WHERE key LIKE ?", ('%TIME_SERIES_DAILY%' + key_suffix,))
    row = c.fetchone()
    if row:
        print(f"Found Cache Key: {row[0]}")
        data = json.loads(row[1])
        print(f"Keys in JSON: {list(data.keys())}")
        if "Time Series (Daily)" in data:
             print("Found 'Time Series (Daily)'")
             ts = data["Time Series (Daily)"]
             print(f"Num Days: {len(ts)}")
             print(f"Sample Entry: {list(ts.items())[0]}")
        elif "Note" in data:
            print(f"NOTE in data: {data['Note']}")
        elif "Information" in data:
            print(f"INFO in data: {data['Information']}")
        else:
            print(f"Unexpected JSON structure: {data}")
    else:
        print("No cache found for TIME_SERIES_DAILY (full)")
    
    conn.close()

if __name__ == "__main__":
    debug()
