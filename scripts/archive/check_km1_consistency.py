import sqlite3
import pandas as pd

def check_values():
    conn = sqlite3.connect('eba_data.db')
    query = """
    SELECT bank_name, period, template_code, row_id, row_label, amount 
    FROM facts_pillar3 
    WHERE row_id IN ('1', '4') AND template_code = 'KM1'
    AND period LIKE '2025%'
    ORDER BY bank_name, period, row_id
    """
    df = pd.read_sql_query(query, conn)
    print(df)
    conn.close()

if __name__ == "__main__":
    check_values()
