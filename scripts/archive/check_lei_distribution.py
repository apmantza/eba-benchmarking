import sqlite3
import pandas as pd

def check_db():
    conn = sqlite3.connect('eba_data.db')
    df = pd.read_sql_query("SELECT lei, bank_name, COUNT(*) as count FROM facts_pillar3 GROUP BY lei, bank_name", conn)
    print("LEI and Bank Name distribution:")
    print(df)
    
    missing = pd.read_sql_query("SELECT COUNT(*) as count FROM facts_pillar3 WHERE bank_name IS NULL OR bank_name = ''", conn)
    print(f"\nRows with missing bank_name: {missing['count'][0]}")
    
    conn.close()

if __name__ == "__main__":
    check_db()
