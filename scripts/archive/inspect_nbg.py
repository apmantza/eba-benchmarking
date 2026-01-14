import sqlite3
import pandas as pd
import os

# Database path
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'eba_data.db')
conn = sqlite3.connect(db_path)

# Check current market data
print("=== Current Market Data (ETE.AT) ===")
df_current = pd.read_sql("SELECT ticker, current_price, dividend_rate, dividend_yield, last_dividend_value FROM market_data WHERE ticker = 'ETE.AT'", conn)
print(df_current.to_string())

# Check historical data which might be used for the charts
print("\n=== Recent Historical Data (ETE.AT) ===")
df_hist = pd.read_sql("SELECT date, close, dividend, dividend_ttm, dividend_yield FROM market_history WHERE ticker = 'ETE.AT' ORDER BY date DESC LIMIT 5", conn)
print(df_hist.to_string())

conn.close()
