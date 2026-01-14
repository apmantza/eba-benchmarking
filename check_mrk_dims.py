import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')
cur = conn.cursor()

# Get all dim tables again to be sure
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'dim_%'")
dim_tables = [t[0] for t in cur.fetchall()]
print(f"Dim tables: {dim_tables}")

# Check specific columns in facts_mrk vs dim tables
if 'dim_mkt_prod' in dim_tables:
    print("Found dim_mkt_prod")
if 'dim_mkt_risk' in dim_tables:
    print("Found dim_mkt_risk")

conn.close()
