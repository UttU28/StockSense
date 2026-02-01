import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "stock_gita.db"

def get_db_connection():
    """Create a database connection to the SQLite database."""
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with the schema."""
    conn = get_db_connection()
    c = conn.cursor()

    # 1. Year Behavior Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS year_behavior (
            year INTEGER PRIMARY KEY,
            profile TEXT,
            expected_volatility TEXT,
            seasonal_bias TEXT,
            expansion_probability REAL,
            distribution_probability REAL,
            consolidation_probability REAL,
            structural_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # 2. Seasonal Zones Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS seasonal_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            zone_name TEXT,
            start_date DATE,
            end_date DATE,
            volatility_profile TEXT,
            expansion_tendency REAL,
            key_events TEXT,
            FOREIGN KEY (year) REFERENCES year_behavior(year)
        );
    ''')

    # 3. Stock Gita Windows Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS stock_gita_windows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month_name TEXT,
            expansion_start DATE,
            expansion_end DATE,
            confidence_boost REAL,
            primary_signal TEXT,
            FOREIGN KEY (year) REFERENCES year_behavior(year)
        );
    ''')

    # 4. Monthly Patterns Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS monthly_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            symbol TEXT,
            month_name TEXT,
            typical_opportunities INTEGER,
            average_move_size REAL,
            expansion_probability REAL,
            typical_entry_zones TEXT,
            typical_profit_taking TEXT,
            notes TEXT,
            FOREIGN KEY (year) REFERENCES year_behavior(year),
            UNIQUE (year, symbol, month_name)
        );
    ''')
    
    # 5. Earnings Calendar Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS earnings_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            earnings_date DATE,
            period TEXT,
            year INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # 6. Trade History Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            direction TEXT,
            entry_date DATE,
            entry_price REAL,
            exit_date DATE,
            exit_price REAL,
            profit_loss REAL,
            confidence_at_entry INTEGER,
            regime_at_entry TEXT,
            is_options BOOLEAN,
            options_dte INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
