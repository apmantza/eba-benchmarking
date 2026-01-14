import sqlite3
conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()
cur.execute("SELECT amount, row_label FROM facts_pillar3 WHERE bank_name='Alpha Bank' AND row_id='11a'")
print(cur.fetchall())
conn.close()
