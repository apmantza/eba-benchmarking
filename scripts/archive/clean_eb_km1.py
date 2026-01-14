import sqlite3

DB_PATH = 'eba_data.db'
LEI = 'JEUVK5RWVJEN8W0C9M24' # Eurobank

def clean_stale_km1():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("Deleting stale KM1 data for Eurobank...")
    cur.execute("""
        DELETE FROM facts_pillar3 
        WHERE lei = ? AND template_code = 'KM1'
    """, (LEI,))
    
    print(f"Deleted {cur.rowcount} stale rows.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    clean_stale_km1()
