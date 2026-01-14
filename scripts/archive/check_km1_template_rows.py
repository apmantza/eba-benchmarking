import sqlite3
conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()
cur.execute("SELECT row_id, row_label FROM pillar3_templates WHERE template_code='KM1'")
for rid, lbl in cur.fetchall():
    if rid in ['15','16','17','18','19','20','21','EU 16a', 'EU 16b']:
        print(f"{rid} | {lbl}")
conn.close()
