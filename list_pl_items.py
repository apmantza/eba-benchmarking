
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')
pd.set_option('display.max_colwidth', None)

# Get all P&L items (usually 25203xx range)
query = "SELECT item_id, label FROM dictionary WHERE item_id LIKE '25203%'"
df = pd.read_sql_query(query, conn)
print("--- P&L Items ---")
print(df.to_markdown())

# Get specific loan items
query2 = "SELECT item_id, label FROM dictionary WHERE label LIKE '%Loans and advances%' AND item_id LIKE '25210%'"
df2 = pd.read_sql_query(query2, conn)
print("\n--- Asset Items ---")
print(df2.head(20).to_markdown())

conn.close()
