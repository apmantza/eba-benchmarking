import sqlite3
import sys
import os

# Ensure we can import from scripts
sys.path.append(os.getcwd())
from scripts.parse_pillar3_batch import TEMPLATE_ROWS

DB_PATH = 'eba_data.db'

def fix_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("Fixing usage of facts_pillar3 table...")
    cur.execute("DROP TABLE IF EXISTS facts_pillar3")
    cur.execute("""
        CREATE TABLE facts_pillar3 (
            lei TEXT,
            period TEXT,
            template_code TEXT,
            table_title TEXT,
            row_id TEXT,
            row_label TEXT,
            raw_label TEXT,
            amount REAL,
            is_new_metric INTEGER,
            source_page INTEGER,
            bank_name TEXT,
            dimension_name TEXT DEFAULT 'Default',
            PRIMARY KEY (lei, period, template_code, row_id, dimension_name)
        )
    """)
    
    print("Fixing usage of pillar3_templates table...")
    cur.execute("DROP TABLE IF EXISTS pillar3_templates")
    cur.execute("""
        CREATE TABLE pillar3_templates (
            template_code TEXT,
            row_id TEXT,
            row_label TEXT,
            is_ratio INTEGER,
            eba_metric_id TEXT,
            PRIMARY KEY (template_code, row_id)
        )
    """)
    
    count = 0
    for code, rows in TEMPLATE_ROWS.items():
        for rid, val in rows.items():
            # TEMPLATE_ROWS values are (label, eba_id)
            label = val[0]
            eba_id = val[1]
            # Simple heuristic for is_ratio
            is_ratio = 1 if ('%' in label or 'ratio' in label.lower()) else 0
            
            cur.execute("""
                INSERT OR REPLACE INTO pillar3_templates 
                (template_code, row_id, row_label, is_ratio, eba_metric_id)
                VALUES (?, ?, ?, ?, ?)
            """, (code, rid, label, is_ratio, eba_id))
            count += 1
            
    print(f"Populated {count} template row definitions.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_db()
