import sqlite3
import pandas as pd
import os

DB_PATH = 'eba_data.db'
OUTPUT_DIR = 'data/output'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'facts_pillar3.csv')

def export_csv():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    conn = sqlite3.connect(DB_PATH)
    
    query = "SELECT * FROM facts_pillar3"
    df = pd.read_sql(query, conn)
    
    print(f"Exporting {len(df)} records to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False)
    print("Export complete.")
    
    conn.close()

if __name__ == "__main__":
    export_csv()
