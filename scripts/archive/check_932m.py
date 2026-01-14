import sqlite3

conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()
cur.execute("SELECT raw_label, amount, row_id FROM facts_pillar3 WHERE bank_name='Eurobank' AND amount=9.32e8")
for r in cur.fetchall():
    print(f"Row ID: {r[2]}, Amount: {r[1]}, Raw Label: {repr(r[0])}")
conn.close()
