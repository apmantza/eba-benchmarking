import sqlite3
import pandas as pd

conn = sqlite3.connect('eba_data.db')
query = """
SELECT 
    row_id, 
    row_label, 
    amount,
    source_page
FROM facts_pillar3 
WHERE template_code='KM1' AND bank_name='Alpha Bank'
ORDER BY CAST(row_id AS INTEGER)
"""
df = pd.read_sql(query, conn)
print("Alpha Bank KM1 Data:")
print(df.to_string())
conn.close()
