import sqlite3
import pandas as pd
import os
import sys

# Add src to sys.path
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from eba_benchmarking.config import ROOT_DIR, DB_NAME

def main():
    print("--- Synchronizing Bank Metadata CSV ---")
    
    csv_path = os.path.join(ROOT_DIR, 'europe_bank_tickers.csv')
    
    # 1. Load existing CSV
    if os.path.exists(csv_path):
        df_csv = pd.read_csv(csv_path)
        print(f"Loaded existing CSV with {len(df_csv)} entries.")
    else:
        df_csv = pd.DataFrame(columns=['NAME', 'yfinance ticker', 'bond ticker', 'trading', 'bank type', 'Majority owner'])
        print("Created new metadata structure.")

    # 2. Get all banks from DB
    if not os.path.exists(DB_NAME):
        print(f"Error: Database not found at {DB_NAME}")
        return

    conn = sqlite3.connect(DB_NAME)
    df_db = pd.read_sql("SELECT name FROM institutions", conn)
    conn.close()
    
    db_names = df_db['name'].unique()
    print(f"Found {len(db_names)} unique banks in Database.")

    # 3. Merge / Append missing banks
    # We use a set of lowercase names to check for existence
    existing_names_lower = set(df_csv['NAME'].str.lower().str.strip())
    
    new_rows = []
    for name in db_names:
        clean_name = str(name).strip()
        if clean_name.lower() not in existing_names_lower:
            new_rows.append({
                'NAME': clean_name,
                'yfinance ticker': None,
                'bond ticker': None,
                'trading': None,
                'bank type': None,
                'Majority owner': None
            })
    
    if new_rows:
        df_new = pd.DataFrame(new_rows)
        df_final = pd.concat([df_csv, df_new], ignore_index=True)
        print(f"Added {len(new_rows)} new banks to the list.")
    else:
        df_final = df_csv
        print("No new banks to add.")

    # 4. Sort and save
    df_final = df_final.sort_values('NAME')
    df_final.to_csv(csv_path, index=False)
    print(f"Successfully updated CSV at: {csv_path}")
    print(f"Total banks in CSV: {len(df_final)}")

if __name__ == "__main__":
    main()
