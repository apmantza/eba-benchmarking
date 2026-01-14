import sqlite3
conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()
cur.execute("SELECT template_code, row_id, row_label, amount FROM facts_pillar3 WHERE bank_name='Alpha Bank' AND source_page=15")
for r in cur.fetchall():
    print(r)
conn.close()
