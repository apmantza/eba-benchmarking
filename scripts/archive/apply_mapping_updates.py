import sqlite3
import pandas as pd
from parse_pillar3_batch import TEMPLATE_ROWS

DB_PATH = 'eba_data.db'

def apply_updates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Updating EBA Item IDs in existing Pillar 3 records...")
    updated_count = 0
    
    for template, rows in TEMPLATE_ROWS.items():
        for row_id, (label, eba_id) in rows.items():
            if eba_id:
                # Update records that match template and row_id
                cursor.execute("""
                    UPDATE facts_pillar3 
                    SET eba_item_id = ? 
                    WHERE template_code = ? AND row_id = ? AND (eba_item_id IS NULL OR eba_item_id != ?)
                """, (eba_id, template, row_id, eba_id))
                
                if cursor.rowcount > 0:
                    updated_count += cursor.rowcount
                    # print(f"Updated {cursor.rowcount} records for {template} Row {row_id} -> {eba_id}")
    
    conn.commit()
    conn.close()
    print(f"Total records updated: {updated_count}")

if __name__ == "__main__":
    apply_updates()
