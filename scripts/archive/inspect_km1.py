import sqlite3
import pandas as pd

conn = sqlite3.connect('eba_data.db')
query = """
SELECT 
    bank_name, 
    row_id, 
    row_label,
    amount, 
    dimension_name 
FROM facts_pillar3 
WHERE template_code='KM1' AND row_id IN ('1', '2', '3', '4', '5', '6', '7', '13')
ORDER BY row_id, bank_name
"""
df = pd.read_sql(query, conn)
print("KM1 Data Inspection:")
print(df.to_string())
conn.close()
