"""
Check bank_models and institutions tables for size merge
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from eba_benchmarking.config import DB_NAME
import sqlite3
import pandas as pd

conn = sqlite3.connect(DB_NAME)

print("=== INSTITUTIONS TABLE SCHEMA ===")
cur = conn.cursor()
cur.execute("PRAGMA table_info(institutions)")
for col in cur.fetchall():
    print(f"  {col[1]}: {col[2]}")

print("\n=== BANK_MODELS TABLE SCHEMA ===")
cur.execute("PRAGMA table_info(bank_models)")
for col in cur.fetchall():
    print(f"  {col[1]}: {col[2]}")

print("\n=== BANK_MODELS DATA SAMPLE ===")
df_bm = pd.read_sql("SELECT * FROM bank_models LIMIT 10", conn)
print(df_bm.to_string())

print("\n=== SIZE CATEGORIES DISTRIBUTION ===")
df_size = pd.read_sql("SELECT size_category, COUNT(*) as count FROM bank_models GROUP BY size_category", conn)
print(df_size)

print("\n=== GREEK BANKS IN BANK_MODELS ===")
df_gr = pd.read_sql("""
    SELECT bm.lei, i.commercial_name, bm.size_category, bm.total_assets, bm.business_model
    FROM bank_models bm
    JOIN institutions i ON bm.lei = i.lei
    WHERE i.country_iso = 'GR'
""", conn)
print(df_gr.to_string())

print("\n=== INSTITUTIONS WITHOUT SIZE CLASSIFICATION ===")
df_missing = pd.read_sql("""
    SELECT i.lei, i.commercial_name, i.country_iso
    FROM institutions i
    LEFT JOIN bank_models bm ON i.lei = bm.lei
    WHERE bm.lei IS NULL
    LIMIT 20
""", conn)
print(f"Count: {len(df_missing)}")
print(df_missing.to_string())

conn.close()
print("\n\nDone!")
