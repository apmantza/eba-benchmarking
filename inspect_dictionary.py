import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')
cur = conn.cursor()

t = 'dictionary'
print(f"--- {t} Schema ---")
cur.execute(f"PRAGMA table_info({t})")
print([col[1] for col in cur.fetchall()])

print(f"--- {t} Sample ---")
df = pd.read_sql(f"SELECT * FROM {t} LIMIT 3", conn)
print(df)

conn.close()
