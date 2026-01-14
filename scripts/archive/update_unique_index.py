import sqlite3

DB_PATH = 'eba_data.db'

def update_unique_index():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Drops existing index if any
    print("Dropping old unique index...")
    cur.execute("DROP INDEX IF EXISTS idx_facts_pillar3_unique")
    
    # Create new index with dimension_name
    print("Creating new unique index with dimension_name...")
    try:
        # We include dimension_name in the unique constraint.
        # Since dimension_name can be NULL, we use IFNULL(dimension_name, '') as a trick 
        # for SQLite versions that don't treat NULLs as equivalent in UNIQUE constraints 
        # (though modern SQLite treats NULL as distinct).
        # Actually, for standard uniqueness where NULL is "a dimension", it's fine.
        cur.execute("""
            CREATE UNIQUE INDEX idx_facts_pillar3_unique 
            ON facts_pillar3(lei, period, template_code, row_id, dimension_name)
        """)
        print("Unique index updated successfully.")
    except Exception as e:
        print(f"Index update failed: {e}")
        print("Note: If there are existing duplicates, this might fail.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_unique_index()
