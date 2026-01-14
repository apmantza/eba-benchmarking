import sqlite3

conn = sqlite3.connect('eba_data.db')

nii_rows = [
    ('IRRBB1', 'EU-1', 'Parallel up', '2525011', 'Interest Rate Risk'),
    ('IRRBB1', 'EU-2', 'Parallel down', '2525012', 'Interest Rate Risk'),
]

print("Adding NII rows to pillar3_dictionary...")
for tmpl, rid, label, eba_id, cat in nii_rows:
    p3_item_id = f"{tmpl}_{rid}"
    conn.execute("""
        INSERT OR REPLACE INTO pillar3_dictionary 
        (p3_item_id, template_code, row_id, p3_label, eba_item_id, category)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (p3_item_id, tmpl, rid, label, eba_id, cat))

conn.commit()
print("Done.")
conn.close()
