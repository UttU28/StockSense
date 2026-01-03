from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from dataclasses import asdict

from main import analyze_symbol, backtest_symbol, scan_market
from models import SymbolState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GS Trading System API",
    description="REST API for stock analysis, backtesting, and market scanning",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
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

# Helper function to convert SymbolState to dict
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
    
    # Convert daily bars
    if state.daily_bars:
        result["daily_bars"] = [asdict(bar) for bar in state.daily_bars[:5]]  # Last 5 bars
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
        logger.info(f"Analyzing {symbol} with account size ${request.account_size}")
        
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
        logger.info(f"Backtesting {symbol} for {request.days} days with account ${request.account_size}")
        
        # Import Backtester directly to use custom days
        from backtester import Backtester
        from data_layer import DataLayer
        
        # Fetch data
        dl = DataLayer()
        state = dl.fetch_symbol_data(symbol)
        
        if not state.daily_bars:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to fetch data for symbol {symbol}"
            )
        
        # Run backtest
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
        if request.symbols:
            symbols_str = ",".join([s.upper() for s in request.symbols])
        
        logger.info(f"Scanning market with account size ${request.account_size}")
        
        # We need to modify scan_market to return data instead of printing
        # For now, let's create a modified version
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
        
        # Sort by confidence
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

