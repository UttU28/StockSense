import os
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from config import ALPHA_VANTAGE_API_KEY, BASE_URL, CALL_DELAY_SECONDS, DB_PATH
from data_layer import DataLayer
from models import DailyBar, WeeklyBar, EarningsRecord

def fetchApiData(function: str, symbol: str, apiKey: str, outputSize: Optional[str] = None, **kwargs) -> Optional[Dict[str, Any]]:
    """Fetch data from Alpha Vantage API."""
    params = {"function": function, "symbol": symbol, "apikey": apiKey, **kwargs}
    if outputSize:
        params["outputsize"] = outputSize
    
    url = BASE_URL
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "Error Message" in data:
            print(f"  ✗ API Error: {data['Error Message']}")
            return None
        
        if "Note" in data:
            note_lower = data["Note"].lower()
            if "rate limit" in note_lower or "premium" in note_lower:
                print(f"  ✗ API Note: {data['Note']}")
                return None
            else:
                print(f"  ⚠ API Note: {data['Note']}")
        
        # Check if we got actual data
        has_data = False
        for key in data.keys():
            if "Time Series" in key or "Technical Analysis" in key or "quarterlyEarnings" in key or "annualEarnings" in key:
                has_data = True
                break
        
        if not has_data:
            print(f"  ⚠ Warning: No data found in response. Keys: {list(data.keys())[:5]}")
        
        time.sleep(CALL_DELAY_SECONDS)
        return data
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Request failed: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return None

def fetchAndStore5YearHistory(symbol: str, apiKey: str) -> bool:
    """
    Fetch complete 5-year historical data for a symbol and store in database.
    Fetches: Daily bars, Weekly bars, Daily indicators, Weekly indicators, Earnings
    """
    symbol = symbol.upper()
    # Initialize database and create tables if not exist
    dataLayer = DataLayer()
    
    print(f"\n{'='*60}")
    print(f"Fetching 5-year history for {symbol}")
    print(f"{'='*60}\n")
    
    successCount = 0
    totalSteps = 8
    
    # 1. Fetch and store Daily Bars (5 years)
    print(f"[1/{totalSteps}] Fetching daily bars...")
    print(f"  ⚠ Note: Free tier only gives ~100 days. Full 5y requires premium API key.")
    dailyData = fetchApiData("TIME_SERIES_DAILY", symbol, apiKey, "compact")
    
    # Check if we got daily data or need to use weekly
    gotDailyData = False
    dailyBarsToStore = []
    
    if dailyData and "Time Series (Daily)" in dailyData:
        dailyBars = dataLayer._parse_daily_bars(dailyData)
        if dailyBars:
            # Filter to 5 years (but free tier only has ~100 days)
            fiveYearsAgo = datetime.now() - timedelta(days=5*365)
            filteredBars = [b for b in dailyBars if datetime.strptime(b.date, "%Y-%m-%d") >= fiveYearsAgo]
            
            # ALWAYS store daily bars we get (even if only 100 days)
            if filteredBars:
                dataLayer.store_daily_bars(symbol, filteredBars)
                dailyBarsToStore = filteredBars
                print(f"  ✓ Stored {len(filteredBars)} daily bars")
                successCount += 1
                gotDailyData = True
                
                if len(filteredBars) < 200:  # Less than ~1 year of trading days
                    print(f"  ⚠ Only {len(filteredBars)} days available (free tier limit). Fetching weekly for 5-year coverage...")
                    time.sleep(CALL_DELAY_SECONDS)
    
    # If daily failed or insufficient, use weekly for 5-year coverage
    if not gotDailyData:
        if dailyData and "Information" in dailyData:
            info_lower = dailyData["Information"].lower()
            if "premium" in info_lower:
                print(f"  ⚠ Premium API key required for full daily history")
        else:
            print(f"  ⚠ Daily data unavailable or insufficient")
        
        print(f"  → Using weekly data for 5-year coverage...")
        weeklyData = fetchApiData("TIME_SERIES_WEEKLY", symbol, apiKey)
        if weeklyData and "Weekly Time Series" in weeklyData:
            weeklyBars = dataLayer._parse_weekly_bars(weeklyData)
            if weeklyBars:
                fiveYearsAgo = datetime.now() - timedelta(days=5*365)
                filteredBars = [b for b in weeklyBars if datetime.strptime(b.date, "%Y-%m-%d") >= fiveYearsAgo]
                dataLayer.store_weekly_bars(symbol, filteredBars)
                print(f"  ✓ Stored {len(filteredBars)} weekly bars (5 years)")
                successCount += 1
            else:
                print(f"  ✗ Failed to parse weekly bars")
        else:
            print(f"  ✗ Failed to fetch weekly bars")
    
    # 2. Fetch and store Weekly Bars (5 years)
    print(f"[2/{totalSteps}] Fetching weekly bars (5 years)...")
    weeklyData = fetchApiData("TIME_SERIES_WEEKLY", symbol, apiKey)
    if weeklyData and "Weekly Time Series" in weeklyData:
        weeklyBars = dataLayer._parse_weekly_bars(weeklyData)
        if weeklyBars:
            # Filter to 5 years
            fiveYearsAgo = datetime.now() - timedelta(days=5*365)
            filteredBars = [b for b in weeklyBars if datetime.strptime(b.date, "%Y-%m-%d") >= fiveYearsAgo]
            dataLayer.store_weekly_bars(symbol, filteredBars)
            print(f"  ✓ Stored {len(filteredBars)} weekly bars")
            successCount += 1
        else:
            print(f"  ✗ Failed to parse weekly bars")
    else:
        print(f"  ✗ Failed to fetch weekly bars")
    
    # 3. Fetch and store Daily RSI
    print(f"[3/{totalSteps}] Fetching daily RSI...")
    rsiDailyData = fetchApiData("RSI", symbol, apiKey, interval="daily", time_period=14, series_type="close")
    rsiDailyParsed = dataLayer._parse_technical(rsiDailyData, "RSI") if rsiDailyData else {}
    
    # 4. Fetch and store Daily STOCHRSI
    print(f"[4/{totalSteps}] Fetching daily STOCHRSI...")
    stochRsiData = fetchApiData("STOCHRSI", symbol, apiKey, interval="daily", time_period=14, 
                                series_type="close", fastkperiod=5, fastdperiod=3, fastdmatype=1)
    stochRsiParsed = dataLayer._parse_technical(stochRsiData, "STOCHRSI") if stochRsiData else {}
    
    # 5. Calculate and store Daily MACD (from bars, not API)
    print(f"[5/{totalSteps}] Calculating daily MACD from price data...")
    macdDailyParsed = {}
    
    # Get daily bars from DB or use what we just fetched
    if dailyBarsToStore:
        barsToUse = dailyBarsToStore
    else:
        barsToUse = dataLayer.get_daily_bars(symbol)
    
    if barsToUse and len(barsToUse) >= 35:
        macdDailyParsed = dataLayer.calculate_macd_for_all_dates(barsToUse)
        if macdDailyParsed:
            print(f"  ✓ Calculated MACD for {len(macdDailyParsed)} dates")
        else:
            print(f"  ⚠ Warning: MACD calculation failed")
    else:
        print(f"  ⚠ Warning: Not enough daily bars for MACD calculation (need 35+, have {len(barsToUse) if barsToUse else 0})")
    
    # Store all daily indicators together
    if rsiDailyParsed or stochRsiParsed or macdDailyParsed:
        dataLayer.store_daily_indicators(symbol, rsiDailyParsed, stochRsiParsed, macdDailyParsed)
        indicatorCount = max(len(rsiDailyParsed) if rsiDailyParsed else 0, 
                           len(stochRsiParsed) if stochRsiParsed else 0, 
                           len(macdDailyParsed) if macdDailyParsed else 0)
        print(f"  ✓ Stored {indicatorCount} daily indicator records")
        successCount += 1
    else:
        print(f"  ✗ No daily indicators to store")
    
    # 6. Fetch and store Weekly RSI
    print(f"[6/{totalSteps}] Fetching weekly RSI...")
    rsiWeeklyData = fetchApiData("RSI", symbol, apiKey, interval="weekly", time_period=14, series_type="close")
    rsiWeeklyParsed = dataLayer._parse_technical(rsiWeeklyData, "RSI") if rsiWeeklyData else {}
    
    # 7. Calculate and store Weekly MACD (from bars, not API)
    print(f"[7/{totalSteps}] Calculating weekly MACD from price data...")
    macdWeeklyParsed = {}
    
    # Get weekly bars from DB or use what we just fetched
    weeklyBarsForMacd = dataLayer.get_weekly_bars(symbol)
    if not weeklyBarsForMacd:
        # Try to get from the weekly data we just fetched
        if weeklyData and "Weekly Time Series" in weeklyData:
            weeklyBarsForMacd = dataLayer._parse_weekly_bars(weeklyData)
    
    if weeklyBarsForMacd and len(weeklyBarsForMacd) >= 35:
        macdWeeklyParsed = dataLayer.calculate_macd_for_weekly(weeklyBarsForMacd)
        if macdWeeklyParsed:
            print(f"  ✓ Calculated MACD for {len(macdWeeklyParsed)} weekly dates")
        else:
            print(f"  ⚠ Warning: Weekly MACD calculation failed")
    else:
        print(f"  ⚠ Warning: Not enough weekly bars for MACD calculation (need 35+, have {len(weeklyBarsForMacd) if weeklyBarsForMacd else 0})")
    
    # Store all weekly indicators together
    if rsiWeeklyParsed or macdWeeklyParsed:
        dataLayer.store_weekly_indicators(symbol, rsiWeeklyParsed, macdWeeklyParsed)
        indicatorCount = max(len(rsiWeeklyParsed) if rsiWeeklyParsed else 0, 
                           len(macdWeeklyParsed) if macdWeeklyParsed else 0)
        print(f"  ✓ Stored {indicatorCount} weekly indicator records")
        successCount += 1
    else:
        print(f"  ✗ No weekly indicators to store")
    
    # 8. Fetch and store Earnings
    print(f"[8/{totalSteps}] Fetching earnings data...")
    earningsData = fetchApiData("EARNINGS", symbol, apiKey)
    if earningsData:
        earningsRecords = dataLayer._parse_earnings(earningsData)
        if earningsRecords:
            dataLayer.store_earnings(symbol, earningsRecords)
            print(f"  ✓ Stored {len(earningsRecords)} earnings records")
            successCount += 1
        else:
            print(f"  ✗ Failed to parse earnings")
    else:
        print(f"  ✗ Failed to fetch earnings")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Completed: {successCount}/{totalSteps} steps successful")
    print(f"{'='*60}\n")
    
    return successCount == totalSteps

def updateDailyDataIncremental(symbol: str, apiKey: str) -> dict:
    """
    Incremental daily update: Fetch latest ~100 days and store only new/missing days.
    This is the day-to-day update method.
    """
    symbol = symbol.upper()
    # Initialize database and create tables if not exist
    dataLayer = DataLayer()
    
    print(f"\n{'='*60}")
    print(f"Incremental daily update for {symbol}")
    print(f"{'='*60}\n")
    
    # Check what we already have
    latestDate = dataLayer.get_latest_date(symbol, "daily_bars")
    print(f"Latest date in database: {latestDate or 'None (empty database)'}")
    
    # Fetch latest ~100 days from API (compact)
    print("Fetching latest ~100 days from API...")
    dailyData = fetchApiData("TIME_SERIES_DAILY", symbol, apiKey, "compact")
    
    if not dailyData or "Time Series (Daily)" not in dailyData:
        print(f"  ✗ Failed to fetch daily data")
        return {"updated": False, "new_days_added": 0}
    
    # Parse the bars
    fetchedBars = dataLayer._parse_daily_bars(dailyData)
    if not fetchedBars:
        print(f"  ✗ Failed to parse daily bars")
        return {"updated": False, "new_days_added": 0}
    
    print(f"  ✓ Fetched {len(fetchedBars)} days from API")
    
    # Filter to only new bars (if we have existing data)
    if latestDate:
        latestDateDt = datetime.strptime(latestDate, "%Y-%m-%d")
        newBars = [b for b in fetchedBars if datetime.strptime(b.date, "%Y-%m-%d") > latestDateDt]
    else:
        # No existing data, store all
        newBars = fetchedBars
    
    if newBars:
        # Store new bars (INSERT OR REPLACE handles updates if dates overlap)
        dataLayer.store_daily_bars(symbol, newBars)
        print(f"  ✓ Stored {len(newBars)} new days")
        
        # Calculate and store MACD for all daily bars (including new ones)
        print("  Calculating MACD from all daily bars...")
        allDailyBars = dataLayer.get_daily_bars(symbol)
        if allDailyBars and len(allDailyBars) >= 35:
            macdCalculated = dataLayer.calculate_macd_for_all_dates(allDailyBars)
            if macdCalculated:
                # Get existing RSI and STOCHRSI to merge (empty for now, can fetch if needed)
                rsiData = {}
                stochRsiData = {}
                # Store MACD (will merge with existing indicators)
                dataLayer.store_daily_indicators(symbol, rsiData, stochRsiData, macdCalculated)
                print(f"  ✓ Calculated and stored MACD for {len(macdCalculated)} dates")
        
        print(f"  Latest date now: {dataLayer.get_latest_date(symbol, 'daily_bars')}")
        return {"updated": True, "new_days_added": len(newBars), "total_fetched": len(fetchedBars)}
    else:
        print(f"  ✓ Already up to date (no new data)")
        return {"updated": False, "new_days_added": 0, "total_fetched": len(fetchedBars)}

if __name__ == "__main__":
    import sys
    
    # Ensure database and tables are initialized
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    DataLayer()  # Initialize database and create tables
    
    apiKey = ALPHA_VANTAGE_API_KEY
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scraping5y.py SYMBOL              # Full 5-year history fetch")
        print("  python scraping5y.py SYMBOL --update     # Incremental daily update")
        print("  python scraping5y.py --update SYMBOL     # Incremental daily update (alternative)")
        print("\nExample:")
        print("  python scraping5y.py AAPL")
        print("  python scraping5y.py AAPL --update")
        sys.exit(1)
    
    # Check if --update flag is present
    args = sys.argv[1:]
    isUpdate = "--update" in args
    
    if isUpdate:
        args.remove("--update")
    
    if not args:
        print("Error: Please provide a symbol")
        sys.exit(1)
    
    symbol = args[0].upper()
    
    if isUpdate:
        # Incremental daily update
        print(f"Starting incremental daily update for {symbol}")
        print(f"This will fetch latest ~100 days and store only new data\n")
        result = updateDailyDataIncremental(symbol, apiKey)
        
        if result["updated"]:
            print(f"\n✅ Successfully updated: Added {result['new_days_added']} new days")
        else:
            print(f"\n✅ Already up to date (no new data)")
    else:
        # Full 5-year history fetch
        print(f"Starting 5-year historical data fetch for {symbol}")
        print(f"This will take approximately 2 minutes (8 API calls with rate limiting)\n")
        
        success = fetchAndStore5YearHistory(symbol, apiKey)
        
        if success:
            print(f"✅ Successfully stored complete 5-year history for {symbol}")
        else:
            print(f"⚠️  Some data may be missing for {symbol}. Check logs above.")
