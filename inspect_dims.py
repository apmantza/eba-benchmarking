import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')
cur = conn.cursor()

# Get all dim tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'dim_%'")
dim_tables = [t[0] for t in cur.fetchall()]
print(f"Dim tables: {dim_tables}")

# Inspect columns of relevant dim tables
for table in dim_tables:
    print(f"\n--- {table} ---")
    cur.execute(f"PRAGMA table_info({table})")
    cols = [col[1] for col in cur.fetchall()]
    print(cols)
    
    # Peek at data
    try:
        df = pd.read_sql(f"SELECT * FROM {table} LIMIT 3", conn)
        print(df)
    except:
        pass

conn.close()
