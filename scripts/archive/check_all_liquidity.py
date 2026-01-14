import sqlite3
import pandas as pd

conn = sqlite3.connect('eba_data.db')
query = """
SELECT bank_name, period, row_id, amount, row_label
FROM facts_pillar3
WHERE template_code = 'KM1' AND row_id IN ('17','18','19','20')
ORDER BY bank_name, period, CAST(row_id AS INTEGER)
"""
df = pd.read_sql_query(query, conn)
df.to_csv('output/liquidity_check.csv', index=False)
print(df.to_string())
print(f"\nTotal rows: {len(df)}")
conn.close()
