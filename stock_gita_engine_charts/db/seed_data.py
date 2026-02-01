import sqlite3
import json
from .database import get_db_connection, init_db

def seed_data():
    conn = get_db_connection()
    c = conn.cursor()

    # 1. Year Behavior (2026)
    year_data = (
        2026, 
        "expansion", "moderate", "bullish_Q1_Q4", 
        0.72, 0.18, 0.10, 
        "Strong first half likely, profit-taking Q3"
    )
    
    try:
        c.execute('''
            INSERT INTO year_behavior (year, profile, expected_volatility, seasonal_bias, 
                                      expansion_probability, distribution_probability, 
                                      consolidation_probability, structural_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', year_data)
    except sqlite3.IntegrityError:
        print("Year 2026 already exists, skipping...")

    # 2. Seasonal Zones (2026)
    zones = [
        (2026, "fall_winter", "2026-09-01", "2026-12-31", "high", 0.65, 
         json.dumps(["September sell-off window", "October volatility", "November recovery", "December rally"])),
        (2026, "transitional", "2026-01-01", "2026-03-31", "moderate", 0.68, 
         json.dumps(["January effect", "Earnings season prep"])),
        (2026, "spring_summer", "2026-04-01", "2026-08-31", "low", 0.55, 
         json.dumps(["Summer doldrums", "Vacation trading"]))
    ]
    
    for z in zones:
        c.execute('''
            INSERT INTO seasonal_zones (year, zone_name, start_date, end_date, 
                                      volatility_profile, expansion_tendency, key_events)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', z)

    # 3. Monthly Patterns (Generic Template for 2026)
    # Adding a generic pattern for 'NVDA' as an example
    pattern_data = (
        2026, "NVDA", "january", 
        2, 3.2, 0.72, 
        json.dumps(["week 1-2", "week 3"]), 
        json.dumps(["week 3-4"]), 
        "Q4 earnings carryover, January effect"
    )
    
    try:
        c.execute('''
            INSERT INTO monthly_patterns (year, symbol, month_name, typical_opportunities,
                                        average_move_size, expansion_probability,
                                        typical_entry_zones, typical_profit_taking, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', pattern_data)
    except sqlite3.IntegrityError:
        pass

    # 4. Stock Gita Windows (Example: January)
    window_data = (
        2026, "january", "2026-01-08", "2026-01-22", 0.10, "breakout"
    )
    
    c.execute('''
        INSERT INTO stock_gita_windows (year, month_name, expansion_start, expansion_end,
                                      confidence_boost, primary_signal)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', window_data)

    conn.commit()
    conn.close()
    print("Database seeded with 2026 data.")

if __name__ == "__main__":
    init_db()
    seed_data()
