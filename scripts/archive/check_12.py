import sqlite3
import pandas as pd

def check_12():
    conn = sqlite3.connect('eba_data.db')
    query = "SELECT bank_name, row_id, amount FROM facts_pillar3 WHERE template_code='KM1' AND row_id='12'"
    df = pd.read_sql_query(query, conn)
    print(df)
    conn.close()

if __name__ == "__main__":
    check_12()
