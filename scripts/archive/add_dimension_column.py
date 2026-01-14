import sqlite3

DB_PATH = 'eba_data.db'

def add_dimension_column():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check if column exists
    cur.execute("PRAGMA table_info(facts_pillar3)")
    cols = [row[1] for row in cur.fetchall()]
    
    if 'dimension_name' not in cols:
        print("Adding 'dimension_name' column to facts_pillar3...")
        try:
            cur.execute("ALTER TABLE facts_pillar3 ADD COLUMN dimension_name TEXT DEFAULT NULL")
            print("Column added successfully.")
        except Exception as e:
            print(f"Error adding column: {e}")
    else:
        print("'dimension_name' column already exists.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_dimension_column()
