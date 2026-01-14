import sqlite3
import pandas as pd

DB_PATH = 'eba_data.db'

def check_negatives():
    conn = sqlite3.connect(DB_PATH)
    
    # Check IRRBB1 for negative values
    query = "SELECT lei, period, template_code, row_label, amount FROM facts_pillar3 WHERE template_code='IRRBB1' AND amount < 0 LIMIT 20"
    df = pd.read_sql(query, conn)
    
    print("Negative IRRBB1 Values:")
    print(df.to_string())
    
    # Check if we have any negative values generally
    query_all = "SELECT count(*) as count FROM facts_pillar3 WHERE amount < 0"
    df_count = pd.read_sql(query_all, conn)
    print(f"\nTotal negative values in DB: {df_count.iloc[0]['count']}")
    
    conn.close()

if __name__ == "__main__":
    check_negatives()
