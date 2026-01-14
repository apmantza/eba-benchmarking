import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')

# Check kri_to_item columns
print("--- kri_to_item ---")
df_map = pd.read_sql("SELECT * FROM kri_to_item LIMIT 5", conn)
print(df_map)

# Check distinct items in facts_cre
print("\n--- facts_cre items ---")
cre_items = pd.read_sql("SELECT DISTINCT item_id FROM facts_cre", conn)
print(f"Count: {len(cre_items)}")

# Check overlap
joined = pd.read_sql("""
SELECT DISTINCT f.item_id, k.kri_label 
FROM facts_cre f 
LEFT JOIN kri_to_item k ON f.item_id = k.item_id
""", conn)

print("\n--- Overlap Check ---")
print(joined.head(10))
print(f"Mapped items: {joined['kri_label'].notna().sum()} / {len(joined)}")

conn.close()
