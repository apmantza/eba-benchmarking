import sqlite3
import pandas as pd

def check_14_detail():
    conn = sqlite3.connect('eba_data.db')
    query = """
    SELECT bank_name, row_id, amount, row_label 
    FROM facts_pillar3 
    WHERE template_code = 'KM1' AND (row_id LIKE '14%' OR row_id LIKE 'EU 16%' OR row_id = '16' OR row_id = '17')
    ORDER BY bank_name, row_id
    """
    df = pd.read_sql_query(query, conn)
    with open('check_14_16_utf8.txt', 'w', encoding='utf-8') as f:
        f.write(df.to_string())
    conn.close()

if __name__ == "__main__":
    check_14_detail()
