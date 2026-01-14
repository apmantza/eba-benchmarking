
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')
cursor = conn.cursor()

search_terms = ['Fee', 'Staff', 'Interest expense', 'Loans', 'Deposit']
dfs = []

for term in search_terms:
    query = f"SELECT item_id, label, category FROM dictionary WHERE label LIKE '%{term}%'"
    df = pd.read_sql_query(query, conn)
    dfs.append(df)

full_df = pd.concat(dfs)
print(full_df[full_df['label'].str.len() < 100].head(100).to_markdown())

conn.close()
