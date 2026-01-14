import sqlite3
conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print(f"Tables: {tables}")
for table in tables:
    tname = table[0]
    if tname == 'institutions':
        print(f"\nSchema for {tname}:")
        cur.execute(f"PRAGMA table_info({tname})")
        for col in cur.fetchall():
            print(col)
        print(f"\nData in {tname}:")
        cur.execute(f"SELECT * FROM {tname}")
        for row in cur.fetchall():
            print(row)
conn.close()
