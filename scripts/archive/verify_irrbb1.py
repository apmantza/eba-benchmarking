import sqlite3
import pandas as pd

conn = sqlite3.connect('eba_data.db')
query = """
SELECT 
    bank_name, 
    row_id, 
    amount, 
    dimension_name 
FROM facts_pillar3 
WHERE template_code='IRRBB1' AND bank_name='Eurobank' 
ORDER BY dimension_name, row_id
"""
df = pd.read_sql(query, conn)
print("IRRBB1 Verified Data:")
print(df.to_string())
conn.close()
