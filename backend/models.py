from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class DailyBar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass
class IndicatorSet:
    # We store indicators as generic dicts for flexibility, 
    # or specific fields if we want strict typing.
    # For now, flexible dicts to match the JSON-heavy nature of the project.
    daily_rsi: Dict[str, float] = field(default_factory=dict)
    daily_stoch_rsi: Dict[str, Dict[str, float]] = field(default_factory=dict) # {date: {FastK, FastD}}
    daily_macd: Dict[str, Dict[str, float]] = field(default_factory=dict) # {date: {macd, signal, hist}}
    weekly_rsi: Dict[str, float] = field(default_factory=dict)
    weekly_macd: Dict[str, Dict[str, float]] = field(default_factory=dict)

@dataclass
class EarningsRecord:
    fiscal_date_ending: str
    reported_date: str
    reported_eps: Optional[float] = None
    estimated_eps: Optional[float] = None
    surprise: Optional[float] = None
    surprise_percentage: Optional[float] = None

@dataclass
class SymbolState:
    symbol: str
    last_updated: str
    daily_bars: List[DailyBar] = field(default_factory=list)
    indicators: IndicatorSet = field(default_factory=IndicatorSet)
    earnings: List[EarningsRecord] = field(default_factory=list)
    
    # Computed Features
    features: Dict[str, Any] = field(default_factory=dict)
    
    # Rules Output
    bias: Dict[str, Any] = field(default_factory=dict)
    alerts: Dict[str, Any] = field(default_factory=dict)
    regime: Dict[str, Any] = field(default_factory=dict)
    plan: Dict[str, Any] = field(default_factory=dict)
