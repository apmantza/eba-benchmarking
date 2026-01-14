import sqlite3
import pandas as pd

def check_irrbb1_problem_banks():
    conn = sqlite3.connect('eba_data.db')
    query = """
    SELECT bank_name, row_id, dimension_name, amount
    FROM facts_pillar3
    WHERE template_code = 'IRRBB1' AND bank_name IN ('NBG', 'Eurobank')
    ORDER BY bank_name, cast(row_id as int), dimension_name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(df.to_string())

if __name__ == "__main__":
    check_irrbb1_problem_banks()
