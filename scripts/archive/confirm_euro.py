import sqlite3
import pandas as pd

def check_euro():
    conn = sqlite3.connect('eba_data.db')
    query = """
    SELECT row_id, amount FROM facts_pillar3 
    WHERE bank_name = 'Eurobank' AND template_code = 'KM1' 
    AND row_id IN ('5', '14', '15', '20')
    """
    df = pd.read_sql_query(query, conn)
    print(df)
    conn.close()

if __name__ == "__main__":
    check_euro()
