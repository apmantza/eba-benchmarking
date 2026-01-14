import pandas as pd
import sqlite3
import os
import glob
import re
from eba_benchmarking.config import DB_NAME, ROOT_DIR
from eba_benchmarking.utils import get_item_mapping

RAW_FOLDER = os.path.join(ROOT_DIR, 'data', 'raw')

class BaseParser:
    def __init__(self, table_name, file_pattern_prefix, col_mapping_rules, create_table_sql, index_sqls, dtype_conversions=None):
        """
        Args:
            table_name (str): Name of the target SQL table (e.g., 'facts_cre').
            file_pattern_prefix (str): Prefix of files to match (e.g., 'tr_cre').
            col_mapping_rules (dict): Dictionary mapping DB columns to list of possible CSV headers.
            create_table_sql (str): SQL statement to create the table.
            index_sqls (list): List of SQL statements to create indexes.
            dtype_conversions (dict, optional): Dictionary of column names to specific numeric conversions.
        """
        self.table_name = table_name
        self.file_pattern = os.path.join(RAW_FOLDER, f"{file_pattern_prefix}*.csv")
        self.col_mapping_rules = col_mapping_rules
        self.create_table_sql = create_table_sql
        self.index_sqls = index_sqls
        self.dtype_conversions = dtype_conversions or {}

    def run(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        print(f"--- [{self.table_name.upper()}] Clearing table for fresh import ---")
        cursor.execute(f'DROP TABLE IF EXISTS {self.table_name}')
        
        # Create Table
        cursor.execute(self.create_table_sql)
        conn.commit()

        files = glob.glob(self.file_pattern)
        if not files:
            print(f"⚠️ No files found matching {self.file_pattern}")
            conn.close()
            return

        for csv_path in files:
            self._process_file(conn, csv_path)

        # Create Indexes
        print(f"Refreshing indexes for {self.table_name}...")
        for idx_sql in self.index_sqls:
            cursor.execute(idx_sql)
        
        conn.commit()
        conn.close()

    def _process_file(self, conn, csv_path):
        file_name = os.path.basename(csv_path)
        print(f"\n--- [{self.table_name.upper()}] Processing {file_name} ---")

        # Determine Exercise Year
        year_match = re.search(r'20\d{2}', file_name)
        exercise_year = year_match.group(0) if year_match else '2025'
        mapping = get_item_mapping(conn, exercise_year)
        
        if mapping:
            print(f"  > Using item mappings for TR{exercise_year} ({len(mapping)} items mapped)")

        # Intelligent Header Mapping
        try:
            # Read header only
            initial_df = pd.read_csv(csv_path, nrows=0)
            actual_cols = initial_df.columns.tolist()
        except Exception as e:
            print(f"❌ Error reading headers: {e}")
            return

        use_cols = []
        db_rename_map = {}

        for db_col, candidates in self.col_mapping_rules.items():
            for candidate in candidates:
                if candidate in actual_cols:
                    use_cols.append(candidate)
                    db_rename_map[candidate] = db_col
                    break
        
        # Validation
        required = ['lei', 'amount', 'item_id']
        missing = [req for req in required if req not in db_rename_map.values()]
        if missing:
            print(f"❌ Critical columns missing in {csv_path}: {missing}. Skipping.")
            return

        # Chunk Processing
        chunk_size = 100000
        total_rows = 0

        try:
            for chunk in pd.read_csv(csv_path, usecols=use_cols, chunksize=chunk_size, dtype=str):
                chunk.rename(columns=db_rename_map, inplace=True)

                # Normalize Item ID
                if mapping:
                    chunk['item_id'] = chunk['item_id'].map(mapping).fillna(chunk['item_id'])

                # Numeric Conversions
                chunk['amount'] = pd.to_numeric(chunk['amount'], errors='coerce')
                
                # Apply specific integer conversions (handling NaNs as 0)
                if self.dtype_conversions:
                    for col in self.dtype_conversions.get('int', []):
                        if col in chunk.columns:
                            chunk[col] = pd.to_numeric(chunk[col], errors='coerce').fillna(0).astype(int)
                        else:
                            chunk[col] = 0 # Default if missing
                
                chunk.to_sql(self.table_name, conn, if_exists='append', index=False)
                total_rows += len(chunk)
                print(f"  - Imported {total_rows} rows...", end='\r')
            
            print(f"\n✅ Success! Imported {total_rows} records.")
            
        except Exception as e:
            print(f"\n❌ Error processing file: {e}")
