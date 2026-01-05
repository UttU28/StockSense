import math
from typing import List, Dict, Any
from datetime import datetime, timedelta

def calculate_options_prices(current_price: float, atr: float, strike_prices: List[float], days_to_expiry: int) -> Dict[str, Any]:
    """
    Calculate Call and Put option prices using simplified Black-Scholes approximation.
    
    Args:
        current_price: Current stock price
        atr: Average True Range (used as volatility proxy)
        strike_prices: List of strike prices to calculate
        days_to_expiry: Days until expiration
    
    Returns:
        Dictionary with call and put prices for each strike
    """
    # Convert ATR to annualized volatility (rough approximation)
    # ATR is typically 1-5% of price, so we scale it
    daily_vol = (atr / current_price) if current_price > 0 else 0.02
    annual_vol = daily_vol * math.sqrt(252)  # Annualize
    
    # Risk-free rate (approximate)
    risk_free_rate = 0.05
    
    # Time to expiration in years
    time_to_expiry = days_to_expiry / 365.0
    
    options_data = []
    
    for strike in strike_prices:
        # Calculate intrinsic value
        call_intrinsic = max(0, current_price - strike)
        put_intrinsic = max(0, strike - current_price)
        
        # Calculate time value using simplified Black-Scholes
        if time_to_expiry > 0:
            # Moneyness
            moneyness = current_price / strike if strike > 0 else 1.0
            
            # Simplified time value calculation
            # Time value decays with square root of time
            time_factor = math.sqrt(time_to_expiry)
            
            # Volatility factor
            vol_factor = annual_vol * time_factor
            
            # Time value approximation
            # For calls: higher for ITM, decays for OTM
            # For puts: higher for ITM, decays for OTM
            if moneyness > 1.0:  # ITM call
                call_time_value = current_price * 0.02 * time_factor * (1 + vol_factor)
            elif moneyness > 0.95:  # Near ATM
                call_time_value = current_price * 0.03 * time_factor * (1 + vol_factor * 1.5)
            else:  # OTM
                call_time_value = current_price * 0.01 * time_factor * vol_factor
            
            if moneyness < 1.0:  # ITM put
                put_time_value = current_price * 0.02 * time_factor * (1 + vol_factor)
            elif moneyness < 1.05:  # Near ATM
                put_time_value = current_price * 0.03 * time_factor * (1 + vol_factor * 1.5)
            else:  # OTM
                put_time_value = current_price * 0.01 * time_factor * vol_factor
        else:
            call_time_value = 0
            put_time_value = 0
        
        call_price = call_intrinsic + call_time_value
        put_price = put_intrinsic + put_time_value
        
        # Ensure minimum price (no free options)
        call_price = max(0.01, call_price)
        put_price = max(0.01, put_price)
        
        options_data.append({
            "strike": round(strike, 2),
            "call_price": round(call_price, 2),
            "put_price": round(put_price, 2),
            "call_intrinsic": round(call_intrinsic, 2),
            "put_intrinsic": round(put_intrinsic, 2),
            "call_time_value": round(call_time_value, 2),
            "put_time_value": round(put_time_value, 2),
            "moneyness": round(moneyness, 4)
        })
    
    return {
        "current_price": round(current_price, 2),
        "expiration_date": (datetime.now() + timedelta(days=days_to_expiry)).strftime("%Y-%m-%d"),
        "days_to_expiry": days_to_expiry,
        "volatility": round(annual_vol * 100, 2),
        "options": options_data
    }

def generate_options_chain(current_price: float, atr: float) -> List[Dict[str, Any]]:
    """
    Generate a complete options chain with multiple expiration dates.
    
    Args:
        current_price: Current stock price
        atr: Average True Range
    
    Returns:
        List of options chains for different expiration dates
    """
    # Generate strike prices around current price
    # Typically: 5 strikes below, ATM, 5 strikes above
    strike_step = max(2.5, current_price * 0.02)  # 2% steps, minimum $2.50
    strikes = []
    
    # Generate strikes from 10% below to 10% above current price
    for i in range(-5, 6):
        strike = current_price + (i * strike_step)
        if strike > 0:
            strikes.append(round(strike / 5) * 5)  # Round to nearest $5
    
    # Remove duplicates and sort
    strikes = sorted(list(set(strikes)))
    
    # Generate options for different expiration dates
    expiration_dates = [7, 14, 21, 30, 45, 60]  # Weekly, bi-weekly, monthly, etc.
    
    chains = []
    for dte in expiration_dates:
        chain_data = calculate_options_prices(current_price, atr, strikes, dte)
        chains.append(chain_data)
    
    return chains

