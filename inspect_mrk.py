import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')
cur = conn.cursor()

table = 'facts_mrk'

print(f"\n--- {table} Schema ---")
cur.execute(f"PRAGMA table_info({table})")
cols = [col[1] for col in cur.fetchall()]
print(cols)

print(f"\n--- {table} Sample ---")
try:
    df = pd.read_sql(f"SELECT * FROM {table} LIMIT 3", conn)
    print(df)
except Exception as e:
    print(e)
    
# Inspect potential dim tables for MRK
# Common suffixes in columns might hint at dim tables. e.g. 'portfolio', 'instrument', etc.

conn.close()
