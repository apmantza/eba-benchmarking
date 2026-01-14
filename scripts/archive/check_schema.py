import sqlite3
conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info(facts_pillar3)")
for col in cur.fetchall():
    print(col)
conn.close()
