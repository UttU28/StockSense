"""
Stock Gita Ticker API Endpoint
Provides real-time market data for ticker bar
Uses YFinance to fetch live prices
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import yfinance as yf
from typing import Dict, Any
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/ticker", tags=["ticker"])

@router.get("/{symbol}")
async def get_ticker_data(symbol: str) -> Dict[str, Any]:
    """
    Fetch real-time ticker data for a given symbol.
    
    Args:
        symbol: Stock symbol (e.g., 'SPY', 'QQQ', '^VIX', 'BTC-USD')
    
    Returns:
        Dict with price, change, and metadata
    """
    try:
        logger.info(f"Fetching ticker data for {symbol}")
        
        # Fetch data from YFinance
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get current price and previous close
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('price', 0)
        previous_close = info.get('previousClose', current_price)
        
        # Calculate change
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close > 0 else 0
        
        # Build response
        response = {
            "symbol": symbol,
            "currentPrice": current_price,
            "previousClose": previous_close,
            "change": change,
            "changePercent": change_percent,
            "dayHigh": info.get('dayHigh'),
            "dayLow": info.get('dayLow'),
            "volume": info.get('volume'),
            "marketCap": info.get('marketCap'),
            "timestamp": info.get('regularMarketTime')
        }
        
        logger.info(f"Successfully fetched {symbol}: ${current_price}")
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error fetching ticker data for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch ticker data for {symbol}: {str(e)}"
        )


@router.get("/batch/{symbols}")
async def get_batch_ticker_data(symbols: str) -> Dict[str, Any]:
    """
    Fetch ticker data for multiple symbols at once.
    
    Args:
        symbols: Comma-separated list of symbols (e.g., 'SPY,QQQ,DIA')
    
    Returns:
        Dict with ticker data for all symbols
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        logger.info(f"Fetching batch ticker data for {len(symbol_list)} symbols")
        
        results = {}
        
        for symbol in symbol_list:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('price', 0)
                previous_close = info.get('previousClose', current_price)
                change = current_price - previous_close
                change_percent = (change / previous_close * 100) if previous_close > 0 else 0
                
                results[symbol] = {
                    "currentPrice": current_price,
                    "previousClose": previous_close,
                    "change": change,
                    "changePercent": change_percent
                }
                
            except Exception as e:
                logger.error(f"Error fetching {symbol} in batch: {str(e)}")
                results[symbol] = {
                    "error": str(e),
                    "currentPrice": 0,
                    "change": 0,
                    "changePercent": 0
                }
        
        return JSONResponse(content={"data": results})
        
    except Exception as e:
        logger.error(f"Error in batch ticker fetch: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch batch ticker data: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for ticker API"""
    return {"status": "healthy", "service": "ticker-api"}
