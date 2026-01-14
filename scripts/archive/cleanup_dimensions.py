import sqlite3

DB_PATH = 'eba_data.db'

def cleanup_dimensions():
    conn = sqlite3.connect(DB_PATH)
    print("Updating NULL dimension_name to 'Default'...")
    cur = conn.execute("UPDATE facts_pillar3 SET dimension_name = 'Default' WHERE dimension_name IS NULL")
    print(f"Updated {cur.rowcount} rows.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    cleanup_dimensions()
