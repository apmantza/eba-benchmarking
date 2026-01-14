import sqlite3
conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()
cur.execute("SELECT row_id, amount, row_label FROM facts_pillar3 WHERE bank_name='Piraeus' AND template_code='KM1' AND row_id IN ('17','18','19','20')")
for res in cur.fetchall():
    print(res)
conn.close()
