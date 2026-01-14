import sqlite3

DB_PATH = 'eba_data.db'

def fix_db_constraints_and_clean():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 1. Clean bad data for Eurobank IRRBB1
    print("Deleting Eurobank IRRBB1 data...")
    cur.execute("DELETE FROM facts_pillar3 WHERE lei='JEUVK5RWVJEN8W0C9M24' AND template_code='IRRBB1'")
    print(f"Deleted {cur.rowcount} rows.")
    
    # 2. Add Unique Index to support INSERT OR REPLACE
    print("Creating unique index...")
    try:
        # We need a unique constraint on (lei, period, template_code, row_id)
        # Note: row_id might be null in some schemas, but here we usually have it.
        # Adding 'source_file' might be too specific? 
        # Best key: lei, period, template_code, row_id
        
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_facts_pillar3_unique 
            ON facts_pillar3(lei, period, template_code, row_id)
        """)
        print("Unique index created/verified.")
    except Exception as e:
        print(f"Index creation failed (maybe duplicates exist?): {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_db_constraints_and_clean()
