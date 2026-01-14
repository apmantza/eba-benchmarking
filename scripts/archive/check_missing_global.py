import sqlite3
import pandas as pd

def check_missing_rows():
    conn = sqlite3.connect('eba_data.db')
    query = """
    SELECT bank_name, row_id, row_label, amount 
    FROM facts_pillar3 
    WHERE template_code = 'KM1' 
    AND row_id IN ('11a', '14', '14a', '14b', '14c', '14d', '14e', 'EU 16a', 'EU 16b', '16', '17')
    ORDER BY bank_name, CAST(row_id AS INTEGER), row_id
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string())
    conn.close()

if __name__ == "__main__":
    check_missing_rows()
