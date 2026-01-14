import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')
cur = conn.cursor()

# Get all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]

# Filter for 'dict'
dict_tables = [t for t in tables if 'dict' in t.lower()]
print(f"Dictionary tables found: {dict_tables}")

for t in dict_tables:
    print(f"\n--- {t} Schema ---")
    cur.execute(f"PRAGMA table_info({t})")
    print([col[1] for col in cur.fetchall()])
    
    print(f"--- {t} Sample ---")
    try:
        df = pd.read_sql(f"SELECT * FROM {t} LIMIT 3", conn)
        print(df)
    except Exception as e:
        print(e)

conn.close()
