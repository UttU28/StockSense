from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from dataclasses import asdict

from main import analyze_symbol, backtest_symbol, scan_market
from models import SymbolState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GS Trading System API",
    description="REST API for stock analysis, backtesting, and market scanning",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://stocksense.thatinsaneguy.com",
        "https://stocksense.thatinsaneguy.com",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    account_size: float = Field(10000, description="Account size for position sizing")

class BacktestRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    account_size: float = Field(10000, description="Account size for backtesting")
    days: int = Field(100, description="Number of days to backtest")

class ScanRequest(BaseModel):
    symbols: Optional[List[str]] = Field(None, description="Custom watchlist (default used if not provided)")
    account_size: float = Field(10000, description="Account size for position sizing")

def state_to_dict(state: SymbolState) -> Dict[str, Any]:
    """Convert SymbolState to JSON-serializable dict"""
    if state is None:
        return None
    
    result = {
        "symbol": state.symbol,
        "last_updated": state.last_updated,
        "features": state.features,
        "bias": state.bias,
        "alerts": state.alerts,
        "regime": state.regime,
        "plan": state.plan,
    }
    
    if state.daily_bars:
        result["daily_bars"] = [asdict(bar) for bar in state.daily_bars[:5]]
        result["current_price"] = state.daily_bars[0].close if state.daily_bars else None
    
    return result

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "GS Trading System API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    Analyze a stock symbol and get trading signals
    
    - **symbol**: Stock ticker symbol (e.g., AAPL, TSLA)
    - **account_size**: Account size for position sizing calculations
    """
    try:
        symbol = request.symbol.upper()
        state, position_result = analyze_symbol(symbol, request.account_size, silent=True)
        
        if state is None or position_result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to fetch data for symbol {symbol}. Check if symbol is valid."
            )
        
        return {
            "success": True,
            "symbol": symbol,
            "account_size": request.account_size,
            "analysis": state_to_dict(state),
            "position": position_result
        }
    except Exception as e:
        logger.error(f"Error analyzing {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest")
async def backtest(request: BacktestRequest):
    """
    Run backtest on a stock symbol
    
    - **symbol**: Stock ticker symbol
    - **account_size**: Starting account size
    - **days**: Number of days to backtest (default: 100)
    """
    try:
        symbol = request.symbol.upper()
        from backtester import Backtester
        from data_layer import DataLayer
        
        dl = DataLayer()
        state = dl.fetch_symbol_data(symbol)
        
        if not state.daily_bars:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to fetch data for symbol {symbol}"
            )
        
        bt = Backtester(start_days_ago=request.days, account_size=request.account_size)
        results = bt.run_backtest(state)
        
        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])
        
        return {
            "success": True,
            "symbol": symbol,
            "account_size": request.account_size,
            "days": request.days,
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error backtesting {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scan")
async def scan(request: ScanRequest):
    """
    Scan multiple stocks for trading opportunities
    
    - **symbols**: Optional list of symbols to scan (default watchlist used if not provided)
    - **account_size**: Account size for position sizing
    """
    try:
        symbols_str = None
        from main import analyze_symbol
        from data_layer import DataLayer
        
        default_watchlist = ['NVDA', 'TSLA', 'AMD', 'MSFT', 'AMZN', 'GOOGL', 'META', 'AAPL']
        watchlist = request.symbols if request.symbols else default_watchlist
        watchlist = [s.upper() for s in watchlist]
        
        opportunities = []
        
        for sym in watchlist:
            try:
                state, pos = analyze_symbol(sym, request.account_size, silent=True)
                if not state: 
                    continue
                
                entry_conf = state.plan.get("entry_analysis", {}).get("entry_confidence", 0)
                checklist = state.plan.get("entry_analysis", {}).get("checklist", [])
                reason_str = ", ".join(checklist[:3]) if checklist else "None"
                
                if entry_conf >= 40:
                    opportunities.append({
                        "symbol": sym,
                        "bias": state.bias.get("bias"),
                        "confidence": entry_conf,
                        "strategy": state.plan.get("options_strategy", {}).get("type"),
                        "take_profit_1r": pos.get("take_profit_1r"),
                        "take_profit_2r": pos.get("take_profit_1"),
                        "units": pos.get("units"),
                        "reason": reason_str,
                        "current_price": state.daily_bars[0].close if state.daily_bars else None
                    })
            except Exception as e:
                logger.warning(f"Error scanning {sym}: {e}")
                continue
        
        opportunities.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "success": True,
            "account_size": request.account_size,
            "watchlist": watchlist,
            "opportunities": opportunities,
            "count": len(opportunities)
        }
    except Exception as e:
        logger.error(f"Error scanning market: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/symbols/{symbol}/price")
async def get_current_price(symbol: str):
    """Get current price for a symbol"""
    try:
        from data_layer import DataLayer
        dl = DataLayer()
        state = dl.fetch_symbol_data(symbol.upper())
        
        if not state.daily_bars:
            raise HTTPException(status_code=404, detail="Symbol not found")
        
        latest_bar = state.daily_bars[0]
        return {
            "success": True,
            "symbol": symbol.upper(),
            "price": latest_bar.close,
            "date": latest_bar.date,
            "open": latest_bar.open,
            "high": latest_bar.high,
            "low": latest_bar.low,
            "volume": latest_bar.volume
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/symbols/{symbol}/chart")
async def get_chart_data(symbol: str, days: int = Query(30, ge=1, le=100)):
    """
    Get historical price data for charting
    
    - **symbol**: Stock ticker symbol
    - **days**: Number of days of data to return (default: 30, max: 100)
    """
    try:
        from data_layer import DataLayer
        dl = DataLayer()
        state = dl.fetch_symbol_data(symbol.upper())
        
        if not state.daily_bars:
            raise HTTPException(status_code=404, detail="Symbol not found")
        
        days = min(max(1, days), 100)
        sorted_bars = sorted(state.daily_bars, key=lambda x: x.date)
        chart_data = sorted_bars[-days:]
        
        chart_points = []
        for bar in chart_data:
            chart_points.append({
                "date": bar.date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume
            })
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "days": days,
            "data": chart_points,
            "current_price": chart_points[-1]["close"] if chart_points else None,
            "price_change": chart_points[-1]["close"] - chart_points[0]["close"] if len(chart_points) > 1 else 0,
            "price_change_pct": ((chart_points[-1]["close"] - chart_points[0]["close"]) / chart_points[0]["close"] * 100) if len(chart_points) > 1 and chart_points[0]["close"] > 0 else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chart data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

