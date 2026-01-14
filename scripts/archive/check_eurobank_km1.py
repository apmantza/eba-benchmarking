import sqlite3
import pandas as pd

def check_eurobank_km1():
    conn = sqlite3.connect('eba_data.db')
    query = """
    SELECT row_id, amount, row_label 
    FROM facts_pillar3 
    WHERE bank_name = 'Eurobank' AND template_code = 'KM1'
    AND row_id IN ('11a','14','14a','14b','14c','14d','14e','16','17','18','19','20','21')
    ORDER BY CAST(row_id AS INTEGER), row_id
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string())
    conn.close()

if __name__ == "__main__":
    check_eurobank_km1()
