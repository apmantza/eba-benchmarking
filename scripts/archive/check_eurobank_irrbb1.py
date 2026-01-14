import sqlite3
import pandas as pd

DB_PATH = 'eba_data.db'

def check_eurobank_irrbb1():
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT * 
    FROM facts_pillar3 
    WHERE template_code='IRRBB1' AND bank_name='Eurobank'
    """
    
    df = pd.read_sql(query, conn)
    
    if df.empty:
        print("No IRRBB1 data found for Eurobank.")
    else:
        print("Eurobank IRRBB1 Data:")
        print(df.to_string())
    
    conn.close()

if __name__ == "__main__":
    check_eurobank_irrbb1()
