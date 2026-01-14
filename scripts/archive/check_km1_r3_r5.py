import sqlite3

conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()
cur.execute("SELECT bank_name, row_id, amount FROM facts_pillar3 WHERE template_code='KM1' AND row_id IN ('3', '5') ORDER BY row_id, bank_name")
print(f"{'Bank':25} | ID | {'Amount':>20}")
print("-" * 55)
for row in cur.fetchall():
    print(f"{row[0]:25} | {row[1]:2} | {row[2]:20,.4f}")
conn.close()
