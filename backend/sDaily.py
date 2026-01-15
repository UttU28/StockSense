import os
import sys
import json
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Set
from dotenv import load_dotenv

load_dotenv()

from config import DB_PATH, CACHE_DIR, KeyManager, AllKeysExhaustedException
from data_layer import DataLayer
from models import DailyBar, EarningsRecord

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

CHECKPOINT_FILE = os.path.join(CACHE_DIR, "sDaily_checkpoint.json")

def fetchIndicatorHistory(ticker, indicator, keyManager, interval='1day', outputsize=2000, maxRetries=3, retryDelay=60, **kwargs):
    url = f"https://api.twelvedata.com/{indicator}"
    
    for attempt in range(maxRetries):
        try:
            apiKey = keyManager.getAvailableKey()
        except AllKeysExhaustedException:
            raise
        
        params = {
            'symbol': ticker,
            'interval': interval,
            'outputsize': outputsize,
            'apikey': apiKey
        }
        params.update(kwargs)
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'error':
                message = data.get('message', 'Unknown error')
                
                if 'rate limit' in message.lower() or 'api credits' in message.lower():
                    keyManager.markRateLimited(apiKey)
                    if keyManager.getAvailableCount() > 0:
                        continue
                    else:
                        raise AllKeysExhaustedException("All API keys exhausted")
                else:
                    return None
            
            if 'values' in data and len(data['values']) > 0:
                return data['values']
            else:
                return None
                
        except AllKeysExhaustedException:
            raise
        except Exception as e:
            if attempt < maxRetries - 1:
                time.sleep(retryDelay)
            return None
    
    return None

def fetchTimeSeriesData(ticker, keyManager, maxRetries=3, retryDelay=60):
    url = "https://api.twelvedata.com/time_series"
    
    for attempt in range(maxRetries):
        try:
            apiKey = keyManager.getAvailableKey()
        except AllKeysExhaustedException:
            raise
        
        params = {
            'symbol': ticker,
            'interval': '1day',
            'outputsize': '2000',
            'apikey': apiKey
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'error':
                message = data.get('message', 'Unknown error')
                
                if 'rate limit' in message.lower() or 'api credits' in message.lower():
                    keyManager.markRateLimited(apiKey)
                    if keyManager.getAvailableCount() > 0:
                        continue
                    else:
                        raise AllKeysExhaustedException("All API keys exhausted")
                else:
                    return None
            
            if 'values' in data:
                df = pd.DataFrame(data['values'])
                df['datetime'] = pd.to_datetime(df['datetime'])
                numericCols = ['open', 'high', 'low', 'close', 'volume']
                for col in numericCols:
                    df[col] = pd.to_numeric(df[col])
                
                df = df.rename(columns={
                    'datetime': 'Date',
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })
                
                fiveYearsAgo = datetime.now() - timedelta(days=5*365)
                df = df[df['Date'] >= fiveYearsAgo]
                df['Stock_Name'] = ticker
                df = df.sort_values('Date')
                
                return df
            else:
                return None
                
        except AllKeysExhaustedException:
            raise
        except Exception as e:
            if attempt < maxRetries - 1:
                time.sleep(retryDelay)
            return None
    
    return None

def fetchAllIndicators(ticker, keyManager):
    indicatorsData = {}
    intervals = ['1day', '1week', '1month']
    
    for interval in intervals:
        try:
            rsiData = fetchIndicatorHistory(ticker, 'rsi', keyManager, interval=interval, time_period=14)
        except AllKeysExhaustedException:
            raise
        if rsiData:
            df = pd.DataFrame(rsiData)
            df['datetime'] = pd.to_datetime(df['datetime'])
            indicatorsData[f'RSI_{interval}'] = df.set_index('datetime')['rsi']
        time.sleep(1.2)
        
        try:
            macdData = fetchIndicatorHistory(ticker, 'macd', keyManager, interval=interval, fast_period=12, slow_period=26, signal_period=9)
        except AllKeysExhaustedException:
            raise
        if macdData:
            df = pd.DataFrame(macdData)
            df['datetime'] = pd.to_datetime(df['datetime'])
            indicatorsData[f'MACD_{interval}'] = df.set_index('datetime')['macd']
            indicatorsData[f'MACD_Signal_{interval}'] = df.set_index('datetime')['macd_signal']
            indicatorsData[f'MACD_Hist_{interval}'] = df.set_index('datetime')['macd_hist']
        time.sleep(1.2)
        
        try:
            bbData = fetchIndicatorHistory(ticker, 'bbands', keyManager, interval=interval, time_period=20, sd=2)
        except AllKeysExhaustedException:
            raise
        if bbData:
            df = pd.DataFrame(bbData)
            df['datetime'] = pd.to_datetime(df['datetime'])
            indicatorsData[f'BB_Upper_{interval}'] = df.set_index('datetime')['upper_band']
            indicatorsData[f'BB_Middle_{interval}'] = df.set_index('datetime')['middle_band']
            indicatorsData[f'BB_Lower_{interval}'] = df.set_index('datetime')['lower_band']
        time.sleep(1.2)
    
    smaPeriods = [55, 89, 144, 233]
    for period in smaPeriods:
        try:
            smaData = fetchIndicatorHistory(ticker, 'sma', keyManager, interval='1day', time_period=period, series_type='close')
        except AllKeysExhaustedException:
            raise
        if smaData:
            df = pd.DataFrame(smaData)
            df['datetime'] = pd.to_datetime(df['datetime'])
            indicatorsData[f'SMA_{period}'] = df.set_index('datetime')['sma']
        time.sleep(1.2)
    
    return indicatorsData

def fetchEarnings(ticker, maxRetries=3, retryDelay=5):
    """Fetch earnings data from Alpha Vantage API"""
    if not ALPHA_VANTAGE_API_KEY:
        print(f"Warning: ALPHA_VANTAGE_API_KEY not set. Skipping earnings fetch for {ticker}")
        return []
    
    url = "https://www.alphavantage.co/query"
    
    for attempt in range(maxRetries):
        params = {
            'function': 'EARNINGS',
            'symbol': ticker,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'Error Message' in data:
                print(f"Error fetching earnings for {ticker}: {data['Error Message']}")
                return []
            
            if 'Note' in data:
                if attempt < maxRetries - 1:
                    waitTime = retryDelay * (attempt + 1)
                    print(f"Rate limit hit for {ticker}. Waiting {waitTime}s...")
                    time.sleep(waitTime)
                    continue
                else:
                    print(f"Rate limit exceeded for {ticker}. Skipping earnings fetch.")
                    return []
            
            if 'Information' in data:
                print(f"API call frequency limit reached for {ticker}. Skipping earnings fetch.")
                return []
            
            earningsRecords = []
            
            if 'quarterlyEarnings' in data and isinstance(data['quarterlyEarnings'], list):
                for item in data['quarterlyEarnings']:
                    try:
                        fiscalDateEnding = item.get('fiscalDateEnding', '')
                        reportedDate = item.get('reportedDate', '')
                        
                        reportedEps = None
                        if item.get('reportedEPS') and item['reportedEPS'] not in [None, '', 'None']:
                            reportedEps = float(item['reportedEPS'])
                        
                        estimatedEps = None
                        if item.get('estimatedEPS') and item['estimatedEPS'] not in [None, '', 'None']:
                            estimatedEps = float(item['estimatedEPS'])
                        
                        surprise = None
                        if item.get('surprise') and item['surprise'] not in [None, '', 'None']:
                            surprise = float(item['surprise'])
                        
                        surprisePercentage = None
                        if item.get('surprisePercentage') and item['surprisePercentage'] not in [None, '', 'None']:
                            surprisePercentage = float(item['surprisePercentage'])
                        
                        if fiscalDateEnding:
                            earningsRecord = EarningsRecord(
                                fiscal_date_ending=fiscalDateEnding,
                                reported_date=reportedDate,
                                reported_eps=reportedEps,
                                estimated_eps=estimatedEps,
                                surprise=surprise,
                                surprise_percentage=surprisePercentage
                            )
                            earningsRecords.append(earningsRecord)
                    except (ValueError, KeyError, TypeError) as e:
                        continue
                
                return earningsRecords
            else:
                return []
                
        except Exception as e:
            print(f"Exception fetching earnings for {ticker}: {e}")
            if attempt < maxRetries - 1:
                time.sleep(retryDelay)
            return []
    
    return []

def mergeIndicatorsWithPriceData(priceDf, indicatorsData):
    if priceDf is None or priceDf.empty:
        return priceDf
    
    df = priceDf.copy()
    df = df.set_index('Date')
    df = df.sort_index()
    
    for indicatorName, indicatorSeries in indicatorsData.items():
        if indicatorSeries is not None and len(indicatorSeries) > 0:
            indicatorDf = indicatorSeries.to_frame(indicatorName)
            indicatorDf = indicatorDf.sort_index()
            
            df = df.join(indicatorDf, how='left')
            
            if '1week' in indicatorName or '1month' in indicatorName:
                df[indicatorName] = df[indicatorName].ffill()
    
    df = df.reset_index()
    
    if 'index' in df.columns and 'Date' not in df.columns:
        df = df.rename(columns={'index': 'Date'})
    
    df['Symbol'] = df['Stock_Name']
    df['Fetch_Time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return df

def loadCheckpoint() -> Set[str]:
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('completedSymbols', []))
        except Exception as e:
            print(f"Warning: Could not load checkpoint: {e}")
    return set()

def saveCheckpoint(completedSymbols: Set[str]):
    try:
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump({'completedSymbols': list(completedSymbols), 'lastUpdate': datetime.now().isoformat()}, f)
    except Exception as e:
        print(f"Warning: Could not save checkpoint: {e}")

def clearCheckpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            os.remove(CHECKPOINT_FILE)
        except Exception as e:
            print(f"Warning: Could not clear checkpoint: {e}")

def updateDailyBars(symbol: str, dataLayer: DataLayer, keyManager: KeyManager) -> Dict[str, Any]:
    latestDateInDb = dataLayer.get_latest_date(symbol, "daily_bars")
    
    try:
        priceDf = fetchTimeSeriesData(symbol, keyManager)
    except AllKeysExhaustedException:
        raise
    if priceDf is None or priceDf.empty:
        return {"success": False, "newDays": 0, "updated": False, "reason": "API fetch failed"}
    
    priceDf['Date'] = pd.to_datetime(priceDf['Date'])
    
    if latestDateInDb:
        latestDateInDbDt = datetime.strptime(latestDateInDb, "%Y-%m-%d")
        newPriceDf = priceDf[priceDf['Date'] > latestDateInDbDt]
    else:
        newPriceDf = priceDf
    
    if newPriceDf.empty:
        return {"success": True, "newDays": 0, "updated": False, "latestDate": latestDateInDb, "reason": "Already up to date"}
    
    newBars = []
    for _, row in newPriceDf.iterrows():
        newBars.append(DailyBar(
            date=row['Date'].strftime("%Y-%m-%d"),
            open=float(row['Open']),
            high=float(row['High']),
            low=float(row['Low']),
            close=float(row['Close']),
            volume=int(row['Volume'])
        ))
    
    if newBars:
        dataLayer.store_daily_bars(symbol, newBars)
        latestNewDate = newBars[-1].date
        return {"success": True, "newDays": len(newBars), "updated": True, "latestDate": latestNewDate}
    else:
        return {"success": True, "newDays": 0, "updated": False, "latestDate": latestDateInDb}

def updateDailyIndicators(symbol: str, dataLayer: DataLayer, keyManager: KeyManager, forceUpdate: bool = False) -> Dict[str, Any]:
    latestIndicatorDate = dataLayer.get_latest_date(symbol, "daily_indicators")
    latestBarDate = dataLayer.get_latest_date(symbol, "daily_bars")
    
    if not forceUpdate and latestIndicatorDate and latestBarDate:
        latestIndicatorDateDt = datetime.strptime(latestIndicatorDate, "%Y-%m-%d")
        latestBarDateDt = datetime.strptime(latestBarDate, "%Y-%m-%d")
        if latestBarDateDt <= latestIndicatorDateDt:
            return {"success": True, "updated": False, "reason": "Indicators up to date"}
    
    try:
        priceDf = fetchTimeSeriesData(symbol, keyManager)
    except AllKeysExhaustedException:
        raise
    if priceDf is None or priceDf.empty:
        return {"success": False, "updated": False, "reason": "No price data available"}
    
    priceDf['Date'] = pd.to_datetime(priceDf['Date'])
    
    historicalBars = dataLayer.get_daily_bars(symbol)
    if not historicalBars:
        return {"success": False, "updated": False, "reason": "No historical bars found in database"}
    
    historicalDf = pd.DataFrame([{
        'Date': pd.to_datetime(bar.date),
        'Open': bar.open,
        'High': bar.high,
        'Low': bar.low,
        'Close': bar.close,
        'Volume': bar.volume
    } for bar in historicalBars])
    
    if latestIndicatorDate:
        latestIndicatorDateDt = datetime.strptime(latestIndicatorDate, "%Y-%m-%d")
        newPriceDf = priceDf[priceDf['Date'] > latestIndicatorDateDt]
    else:
        newPriceDf = priceDf
    
    if newPriceDf.empty:
        return {"success": True, "updated": False, "reason": "Indicators up to date"}
    
    fullPriceDf = pd.concat([historicalDf, newPriceDf], ignore_index=True)
    fullPriceDf = fullPriceDf.drop_duplicates(subset=['Date'], keep='last')
    fullPriceDf = fullPriceDf.sort_values('Date')
    fullPriceDf['Stock_Name'] = symbol
    
    try:
        indicatorsData = fetchAllIndicators(symbol, keyManager)
    except AllKeysExhaustedException:
        raise
    if not indicatorsData:
        return {"success": False, "updated": False, "reason": "No indicator data fetched"}
    
    mergedDf = mergeIndicatorsWithPriceData(fullPriceDf, indicatorsData)
    if mergedDf is None or mergedDf.empty:
        return {"success": False, "updated": False, "reason": "Failed to merge indicators"}
    
    if latestIndicatorDate:
        latestIndicatorDateDt = datetime.strptime(latestIndicatorDate, "%Y-%m-%d")
        newMergedDf = mergedDf[mergedDf['Date'] > latestIndicatorDateDt]
    else:
        newMergedDf = mergedDf
    
    if newMergedDf.empty:
        return {"success": True, "updated": False, "reason": "No new indicator data to store"}
    
    dataLayer.storeDailyIndicators(symbol, newMergedDf)
    
    indicatorCount = len([col for col in newMergedDf.columns if any(x in col for x in ['RSI_', 'MACD_', 'BB_'])])
    return {"success": True, "updated": True, "indicatorCount": indicatorCount, "recordCount": len(newMergedDf)}

def updateEarnings(symbol: str, dataLayer: DataLayer) -> Dict[str, Any]:
    """Fetch and store earnings data for a symbol using Alpha Vantage API"""
    try:
        earningsRecords = fetchEarnings(symbol)
        if earningsRecords:
            dataLayer.store_earnings(symbol, earningsRecords)
            return {"success": True, "updated": True, "count": len(earningsRecords)}
        else:
            return {"success": True, "updated": False, "reason": "No earnings data available"}
    except Exception as e:
        return {"success": False, "updated": False, "reason": f"Error fetching earnings: {e}"}

def updateSymbol(symbol: str, keyManager: KeyManager) -> Dict[str, Any]:
    symbol = symbol.upper()
    dataLayer = DataLayer()
    
    result = {
        "symbol": symbol,
        "dailyBars": {},
        "dailyIndicators": {},
        "earnings": {},
        "success": True
    }
    
    try:
        dailyResult = updateDailyBars(symbol, dataLayer, keyManager)
        result["dailyBars"] = dailyResult
        if dailyResult.get("updated"):
            print(f"[{symbol}] Daily bars: +{dailyResult['newDays']} days (latest: {dailyResult.get('latestDate', 'N/A')})")
        else:
            print(f"[{symbol}] Daily bars: {dailyResult.get('reason', 'Up to date')}")
        
        dailyIndResult = updateDailyIndicators(symbol, dataLayer, keyManager, forceUpdate=dailyResult.get("updated", False))
        result["dailyIndicators"] = dailyIndResult
        if dailyIndResult.get("updated"):
            print(f"[{symbol}] Daily indicators: Updated - {dailyIndResult.get('indicatorCount', 0)} indicators, {dailyIndResult.get('recordCount', 0)} records")
        else:
            print(f"[{symbol}] Daily indicators: {dailyIndResult.get('reason', 'Up to date')}")
        
        earningsResult = updateEarnings(symbol, dataLayer)
        result["earnings"] = earningsResult
        if earningsResult.get("updated"):
            print(f"[{symbol}] Earnings: Updated - {earningsResult.get('count', 0)} records")
        else:
            print(f"[{symbol}] Earnings: {earningsResult.get('reason', 'Up to date')}")
        
        if dailyIndResult.get("success") and dailyResult.get("success"):
            result["success"] = True
        else:
            result["success"] = False
    except KeyboardInterrupt:
        print(f"\n[{symbol}] Interrupted by user")
        raise
    except Exception as e:
        print(f"[{symbol}] Error: {e}")
        result["success"] = False
        result["error"] = str(e)
        raise
    
    return result

def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    DataLayer()
    
    keyManager = KeyManager()
    print(f"Initialized KeyManager with {len(keyManager.apiKeys)} API key(s)\n")
    
    completedSymbols = loadCheckpoint()
    if completedSymbols:
        print(f"Resuming from checkpoint: {len(completedSymbols)} symbols already completed")
        print(f"Completed: {', '.join(sorted(completedSymbols))}\n")
    
    symbols = []
    
    if len(sys.argv) < 2:
        allSymbols = ["AAPL", "NVDA", "PANW", "RH", "AVGO", "MSTR", "COIN", "BLK", "ADBE", "MDB", "ASML", "TSLA"]
        # allSymbols = ["AAPL"]
        
        if '--clear-checkpoint' in sys.argv:
            clearCheckpoint()
            completedSymbols = set()
            symbols = allSymbols
            print("Checkpoint cleared. Processing all symbols.\n")
        else:
            symbols = [s for s in allSymbols if s not in completedSymbols]
            if not symbols:
                print("All symbols already completed. Use --clear-checkpoint to reset.\n")
                return
            print(f"No symbols provided, defaulting to: {', '.join(allSymbols)}")
            print(f"Processing remaining: {', '.join(symbols)}\n")
    else:
        symbols = [s.upper() for s in sys.argv[1:] if s != '--clear-checkpoint']
        if '--clear-checkpoint' in sys.argv:
            clearCheckpoint()
            completedSymbols = set()
        symbols = [s for s in symbols if s not in completedSymbols]
        if not symbols:
            print("All specified symbols already completed. Use --clear-checkpoint to reset.\n")
            return
        print(f"Updating symbols: {', '.join(symbols)}\n")
    
    startTime = datetime.now()
    results = []
    
    try:
        for symbol in symbols:
            try:
                result = updateSymbol(symbol, keyManager)
                results.append(result)
                
                if result.get("success"):
                    completedSymbols.add(symbol)
                    saveCheckpoint(completedSymbols)
                    print(f"[{symbol}] ✓ Completed and saved to checkpoint\n")
                else:
                    print(f"[{symbol}] ✗ Failed - will retry on next run\n")
            except AllKeysExhaustedException as e:
                print(f"\n\n[ERROR] All API keys exhausted: {e}")
                print(f"Progress saved to checkpoint.")
                print(f"Completed: {', '.join(sorted(completedSymbols))}")
                print(f"Remaining: {', '.join([s for s in symbols if s not in completedSymbols])}")
                keyManager.saveKeys()
                sys.exit(1)
            except KeyboardInterrupt:
                print(f"\n\nInterrupted. Progress saved to checkpoint.")
                print(f"Completed: {', '.join(sorted(completedSymbols))}")
                print(f"Remaining: {', '.join([s for s in symbols if s not in completedSymbols])}")
                sys.exit(1)
            except Exception as e:
                print(f"[{symbol}] Error: {e}")
                results.append({"symbol": symbol, "success": False, "error": str(e)})
                print(f"[{symbol}] ✗ Failed - will retry on next run\n")
    except AllKeysExhaustedException as e:
        print(f"\n\n[ERROR] All API keys exhausted: {e}")
        print(f"Progress saved to checkpoint.")
        print(f"Completed: {', '.join(sorted(completedSymbols))}")
        keyManager.saveKeys()
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\nInterrupted. Progress saved to checkpoint.")
        print(f"Completed: {', '.join(sorted(completedSymbols))}")
        sys.exit(1)
    
    elapsed = (datetime.now() - startTime).total_seconds()
    print(f"\n{'='*60}")
    print(f"Completed: {len([r for r in results if r.get('success')])}/{len(symbols)} symbols in {elapsed:.1f}s")
    print(f"{'='*60}")
    
    keyManager.saveKeys()
    
    if completedSymbols:
        print(f"\nCheckpoint saved. Completed symbols: {', '.join(sorted(completedSymbols))}")

if __name__ == "__main__":
    main()
