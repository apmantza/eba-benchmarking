import sqlite3
import pandas as pd

conn = sqlite3.connect('eba_data.db')
df = pd.read_sql("SELECT * FROM pillar3_dictionary WHERE template_code='IRRBB1'", conn)
print("Pillar 3 Dictionary - IRRBB1:")
print(df.to_string())
conn.close()
