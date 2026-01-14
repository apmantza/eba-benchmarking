import sqlite3
import pandas as pd

def check_alpha_liquidity():
    conn = sqlite3.connect('eba_data.db')
    query = """
    SELECT row_id, amount, row_label 
    FROM facts_pillar3 
    WHERE bank_name = 'Alpha Bank' AND template_code = 'KM1'
    AND row_id IN ('15','16','17','18','19','20','21')
    ORDER BY CAST(row_id AS INTEGER), row_id
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string())
    conn.close()

if __name__ == "__main__":
    check_alpha_liquidity()
