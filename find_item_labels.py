import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')
cur = conn.cursor()

# Get all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]
print(f"Tables: {tables}")

# Check for 'items' or 'labels' in table names
potential_tables = [t for t in tables if 'item' in t.lower() or 'label' in t.lower() or 'desc' in t.lower()]
print(f"Potential item label tables: {potential_tables}")

for t in potential_tables:
    print(f"\n--- {t} Schema ---")
    cur.execute(f"PRAGMA table_info({t})")
    print([col[1] for col in cur.fetchall()])
    
    print(f"--- {t} Sample ---")
    try:
        df = pd.read_sql(f"SELECT * FROM {t} LIMIT 3", conn)
        print(df)
    except:
        pass

conn.close()
