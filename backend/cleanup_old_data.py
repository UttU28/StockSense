"""
One-time cleanup script to delete data on or before 2021-01-15 from all tables.
This helps keep the database focused on recent data (last 5 years).

Usage:
    python cleanup_old_data.py
    python cleanup_old_data.py --date 2021-01-15  # Custom cutoff date
"""

import sqlite3
import sys
from datetime import datetime
from config import DB_PATH

def cleanup_old_data(cutoff_date: str = "2021-01-15"):
    """
    Delete all data on or before the cutoff date from all historical tables.
    
    Args:
        cutoff_date: Date string in YYYY-MM-DD format. Data on or before this date will be deleted.
    """
    print(f"\n{'='*60}")
    print(f"Cleaning up data on or before {cutoff_date}")
    print(f"{'='*60}\n")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Tables with date column
        tables_to_clean = [
            ("daily_bars", "date"),
            ("weekly_bars", "date"),
            ("daily_indicators", "date"),
            ("weekly_indicators", "date"),
        ]
        
        # Earnings table uses fiscal_date_ending
        earnings_table = ("earnings", "fiscal_date_ending")
        
        total_deleted = 0
        
        for table_name, date_column in tables_to_clean:
            # Count rows to be deleted
            c.execute(f'SELECT COUNT(*) FROM {table_name} WHERE {date_column} <= ?', (cutoff_date,))
            count = c.fetchone()[0]
            
            if count > 0:
                # Delete old data
                c.execute(f'DELETE FROM {table_name} WHERE {date_column} <= ?', (cutoff_date,))
                deleted = c.rowcount
                total_deleted += deleted
                print(f"✓ {table_name}: Deleted {deleted} rows")
            else:
                print(f"  {table_name}: No data to delete")
        
        # Handle earnings table separately
        c.execute(f'SELECT COUNT(*) FROM {earnings_table[0]} WHERE {earnings_table[1]} <= ?', (cutoff_date,))
        earnings_count = c.fetchone()[0]
        
        if earnings_count > 0:
            c.execute(f'DELETE FROM {earnings_table[0]} WHERE {earnings_table[1]} <= ?', (cutoff_date,))
            deleted = c.rowcount
            total_deleted += deleted
            print(f"✓ {earnings_table[0]}: Deleted {deleted} rows")
        else:
            print(f"  {earnings_table[0]}: No data to delete")
        
        # Commit changes
        conn.commit()
        
        print(f"\n{'='*60}")
        print(f"Cleanup complete: Deleted {total_deleted} total rows")
        print(f"{'='*60}\n")
        
        # Show remaining data counts
        print("Remaining data counts:")
        for table_name, date_column in tables_to_clean + [earnings_table]:
            c.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = c.fetchone()[0]
            if count > 0:
                # Get date range
                c.execute(f'SELECT MIN({date_column}), MAX({date_column}) FROM {table_name}')
                min_date, max_date = c.fetchone()
                print(f"  {table_name}: {count} rows (from {min_date} to {max_date})")
            else:
                print(f"  {table_name}: 0 rows")
        
        return total_deleted
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error during cleanup: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    cutoff = "2021-01-15"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--date" and len(sys.argv) > 2:
            cutoff = sys.argv[2]
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage:")
            print("  python cleanup_old_data.py                    # Default: 2021-01-15")
            print("  python cleanup_old_data.py --date 2020-01-01   # Custom date")
            sys.exit(0)
    
    # Validate date format
    try:
        datetime.strptime(cutoff, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format. Use YYYY-MM-DD (e.g., 2021-01-15)")
        sys.exit(1)
    
    print(f"⚠️  WARNING: This will permanently delete all data on or before {cutoff}")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        cleanup_old_data(cutoff)
    else:
        print("Cleanup cancelled.")

