import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')
cur = conn.cursor()

# Get all facts tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'facts_%'")
tables = [t[0] for t in cur.fetchall()]
print(f"Facts tables: {tables}")

conn.close()
