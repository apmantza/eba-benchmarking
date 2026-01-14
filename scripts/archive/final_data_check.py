import sqlite3
import pandas as pd

def check_final():
    conn = sqlite3.connect('eba_data.db')
    query = """
    SELECT bank_name, row_id, amount 
    FROM facts_pillar3 
    WHERE template_code = 'KM1' 
    AND row_id IN ('1', '5', '12', '14', '15', '20')
    AND bank_name IN ('Alpha Bank', 'Eurobank')
    ORDER BY bank_name, CAST(row_id AS INTEGER)
    """
    df = pd.read_sql_query(query, conn)
    print(df)
    conn.close()

if __name__ == "__main__":
    check_final()
