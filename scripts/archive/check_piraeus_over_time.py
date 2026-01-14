import sqlite3
import pandas as pd

conn = sqlite3.connect('eba_data.db')
query = """
SELECT period, row_id, amount, row_label, source_page
FROM facts_pillar3
WHERE bank_name = 'Piraeus' AND template_code = 'KM1' AND row_id IN ('17','18','19','20')
ORDER BY period, CAST(row_id AS INTEGER)
"""
df = pd.read_sql_query(query, conn)
print(df.to_string())
conn.close()
