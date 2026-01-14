import sqlite3
conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()
cur.execute("SELECT row_id, row_label FROM pillar3_templates WHERE template_code='KM1' ORDER BY row_id")
for res in cur.fetchall():
    print(res)
conn.close()
