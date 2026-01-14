import sqlite3
conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print(f"Tables: {tables}")

if 'institutions' in tables:
    print("\nInstitutions Table:")
    cur.execute("SELECT * FROM institutions")
    for row in cur.fetchall():
        print(row)

if 'facts_pillar3' in tables:
    print("\nFacts Pillar3 Sample:")
    cur.execute("SELECT lei, bank_name, period FROM facts_pillar3 LIMIT 5")
    for row in cur.fetchall():
        print(row)

conn.close()
