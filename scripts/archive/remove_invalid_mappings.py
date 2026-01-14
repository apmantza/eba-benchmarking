import sqlite3
import pandas as pd

DB_PATH = 'eba_data.db'

def clear_invalid_mappings():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Items to clear
    targets = [
        ('LIQ1', '21'),
        ('LIQ1', '22'),
        ('LIQ1', '23'),
        ('LIQ2', '27'),
        ('CC2', '2'),
        ('CC2', '3'),
        ('LIQ1', 'EU-19a'), 
        ('LIQ1', '1')       
    ]
    
    print("Clearing invalid mappings for:")
    for tpl, rid in targets:
        print(f"  - {tpl} Row {rid}")
        cur.execute("""
            UPDATE pillar3_dictionary 
            SET eba_item_id = NULL 
            WHERE template_code = ? AND row_id = ?
        """, (tpl, rid))
        
    conn.commit()
    print(f"Updates committed. Affected rows: {cur.rowcount} (Note: rowcount might be global or last stmt)")
    
    conn.close()

if __name__ == "__main__":
    clear_invalid_mappings()
