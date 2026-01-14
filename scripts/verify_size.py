"""
Verify the merge worked
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from eba_benchmarking.config import DB_NAME
import sqlite3
import pandas as pd

conn = sqlite3.connect(DB_NAME)

print("=== SIZE DISTRIBUTION IN INSTITUTIONS ===")
df_size = pd.read_sql("""
    SELECT size_category, COUNT(*) as count 
    FROM institutions 
    GROUP BY size_category 
    ORDER BY count DESC
""", conn)
print(df_size.to_string())

print("\n=== GREEK BANKS WITH SIZE ===")
df_gr = pd.read_sql("""
    SELECT commercial_name, size_category, total_assets, business_model, Systemic_Importance
    FROM institutions
    WHERE country_iso = 'GR'
    ORDER BY total_assets DESC
""", conn)
print(df_gr.to_string())

print("\n=== SAMPLE OF ALL BANKS ===")
df_all = pd.read_sql("""
    SELECT commercial_name, country_iso, region, size_category, Systemic_Importance
    FROM institutions
    WHERE size_category IS NOT NULL
    ORDER BY size_category, commercial_name
    LIMIT 20
""", conn)
print(df_all.to_string())

conn.close()
print("\n\nDone!")
