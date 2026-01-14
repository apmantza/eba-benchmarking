import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = 'eba_data.db'
OUTPUT_DIR = 'data/output'

def export_mapping():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Load Pillar 3 Dictionary
    print("Loading Pillar 3 Dictionary...")
    p3_dict = pd.read_sql("""
        SELECT template_code, row_id, p3_label, eba_item_id, category
        FROM pillar3_dictionary
        ORDER BY template_code, CAST(row_id AS INTEGER)
    """, conn)
    
    # 2. Load EBA Dictionary
    print("Loading EBA Dictionary...")
    eba_dict = pd.read_sql("SELECT item_id, label as eba_label FROM dictionary", conn)
    
    # 3. Merge
    print("Merging data...")
    merged = pd.merge(
        p3_dict, 
        eba_dict, 
        left_on='eba_item_id', 
        right_on='item_id', 
        how='left'
    )
    
    # 4. Clean up columns
    final_df = merged[[
        'template_code',
        'row_id',
        'p3_label',
        'eba_item_id',
        'eba_label',
        'category'
    ]]
    
    # Fill N/As
    final_df['eba_item_id'] = final_df['eba_item_id'].fillna('-(Unmapped)-')
    final_df['eba_label'] = final_df['eba_label'].fillna('')
    
    # 5. Export
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/pillar3_eba_mapping_{timestamp}.csv"
    
    final_df.to_csv(filename, index=False)
    print(f"Exported mapping to {filename}")
    print(f"Total Rows: {len(final_df)}")
    print(f"Mapped Rows: {len(final_df[final_df['eba_item_id'] != '-(Unmapped)-'])}")
    
    conn.close()

if __name__ == "__main__":
    export_mapping()
