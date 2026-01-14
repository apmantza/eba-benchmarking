import sqlite3
import pandas as pd

conn = sqlite3.connect('eba_data.db')
query = """
SELECT 
    bank_name, 
    dimension_name, 
    count(*) as count 
FROM facts_pillar3 
WHERE template_code='IRRBB1' 
GROUP BY bank_name, dimension_name
"""
df = pd.read_sql(query, conn)
print("IRRBB1 Data Distribution:")
print(df.to_string())
conn.close()
