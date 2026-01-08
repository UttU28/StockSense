#!/usr/bin/env python3
"""
Script to extract stock data from HTML file and save as CSV.
Parses Yahoo Finance HTML and extracts historical price table data.
Also updates the daily_bars table in the database, skipping existing dates.
"""

import os
import re
import csv
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from data_layer import DataLayer
from models import DailyBar
from config import DB_PATH


def extractStockSymbol(htmlContent):
    """Extract stock symbol from HTML content."""
    match = re.search(r'<h1[^>]*>([^<]+)\(([A-Z]+)\)</h1>', htmlContent)
    if match:
        return match.group(2)
    
    match = re.search(r'data-symbol="([A-Z]+)"', htmlContent)
    if match:
        return match.group(1)
    
    return "UNKNOWN"


def parseTableData(htmlContent):
    """Parse HTML table and extract headers and rows."""
    soup = BeautifulSoup(htmlContent, 'html.parser')
    
    table = soup.find('table', class_='table')
    if not table:
        return None, None
    
    headers = []
    thead = table.find('thead')
    if thead:
        headerRow = thead.find('tr')
        if headerRow:
            for th in headerRow.find_all('th'):
                headerText = th.get_text(strip=True)
                if headerText:
                    headers.append(headerText)
    
    rows = []
    tbody = table.find('tbody')
    if tbody:
        for tr in tbody.find_all('tr'):
            rowData = []
            for td in tr.find_all('td'):
                cellText = td.get_text(strip=True)
                rowData.append(cellText)
            if rowData:
                rows.append(rowData)
    
    return headers, rows


def formatDate(dateStr):
    """Convert date from 'Jan 7, 2026' format to '2026-01-07' format."""
    try:
        dateObj = datetime.strptime(dateStr.strip(), '%b %d, %Y')
        return dateObj.strftime('%Y-%m-%d')
    except ValueError:
        return dateStr


def formatVolume(volumeStr):
    """Convert volume from '45,316,385' format to integer."""
    try:
        volumeStr = volumeStr.replace(',', '').strip()
        return int(volumeStr)
    except (ValueError, AttributeError):
        return volumeStr


def isValidRow(row, expectedColumns):
    """Check if row is valid (has correct number of columns and no dividend/split data)."""
    if len(row) != expectedColumns:
        return False
    
    rowStr = ' '.join(str(cell) for cell in row).lower()
    if 'dividend' in rowStr or 'split' in rowStr:
        return False
    
    return True


def processRowData(headers, row):
    """Process row data: format dates and convert volume to integer."""
    processedRow = []
    for i, cell in enumerate(row):
        if i < len(headers):
            header = headers[i].strip().lower()
            if 'date' in header:
                processedRow.append(formatDate(cell))
            elif 'volume' in header:
                processedRow.append(formatVolume(cell))
            else:
                processedRow.append(cell)
        else:
            processedRow.append(cell)
    return processedRow


def convertToDailyBar(processedRow, headers):
    """Convert processed row to DailyBar object."""
    try:
        dateIdx = None
        openIdx = None
        highIdx = None
        lowIdx = None
        closeIdx = None
        volumeIdx = None
        
        for i, header in enumerate(headers):
            headerLower = header.strip().lower()
            if 'date' in headerLower:
                dateIdx = i
            elif 'open' in headerLower:
                openIdx = i
            elif 'high' in headerLower:
                highIdx = i
            elif 'low' in headerLower:
                lowIdx = i
            elif 'close' in headerLower and 'adj' not in headerLower:
                closeIdx = i
            elif 'volume' in headerLower:
                volumeIdx = i
        
        if None in [dateIdx, openIdx, highIdx, lowIdx, closeIdx, volumeIdx]:
            return None
        
        return DailyBar(
            date=str(processedRow[dateIdx]),
            open=float(processedRow[openIdx]),
            high=float(processedRow[highIdx]),
            low=float(processedRow[lowIdx]),
            close=float(processedRow[closeIdx]),
            volume=int(processedRow[volumeIdx])
        )
    except (ValueError, IndexError, TypeError) as e:
        return None


def reorderRowToFixedHeaders(processedRow, originalHeaders, fixedHeaders):
    """Reorder processedRow to match fixedHeaders order."""
    headerMap = {}
    for i, origHeader in enumerate(originalHeaders):
        origHeaderLower = origHeader.strip().lower()
        for fixedHeader in fixedHeaders:
            fixedHeaderLower = fixedHeader.strip().lower()
            if fixedHeaderLower in origHeaderLower or origHeaderLower in fixedHeaderLower:
                headerMap[fixedHeaderLower] = i
                break
    
    reorderedRow = []
    for fixedHeader in fixedHeaders:
        fixedHeaderLower = fixedHeader.strip().lower()
        idx = headerMap.get(fixedHeaderLower)
        if idx is not None and idx < len(processedRow):
            reorderedRow.append(processedRow[idx])
        else:
            reorderedRow.append('')
    
    return reorderedRow


def saveToCsv(stockSymbol, headers, rows, outputPath):
    """Save extracted data to CSV file."""
    fixedHeaders = ['date', 'open', 'high', 'low', 'close', 'adj close', 'volume']
    expectedColumns = len(fixedHeaders)
    
    validRows = []
    with open(outputPath, 'w', newline='', encoding='utf-8') as csvFile:
        writer = csv.writer(csvFile)
        
        writer.writerow(fixedHeaders)
        
        for row in rows:
            if isValidRow(row, expectedColumns):
                processedRow = processRowData(headers, row)
                reorderedRow = reorderRowToFixedHeaders(processedRow, headers, fixedHeaders)
                writer.writerow(reorderedRow)
                validRows.append(reorderedRow)
    
    print(f"CSV saved: {outputPath}")
    print(f"Stock: {stockSymbol}")
    print(f"Valid rows: {len(validRows)}")
    
    return validRows, fixedHeaders


def updateDatabase(stockSymbol, processedRows, fixedHeaders):
    """Update daily_bars table in database, skipping existing dates."""
    # Initialize database and create tables if not exist
    dataLayer = DataLayer()
    
    existingBars = dataLayer.get_daily_bars(stockSymbol)
    existingDates = {bar.date for bar in existingBars}
    
    dailyBars = []
    for processedRow in processedRows:
        dailyBar = convertToDailyBar(processedRow, fixedHeaders)
        if dailyBar and dailyBar.date not in existingDates:
            dailyBars.append(dailyBar)
    
    if dailyBars:
        dataLayer.store_daily_bars(stockSymbol, dailyBars)
        print(f"Database: Added {len(dailyBars)} new daily bars for {stockSymbol}")
        print(f"Database: Skipped {len(processedRows) - len(dailyBars)} existing dates")
    else:
        print(f"Database: All dates already exist for {stockSymbol}, no updates needed")
    
    # Calculate and update indicators for dates with null values
    updateIndicatorsForNullDates(stockSymbol, dataLayer)


def updateIndicatorsForNullDates(symbol, dataLayer):
    """Calculate and update daily indicators (MACD) for dates where values are null."""
    import sqlite3
    from config import DB_PATH
    
    print("\nCalculating indicators for null dates...")
    
    # Get all daily bars
    allDailyBars = dataLayer.get_daily_bars(symbol)
    if not allDailyBars or len(allDailyBars) < 35:
        print(f"  ⚠ Not enough daily bars for indicator calculation (need 35+, have {len(allDailyBars) if allDailyBars else 0})")
        return
    
    # Calculate MACD for all dates
    macdCalculated = dataLayer.calculate_macd_for_all_dates(allDailyBars)
    if not macdCalculated:
        print("  ⚠ MACD calculation failed")
        return
    
    # Get existing indicators to find null dates
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Get all dates with null MACD values
        c.execute('''
            SELECT date FROM daily_indicators 
            WHERE symbol = ? AND (macd IS NULL OR macd_signal IS NULL OR macd_histogram IS NULL)
        ''', (symbol,))
        nullDates = {row[0] for row in c.fetchall()}
        
        # Also check which dates from calculated MACD don't exist in indicators table
        c.execute('''
            SELECT DISTINCT date FROM daily_indicators WHERE symbol = ?
        ''', (symbol,))
        existingIndicatorDates = {row[0] for row in c.fetchall()}
        
        # Find dates that need updating (null in DB or don't exist)
        datesToUpdate = set()
        for date in macdCalculated.keys():
            if date in nullDates or date not in existingIndicatorDates:
                datesToUpdate.add(date)
        
        if not datesToUpdate:
            print(f"  ✓ All indicators already calculated for {symbol}")
            return
        
        # Update only null values
        updatedCount = 0
        for date in datesToUpdate:
            if date not in macdCalculated:
                continue
            
            macdVals = macdCalculated[date]
            macdLine = macdVals.get("MACD")
            macdSig = macdVals.get("MACD_Signal")
            macdHist = macdVals.get("MACD_Hist")
            
            if date in existingIndicatorDates:
                # Update existing row where MACD is null
                c.execute('''
                    UPDATE daily_indicators 
                    SET macd = COALESCE(macd, ?),
                        macd_signal = COALESCE(macd_signal, ?),
                        macd_histogram = COALESCE(macd_histogram, ?),
                        last_updated = CURRENT_TIMESTAMP
                    WHERE symbol = ? AND date = ?
                ''', (macdLine, macdSig, macdHist, symbol, date))
            else:
                # Insert new row with only MACD values (RSI and STOCHRSI will be NULL)
                c.execute('''
                    INSERT INTO daily_indicators
                    (symbol, date, macd, macd_signal, macd_histogram, last_updated)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (symbol, date, macdLine, macdSig, macdHist))
            
            updatedCount += 1
        
        conn.commit()
        print(f"  ✓ Updated MACD indicators for {updatedCount} dates (only null values updated)")
            
    except Exception as e:
        print(f"  ✗ Error updating indicators: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    # Ensure database and tables are initialized
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    DataLayer()  # Initialize database and create tables
    
    htmlFilePath = Path('cache/sss.html')
    
    if not htmlFilePath.exists():
        print(f"Error: {htmlFilePath} not found")
        return
    
    print(f"Reading HTML from: {htmlFilePath}")
    with open(htmlFilePath, 'r', encoding='utf-8') as f:
        htmlContent = f.read()
    
    stockSymbol = extractStockSymbol(htmlContent)
    print(f"Extracted stock symbol: {stockSymbol}")
    
    headers, rows = parseTableData(htmlContent)
    
    if not headers or not rows:
        print("Error: Could not extract table data from HTML")
        return
    
    print(f"Found {len(rows)} data rows")
    
    outputPath = Path(f'cache/{stockSymbol}_data.csv')
    processedRows, fixedHeaders = saveToCsv(stockSymbol, headers, rows, outputPath)
    
    print("\nUpdating database...")
    updateDatabase(stockSymbol, processedRows, fixedHeaders)


if __name__ == '__main__':
    main()

