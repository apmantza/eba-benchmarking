
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')
cursor = conn.cursor()

queries = [
    "SELECT item_id, label FROM dictionary WHERE label LIKE '%Staff expenses%'",
    "SELECT item_id, label FROM dictionary WHERE label LIKE '%Loans and advances%' AND (label LIKE '%Net%' OR label LIKE '%carrying amount%') LIMIT 20"
]

for q in queries:
    print(f"Query: {q}")
    df = pd.read_sql_query(q, conn)
    print(df.to_markdown())
    print("-" * 50)

conn.close()
