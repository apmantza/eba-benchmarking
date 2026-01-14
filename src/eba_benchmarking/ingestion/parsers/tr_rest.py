import pandas as pd
import sqlite3
import os
import glob
import re
from eba_benchmarking.config import ROOT_DIR, DB_NAME
from eba_benchmarking.utils import get_item_mapping

# --- CONFIGURATION ---
RAW_FOLDER = os.path.join(ROOT_DIR, 'data', 'raw')

def run_parser(conn, csv_path, table_name, specific_mappings, mapping=None):
    """
    Parses a CSV and inserts it into the specified DB table.
    """
    cursor = conn.cursor()
    print(f"--- Processing {os.path.basename(csv_path)} ---")
    
    # 1. Inspect Headers
    try:
        initial_df = pd.read_csv(csv_path, nrows=0)
        actual_cols = initial_df.columns.tolist()
    except Exception as e:
        print(f"  [ERROR] Could not read headers: {e}")
        return

    # 2. Build Column Map
    base_mappings = {
        'lei': ['LEI_code', 'LEI_Code', 'lei'],
        'period': ['Period', 'period'],
        'item_id': ['Item', 'item'],
        'amount': ['Amount', 'amount']
    }
    all_mappings = {**base_mappings, **specific_mappings}
    
    use_cols = []
    db_rename_map = {}
    
    for db_col, candidates in all_mappings.items():
        for candidate in candidates:
            if candidate in actual_cols:
                use_cols.append(candidate)
                db_rename_map[candidate] = db_col
                break
    
    if 'lei' not in db_rename_map.values() or 'amount' not in db_rename_map.values() or 'item_id' not in db_rename_map.values():
         print(f"  [SKIP] Missing essential columns. Skipping file.")
         return

    # 3. Process Data
    chunk_size = 100000
    total_rows = 0
    
    try:
        for chunk in pd.read_csv(csv_path, usecols=use_cols, chunksize=chunk_size, dtype=str):
            chunk.rename(columns=db_rename_map, inplace=True)
            
            # Normalize Item ID
            if mapping:
                chunk['item_id'] = chunk['item_id'].map(mapping).fillna(chunk['item_id'])
                
            chunk['amount'] = pd.to_numeric(chunk['amount'], errors='coerce')
            
            int_dims = [col for col in db_rename_map.values() 
                        if col not in ['lei', 'period', 'item_id', 'amount', 'country']]
            
            for col in int_dims:
                chunk[col] = pd.to_numeric(chunk[col], errors='coerce').fillna(0).astype(int)

            chunk.to_sql(table_name, conn, if_exists='append', index=False)
            total_rows += len(chunk)
            print(f"    - Imported {total_rows} rows...", end='\r')
            
        print(f"\n  ✅ Success! Imported {total_rows} records into '{table_name}'.")

    except Exception as e:
        print(f"\n  [ERROR] Processing failed: {e}")

def main():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Clear tables for fresh import (Idempotency)
    print("--- [MRK/SOV] Clearing tables for fresh import ---")
    cursor.execute('DROP TABLE IF EXISTS facts_mrk')
    cursor.execute('DROP TABLE IF EXISTS facts_sov')

    # Schemas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS facts_mrk (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lei TEXT,
        period INTEGER,
        item_id TEXT,
        portfolio INTEGER,
        mkt_modprod INTEGER,
        mkt_risk INTEGER,
        amount REAL,
        FOREIGN KEY(lei) REFERENCES institutions(lei),
        FOREIGN KEY(item_id) REFERENCES dictionary(item_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS facts_sov (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lei TEXT,
        period INTEGER,
        item_id TEXT,
        country TEXT,
        maturity INTEGER,
        accounting_portfolio INTEGER,
        amount REAL,
        FOREIGN KEY(lei) REFERENCES institutions(lei),
        FOREIGN KEY(item_id) REFERENCES dictionary(item_id)
    )
    ''')
    conn.commit()

    # --- 1. Process MRK files ---
    mrk_files = glob.glob(os.path.join(RAW_FOLDER, 'tr_mrk*.csv'))
    mrk_map = {
        'portfolio': ['Portfolio', 'portfolio'],
        'mkt_modprod': ['MKT_Modprod', 'MKT_modprod', 'mkt_modprod'],
        'mkt_risk': ['Mkt_risk', 'Mkt_Risk', 'mkt_risk']
    }
    for f in mrk_files:
        year_match = re.search(r'20\d{2}', os.path.basename(f))
        exercise_year = year_match.group(0) if year_match else '2025'
        mapping = get_item_mapping(conn, exercise_year)
        run_parser(conn, f, 'facts_mrk', mrk_map, mapping)

    # --- 2. Process SOV files ---
    sov_files = glob.glob(os.path.join(RAW_FOLDER, 'tr_sov*.csv'))
    sov_map = {
        'country': ['Country', 'country', 'Ctry'],
        'maturity': ['Maturity', 'maturity'],
        'accounting_portfolio': ['Accounting_portfolio', 'Acc_Portfolio', 'accounting_portfolio']
    }
    for f in sov_files:
        year_match = re.search(r'20\d{2}', os.path.basename(f))
        exercise_year = year_match.group(0) if year_match else '2025'
        mapping = get_item_mapping(conn, exercise_year)
        run_parser(conn, f, 'facts_sov', sov_map, mapping)

    # Indexes
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_facts_mrk_lei ON facts_mrk(lei)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_facts_sov_lei ON facts_sov(lei)")
    conn.commit()
    conn.close()
    print("\nBatch job complete.")

if __name__ == '__main__':
    main()