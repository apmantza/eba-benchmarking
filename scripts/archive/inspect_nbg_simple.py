import sqlite3
import pandas as pd
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'eba_data.db')
conn = sqlite3.connect(db_path)

print("=== Current Market Data (ETE.AT) ===")
df_current = pd.read_sql("SELECT ticker, dividend_yield FROM market_data WHERE ticker = 'ETE.AT'", conn)
for _, row in df_current.iterrows():
    print(f"Yield: {row['dividend_yield'] * 100:.2f}%")

conn.close()
