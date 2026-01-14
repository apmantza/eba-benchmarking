import sqlite3
conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()
cur.execute("SELECT row_id, row_label FROM pillar3_templates WHERE template_code='KM1' AND row_id LIKE '5%'")
for r in cur.fetchall():
    print(r)
conn.close()
