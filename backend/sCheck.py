import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

from config import DB_PATH, KeyManager, AllKeysExhaustedException
from data_layer import DataLayer
from models import DailyBar, EarningsRecord
from sDaily import updateDailyBars, updateDailyIndicators, updateEarnings

def getSymbolsFromDb(dataLayer: DataLayer) -> List[str]:
    """Get all unique symbols from the database"""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    symbols = set()
    
    c.execute("SELECT DISTINCT symbol FROM daily_bars")
    symbols.update([row[0] for row in c.fetchall()])
    
    c.execute("SELECT DISTINCT symbol FROM daily_indicators")
    symbols.update([row[0] for row in c.fetchall()])
    
    c.execute("SELECT DISTINCT symbol FROM earnings")
    symbols.update([row[0] for row in c.fetchall()])
    
    conn.close()
    return sorted(list(symbols))

def checkDailyBars(dataLayer: DataLayer, symbol: str) -> Dict:
    """Check daily bars data for a symbol"""
    bars = dataLayer.get_daily_bars(symbol)
    
    if not bars:
        return {
            "exists": False,
            "count": 0,
            "latestDate": None,
            "earliestDate": None,
            "hasRecentData": False,
            "daysBehind": None
        }
    
    sortedBars = sorted(bars, key=lambda x: x.date)
    latestDate = datetime.strptime(sortedBars[-1].date, "%Y-%m-%d")
    earliestDate = datetime.strptime(sortedBars[0].date, "%Y-%m-%d")
    today = datetime.now()
    daysBehind = (today - latestDate).days
    
    return {
        "exists": True,
        "count": len(bars),
        "latestDate": sortedBars[-1].date,
        "earliestDate": sortedBars[0].date,
        "hasRecentData": daysBehind <= 2,
        "daysBehind": daysBehind,
        "dateRangeDays": (latestDate - earliestDate).days
    }

def checkDailyIndicators(dataLayer: DataLayer, symbol: str) -> Dict:
    """Check daily indicators data for a symbol"""
    indicators = dataLayer.getDailyIndicators(symbol)
    
    if not indicators:
        return {
            "exists": False,
            "count": 0,
            "latestDate": None,
            "earliestDate": None,
            "hasRecentData": False,
            "daysBehind": None,
            "missingIndicators": []
        }
    
    dates = sorted(indicators.keys())
    latestDate = datetime.strptime(dates[-1], "%Y-%m-%d")
    earliestDate = datetime.strptime(dates[0], "%Y-%m-%d")
    today = datetime.now()
    daysBehind = (today - latestDate).days
    
    requiredIndicators = [
        "RSI_1day", "RSI_1week", "RSI_1month",
        "MACD_1day", "MACD_Signal_1day", "MACD_Hist_1day",
        "MACD_1week", "MACD_Signal_1week", "MACD_Hist_1week",
        "MACD_1month", "MACD_Signal_1month", "MACD_Hist_1month",
        "BB_Upper_1day", "BB_Middle_1day", "BB_Lower_1day",
        "BB_Upper_1week", "BB_Middle_1week", "BB_Lower_1week",
        "BB_Upper_1month", "BB_Middle_1month", "BB_Lower_1month",
        "SMA_55", "SMA_89", "SMA_144", "SMA_233"
    ]
    
    missingIndicators = []
    sampleDate = dates[-1] if dates else None
    if sampleDate:
        sampleIndicators = indicators[sampleDate]
        for req in requiredIndicators:
            if req not in sampleIndicators or sampleIndicators[req] is None:
                missingIndicators.append(req)
    
    return {
        "exists": True,
        "count": len(indicators),
        "latestDate": dates[-1] if dates else None,
        "earliestDate": dates[0] if dates else None,
        "hasRecentData": daysBehind <= 2,
        "daysBehind": daysBehind,
        "dateRangeDays": (latestDate - earliestDate).days if dates else 0,
        "missingIndicators": missingIndicators
    }

def checkEarnings(dataLayer: DataLayer, symbol: str) -> Dict:
    """Check earnings data for a symbol"""
    earnings = dataLayer.get_earnings(symbol)
    
    if not earnings:
        return {
            "exists": False,
            "count": 0,
            "latestFiscalDate": None,
            "earliestFiscalDate": None
        }
    
    sortedEarnings = sorted(earnings, key=lambda x: x.fiscal_date_ending)
    
    return {
        "exists": True,
        "count": len(earnings),
        "latestFiscalDate": sortedEarnings[-1].fiscal_date_ending,
        "earliestFiscalDate": sortedEarnings[0].fiscal_date_ending
    }

def checkDataAlignment(dataLayer: DataLayer, symbol: str) -> Dict:
    """Check if bars and indicators are aligned"""
    bars = dataLayer.get_daily_bars(symbol)
    indicators = dataLayer.getDailyIndicators(symbol)
    
    if not bars or not indicators:
        return {
            "aligned": False,
            "barsCount": len(bars) if bars else 0,
            "indicatorsCount": len(indicators) if indicators else 0,
            "missingIndicatorDates": []
        }
    
    barDates = set(bar.date for bar in bars)
    indicatorDates = set(indicators.keys())
    
    missingIndicatorDates = sorted(list(barDates - indicatorDates))
    
    return {
        "aligned": len(missingIndicatorDates) == 0,
        "barsCount": len(bars),
        "indicatorsCount": len(indicators),
        "missingIndicatorDatesCount": len(missingIndicatorDates),
        "missingIndicatorDates": missingIndicatorDates[:10]
    }

def generateReport(dataLayer: DataLayer, symbols: List[str] = None, autoFix: bool = False) -> None:
    """Generate a comprehensive data status report and optionally fix missing data"""
    if symbols is None:
        symbols = getSymbolsFromDb(dataLayer)
    
    if not symbols:
        print("No symbols found in database.")
        return
    
    print(f"Database Status Check - {len(symbols)} symbols")
    if autoFix:
        print("Auto-fix mode: Will update missing data\n")
    else:
        print()
    
    issues = defaultdict(list)
    needsUpdate = defaultdict(dict)
    summary = {
        "totalSymbols": len(symbols),
        "missingBars": 0,
        "missingIndicators": 0,
        "missingEarnings": 0,
        "outdatedBars": 0,
        "outdatedIndicators": 0,
        "misalignedData": 0
    }
    
    for symbol in symbols:
        barsStatus = checkDailyBars(dataLayer, symbol)
        indicatorsStatus = checkDailyIndicators(dataLayer, symbol)
        earningsStatus = checkEarnings(dataLayer, symbol)
        alignmentStatus = checkDataAlignment(dataLayer, symbol)
        
        status = []
        
        if not barsStatus["exists"]:
            status.append("BARS: MISSING")
            issues[symbol].append("Missing daily bars")
            summary["missingBars"] += 1
            needsUpdate[symbol]["bars"] = True
        elif not barsStatus["hasRecentData"]:
            status.append(f"BARS: {barsStatus['daysBehind']}d old")
            issues[symbol].append(f"Bars outdated by {barsStatus['daysBehind']} days")
            summary["outdatedBars"] += 1
            needsUpdate[symbol]["bars"] = True
        else:
            status.append(f"BARS: {barsStatus['count']} ({barsStatus['latestDate']})")
        
        if not indicatorsStatus["exists"]:
            status.append("INDICATORS: MISSING")
            issues[symbol].append("Missing indicators")
            summary["missingIndicators"] += 1
            needsUpdate[symbol]["indicators"] = True
        elif not indicatorsStatus["hasRecentData"]:
            status.append(f"INDICATORS: {indicatorsStatus['daysBehind']}d old")
            issues[symbol].append(f"Indicators outdated by {indicatorsStatus['daysBehind']} days")
            summary["outdatedIndicators"] += 1
            needsUpdate[symbol]["indicators"] = True
        else:
            status.append(f"INDICATORS: {indicatorsStatus['count']} ({indicatorsStatus['latestDate']})")
            if indicatorsStatus["missingIndicators"]:
                status.append(f"MISSING: {', '.join(indicatorsStatus['missingIndicators'][:3])}")
                issues[symbol].append(f"Missing indicators: {', '.join(indicatorsStatus['missingIndicators'])}")
                needsUpdate[symbol]["indicators"] = True
        
        if not earningsStatus["exists"]:
            status.append("EARNINGS: MISSING")
            issues[symbol].append("Missing earnings")
            summary["missingEarnings"] += 1
            needsUpdate[symbol]["earnings"] = True
        else:
            status.append(f"EARNINGS: {earningsStatus['count']}")
        
        if not alignmentStatus["aligned"]:
            missingCount = alignmentStatus.get("missingIndicatorDatesCount", 0)
            if missingCount > 0:
                status.append(f"MISALIGNED: {missingCount} dates")
            issues[symbol].append(f"Data misaligned: {missingCount} dates missing indicators")
            summary["misalignedData"] += 1
            if missingCount > 0:
                needsUpdate[symbol]["indicators"] = True
        
        if any("MISSING" in s or "MISALIGNED" in s or "d old" in s for s in status):
            print(f"{symbol:6} | {' | '.join(status)}")
        else:
            print(f"{symbol:6} | OK")
    
    print(f"\nSummary: {summary['totalSymbols']} symbols | Missing: {summary['missingBars']} bars, {summary['missingIndicators']} indicators, {summary['missingEarnings']} earnings")
    
    if issues:
        print(f"\nIssues found:")
        for symbol, symbolIssues in sorted(issues.items()):
            print(f"  {symbol}: {'; '.join(symbolIssues)}")
    else:
        print(f"\nAll symbols complete!")
    
    if autoFix and needsUpdate:
        print(f"\n{'='*60}")
        print("Auto-fixing missing data...")
        print(f"{'='*60}\n")
        
        keyManager = KeyManager()
        fixedCount = 0
        failedCount = 0
        
        for symbol in sorted(needsUpdate.keys()):
            print(f"\n[{symbol}] Updating...")
            try:
                if needsUpdate[symbol].get("bars"):
                    result = updateDailyBars(symbol, dataLayer, keyManager)
                    if result.get("updated"):
                        print(f"  [OK] Bars updated: +{result.get('newDays', 0)} days")
                    else:
                        print(f"  [SKIP] Bars: {result.get('reason', 'No update needed')}")
                
                if needsUpdate[symbol].get("indicators"):
                    result = updateDailyIndicators(symbol, dataLayer, keyManager, forceUpdate=True)
                    if result.get("updated"):
                        print(f"  [OK] Indicators updated: {result.get('recordCount', 0)} records")
                    else:
                        print(f"  [SKIP] Indicators: {result.get('reason', 'No update needed')}")
                
                if needsUpdate[symbol].get("earnings"):
                    result = updateEarnings(symbol, dataLayer)
                    if result.get("updated"):
                        print(f"  [OK] Earnings updated: {result.get('count', 0)} records")
                    else:
                        print(f"  [SKIP] Earnings: {result.get('reason', 'No update needed')}")
                
                fixedCount += 1
                
            except AllKeysExhaustedException as e:
                print(f"  [ERROR] All API keys exhausted. Stopping updates.")
                keyManager.saveKeys()
                failedCount += 1
                break
            except Exception as e:
                print(f"  [ERROR] Failed to update {symbol}: {e}")
                failedCount += 1
        
        keyManager.saveKeys()
        print(f"\n{'='*60}")
        print(f"Update complete: {fixedCount} fixed, {failedCount} failed")
        print(f"{'='*60}")
        
        if fixedCount > 0:
            print("\nRe-checking status...\n")
            generateReport(dataLayer, symbols, autoFix=False)

def main():
    dataLayer = DataLayer()
    
    autoFix = '--fix' in sys.argv or '--update' in sys.argv
    symbols = None
    
    if len(sys.argv) > 1:
        filteredArgs = [s for s in sys.argv[1:] if s not in ['--fix', '--update']]
        if filteredArgs:
            symbols = [s.upper() for s in filteredArgs]
            print(f"Checking specified symbols: {', '.join(symbols)}\n")
        else:
            print("Checking all symbols in database...\n")
    else:
        print("Checking all symbols in database...\n")
    
    generateReport(dataLayer, symbols, autoFix=autoFix)

if __name__ == "__main__":
    main()
