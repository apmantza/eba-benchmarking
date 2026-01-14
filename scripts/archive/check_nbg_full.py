import sqlite3
import pandas as pd

def check_nbg_full():
    conn = sqlite3.connect('eba_data.db')
    query = """
    SELECT row_id, row_label, amount, source_page 
    FROM facts_pillar3 
    WHERE bank_name = 'NBG' AND template_code = 'KM1'
    ORDER BY CAST(row_id AS INTEGER), row_id
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string())
    conn.close()

if __name__ == "__main__":
    check_nbg_full()
