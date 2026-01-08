import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from config import ALPHA_VANTAGE_API_KEY, BASE_URL, CALL_DELAY_SECONDS, DB_PATH
from data_layer import DataLayer
from models import DailyBar, WeeklyBar

def fetchApiData(function: str, symbol: str, apiKey: str, outputSize: str = None, **kwargs) -> Dict[str, Any]:
    """Fetch data from Alpha Vantage API."""
    params = {"function": function, "symbol": symbol, "apikey": apiKey, **kwargs}
    if outputSize:
        params["outputsize"] = outputSize
    
    try:
        import requests
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "Error Message" in data:
            return None
        if "Note" in data:
            noteLower = data["Note"].lower()
            if "rate limit" in noteLower or "premium" in noteLower:
                return None
        
        time.sleep(CALL_DELAY_SECONDS)
        return data
    except Exception as e:
        return None

def updateDailyBars(symbol: str, dataLayer: DataLayer, apiKey: str) -> Dict[str, Any]:
    """Check daily bars every day, update only if new data available."""
    latestDateInDb = dataLayer.get_latest_date(symbol, "daily_bars")
    
    # Always fetch latest data to check
    dailyData = fetchApiData("TIME_SERIES_DAILY", symbol, apiKey, "compact")
    if not dailyData or "Time Series (Daily)" not in dailyData:
        return {"success": False, "newDays": 0, "updated": False, "reason": "API fetch failed"}
    
    fetchedBars = dataLayer._parse_daily_bars(dailyData)
    if not fetchedBars:
        return {"success": False, "newDays": 0, "updated": False, "reason": "Parse failed"}
    
    # Get latest date from fetched data
    latestDateFromApi = fetchedBars[0].date if fetchedBars else None
    
    # Check if we have new data
    if latestDateInDb:
        latestDateInDbDt = datetime.strptime(latestDateInDb, "%Y-%m-%d")
        latestDateFromApiDt = datetime.strptime(latestDateFromApi, "%Y-%m-%d")
        
        if latestDateFromApiDt <= latestDateInDbDt:
            return {"success": True, "newDays": 0, "updated": False, "latestDate": latestDateInDb, "reason": "Already up to date"}
        
        # Filter to only new bars
        newBars = [b for b in fetchedBars if datetime.strptime(b.date, "%Y-%m-%d") > latestDateInDbDt]
    else:
        # No existing data, store all
        newBars = fetchedBars
    
    if newBars:
        dataLayer.store_daily_bars(symbol, newBars)
        return {"success": True, "newDays": len(newBars), "updated": True, "latestDate": newBars[-1].date}
    else:
        return {"success": True, "newDays": 0, "updated": False, "latestDate": latestDateInDb}

def updateWeeklyBars(symbol: str, dataLayer: DataLayer, apiKey: str) -> Dict[str, Any]:
    """Check weekly bars every day, update only if new data available."""
    latestDateInDb = dataLayer.get_latest_date(symbol, "weekly_bars")
    
    # Always fetch latest data to check
    weeklyData = fetchApiData("TIME_SERIES_WEEKLY", symbol, apiKey)
    if not weeklyData or "Weekly Time Series" not in weeklyData:
        return {"success": False, "updated": False, "reason": "API fetch failed"}
    
    weeklyBars = dataLayer._parse_weekly_bars(weeklyData)
    if not weeklyBars:
        return {"success": False, "updated": False, "reason": "Parse failed"}
    
    # Get latest date from fetched data
    latestDateFromApi = weeklyBars[0].date if weeklyBars else None
    
    # Check if we have new data
    if latestDateInDb:
        latestDateInDbDt = datetime.strptime(latestDateInDb, "%Y-%m-%d")
        latestDateFromApiDt = datetime.strptime(latestDateFromApi, "%Y-%m-%d")
        
        if latestDateFromApiDt <= latestDateInDbDt:
            return {"success": True, "updated": False, "reason": "Already up to date"}
        
        # Filter to only new bars
        fiveYearsAgo = datetime.now() - timedelta(days=5*365)
        newBars = [b for b in weeklyBars if datetime.strptime(b.date, "%Y-%m-%d") > latestDateInDbDt and datetime.strptime(b.date, "%Y-%m-%d") >= fiveYearsAgo]
    else:
        # No existing data, filter to 5 years and store all
        fiveYearsAgo = datetime.now() - timedelta(days=5*365)
        newBars = [b for b in weeklyBars if datetime.strptime(b.date, "%Y-%m-%d") >= fiveYearsAgo]
    
    if newBars:
        dataLayer.store_weekly_bars(symbol, newBars)
        return {"success": True, "updated": True, "count": len(newBars), "latestDate": newBars[-1].date}
    else:
        return {"success": True, "updated": False, "reason": "No new data"}

def updateDailyIndicators(symbol: str, dataLayer: DataLayer, apiKey: str, forceUpdate: bool = False) -> Dict[str, Any]:
    """Check daily indicators every day, update only if new data or daily bars were updated."""
    # Get daily bars for MACD calculation
    dailyBars = dataLayer.get_daily_bars(symbol)
    if not dailyBars or len(dailyBars) < 35:
        return {"success": False, "updated": False, "reason": "Not enough daily bars for indicators"}
    
    # Check latest indicator date
    latestIndicatorDate = dataLayer.get_latest_date(symbol, "daily_indicators")
    latestBarDate = dailyBars[-1].date if dailyBars else None
    
    # Only update if we have new bars or force update
    if not forceUpdate and latestIndicatorDate and latestBarDate:
        latestIndicatorDateDt = datetime.strptime(latestIndicatorDate, "%Y-%m-%d")
        latestBarDateDt = datetime.strptime(latestBarDate, "%Y-%m-%d")
        if latestBarDateDt <= latestIndicatorDateDt:
            return {"success": True, "updated": False, "reason": "Indicators up to date"}
    
    # Calculate MACD from bars
    macdCalculated = dataLayer.calculate_macd_for_all_dates(dailyBars)
    
    # Fetch RSI and STOCHRSI from API
    rsiData = fetchApiData("RSI", symbol, apiKey, interval="daily", time_period=14, series_type="close")
    rsiParsed = dataLayer._parse_technical(rsiData, "RSI") if rsiData else {}
    
    stochRsiData = fetchApiData("STOCHRSI", symbol, apiKey, interval="daily", time_period=14,
                                series_type="close", fastkperiod=5, fastdperiod=3, fastdmatype=1)
    stochRsiParsed = dataLayer._parse_technical(stochRsiData, "STOCHRSI") if stochRsiData else {}
    
    # Store all indicators
    if macdCalculated or rsiParsed or stochRsiParsed:
        dataLayer.store_daily_indicators(symbol, rsiParsed, stochRsiParsed, macdCalculated)
        return {"success": True, "updated": True, "macdCount": len(macdCalculated), "rsiCount": len(rsiParsed), "stochCount": len(stochRsiParsed)}
    else:
        return {"success": False, "updated": False, "reason": "No indicator data to store"}

def updateWeeklyIndicators(symbol: str, dataLayer: DataLayer, apiKey: str, forceUpdate: bool = False) -> Dict[str, Any]:
    """Check weekly indicators every day, update only if new data or weekly bars were updated."""
    weeklyBars = dataLayer.get_weekly_bars(symbol)
    if not weeklyBars or len(weeklyBars) < 35:
        return {"success": False, "updated": False, "reason": "Not enough weekly bars for indicators"}
    
    # Check latest indicator date
    latestIndicatorDate = dataLayer.get_latest_date(symbol, "weekly_indicators")
    latestBarDate = weeklyBars[-1].date if weeklyBars else None
    
    # Only update if we have new bars or force update
    if not forceUpdate and latestIndicatorDate and latestBarDate:
        latestIndicatorDateDt = datetime.strptime(latestIndicatorDate, "%Y-%m-%d")
        latestBarDateDt = datetime.strptime(latestBarDate, "%Y-%m-%d")
        if latestBarDateDt <= latestIndicatorDateDt:
            return {"success": True, "updated": False, "reason": "Indicators up to date"}
    
    # Calculate MACD from bars
    macdCalculated = dataLayer.calculate_macd_for_weekly(weeklyBars)
    
    # Fetch RSI from API
    rsiData = fetchApiData("RSI", symbol, apiKey, interval="weekly", time_period=14, series_type="close")
    rsiParsed = dataLayer._parse_technical(rsiData, "RSI") if rsiData else {}
    
    # Store indicators
    if macdCalculated or rsiParsed:
        dataLayer.store_weekly_indicators(symbol, rsiParsed, macdCalculated)
        return {"success": True, "updated": True, "macdCount": len(macdCalculated), "rsiCount": len(rsiParsed)}
    else:
        return {"success": False, "updated": False, "reason": "No indicator data to store"}

def updateEarnings(symbol: str, dataLayer: DataLayer, apiKey: str) -> Dict[str, Any]:
    """Update earnings data."""
    earningsData = fetchApiData("EARNINGS", symbol, apiKey)
    if not earningsData:
        return {"success": False, "reason": "API fetch failed"}
    
    earningsRecords = dataLayer._parse_earnings(earningsData)
    if earningsRecords:
        dataLayer.store_earnings(symbol, earningsRecords)
        return {"success": True, "count": len(earningsRecords)}
    else:
        return {"success": False, "reason": "No earnings data"}

def updateSymbol(symbol: str, apiKey: str) -> Dict[str, Any]:
    """Update all data for a single symbol."""
    symbol = symbol.upper()
    # Initialize database and create tables if not exist
    dataLayer = DataLayer()
    
    result = {
        "symbol": symbol,
        "dailyBars": {},
        "weeklyBars": {},
        "dailyIndicators": {},
        "weeklyIndicators": {},
        "earnings": {},
        "success": True
    }
    
    # 1. Check daily bars - update only if new data
    dailyResult = updateDailyBars(symbol, dataLayer, apiKey)
    result["dailyBars"] = dailyResult
    if dailyResult.get("updated"):
        print(f"[{symbol}] Daily bars: +{dailyResult['newDays']} days (latest: {dailyResult.get('latestDate', 'N/A')})")
    else:
        print(f"[{symbol}] Daily bars: {dailyResult.get('reason', 'Up to date')}")
    
    # 2. Check weekly bars - update only if new data
    weeklyResult = updateWeeklyBars(symbol, dataLayer, apiKey)
    result["weeklyBars"] = weeklyResult
    if weeklyResult.get("updated"):
        print(f"[{symbol}] Weekly bars: +{weeklyResult.get('count', 0)} bars (latest: {weeklyResult.get('latestDate', 'N/A')})")
    else:
        print(f"[{symbol}] Weekly bars: {weeklyResult.get('reason', 'Up to date')}")
    
    # 3. Check daily indicators - update only if daily bars were updated or new data
    dailyIndResult = updateDailyIndicators(symbol, dataLayer, apiKey, forceUpdate=dailyResult.get("updated", False))
    result["dailyIndicators"] = dailyIndResult
    if dailyIndResult.get("updated"):
        print(f"[{symbol}] Daily indicators: Updated - MACD({dailyIndResult.get('macdCount', 0)}), RSI({dailyIndResult.get('rsiCount', 0)}), STOCH({dailyIndResult.get('stochCount', 0)})")
    else:
        print(f"[{symbol}] Daily indicators: {dailyIndResult.get('reason', 'Up to date')}")
    
    # 4. Check weekly indicators - update only if weekly bars were updated or new data
    weeklyIndResult = updateWeeklyIndicators(symbol, dataLayer, apiKey, forceUpdate=weeklyResult.get("updated", False))
    result["weeklyIndicators"] = weeklyIndResult
    if weeklyIndResult.get("updated"):
        print(f"[{symbol}] Weekly indicators: Updated - MACD({weeklyIndResult.get('macdCount', 0)}), RSI({weeklyIndResult.get('rsiCount', 0)})")
    else:
        print(f"[{symbol}] Weekly indicators: {weeklyIndResult.get('reason', 'Up to date')}")
    
    # 5. Update earnings (optional, less frequent)
    # earningsResult = updateEarnings(symbol, dataLayer, apiKey)
    # result["earnings"] = earningsResult
    
    return result

def main():
    """Main entry point."""
    # Ensure database and tables are initialized
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    DataLayer()  # Initialize database and create tables

    apiKey = ALPHA_VANTAGE_API_KEY
    symbols = []

    # If no symbols provided, use default batch list
    if len(sys.argv) < 2:
        symbols = ["AAPL", "NVDA", "PANW", "RH", "AVGO", "MSTR", "COIN", "BLK", "ADBE", "MDB", "ASML", "TSLA"]
        print(f"No symbols provided, defaulting to: {', '.join(symbols)}\n")
    elif sys.argv[1] == "--watchlist":
        symbols = ['AAPL', 'NVDA', 'PANW', 'AVGO', 'ADBE', 'MDB', 'ASML', 'TSLA', 'BLK', 'RH', 'MSTR', 'COIN']
        print(f"Updating watchlist: {', '.join(symbols)}\n")
    else:
        symbols = [s.upper() for s in sys.argv[1:]]
        print(f"Updating symbols: {', '.join(symbols)}\n")

    startTime = datetime.now()
    results = []

    for symbol in symbols:
        try:
            result = updateSymbol(symbol, apiKey)
            results.append(result)
        except Exception as e:
            print(f"[{symbol}] Error: {e}")
            results.append({"symbol": symbol, "success": False, "error": str(e)})

    # Summary
    elapsed = (datetime.now() - startTime).total_seconds()
    print(f"\n{'='*60}")
    print(f"Completed: {len(symbols)} symbols in {elapsed:.1f}s")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

