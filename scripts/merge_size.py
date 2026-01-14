"""
Merge size data from bank_models into institutions table
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from eba_benchmarking.config import DB_NAME
import sqlite3
import pandas as pd

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

print("=== CURRENT STATE ===")

# Check if columns already exist
cursor.execute("PRAGMA table_info(institutions)")
existing_cols = [col[1] for col in cursor.fetchall()]
print(f"Existing columns: {existing_cols}")

# Check bank_models
df_bm = pd.read_sql("SELECT COUNT(*) as cnt FROM bank_models", conn)
print(f"Banks in bank_models: {df_bm.iloc[0]['cnt']}")

df_size = pd.read_sql("SELECT size_category, COUNT(*) as count FROM bank_models GROUP BY size_category ORDER BY count DESC", conn)
print(f"\nSize distribution:")
print(df_size.to_string())

# Step 1: Add columns if not exist
print("\n=== ADDING COLUMNS ===")
new_cols = ['total_assets', 'size_category', 'business_model']
for col in new_cols:
    if col not in existing_cols:
        try:
            if col == 'total_assets':
                cursor.execute(f"ALTER TABLE institutions ADD COLUMN {col} REAL")
            else:
                cursor.execute(f"ALTER TABLE institutions ADD COLUMN {col} TEXT")
            print(f"  Added column: {col}")
        except Exception as e:
            print(f"  Column {col} already exists or error: {e}")
    else:
        print(f"  Column {col} already exists")

conn.commit()

# Step 2: Update from bank_models
print("\n=== UPDATING DATA ===")
cursor.execute("""
    UPDATE institutions
    SET 
        total_assets = (SELECT bm.total_assets FROM bank_models bm WHERE bm.lei = institutions.lei),
        size_category = (SELECT bm.size_category FROM bank_models bm WHERE bm.lei = institutions.lei),
        business_model = (SELECT bm.business_model FROM bank_models bm WHERE bm.lei = institutions.lei)
""")
updated = cursor.rowcount
conn.commit()
print(f"  Updated {updated} rows")

# Verify
print("\n=== VERIFICATION ===")
df_verify = pd.read_sql("""
    SELECT size_category, COUNT(*) as count 
    FROM institutions 
    GROUP BY size_category 
    ORDER BY count DESC
""", conn)
print(df_verify.to_string())

# Greek banks
print("\n=== GREEK BANKS ===")
df_gr = pd.read_sql("""
    SELECT commercial_name, size_category, total_assets, business_model
    FROM institutions
    WHERE country_iso = 'GR'
    ORDER BY total_assets DESC
""", conn)
print(df_gr.to_string())

conn.close()
print("\n\nDone!")
