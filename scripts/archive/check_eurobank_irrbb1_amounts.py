import sqlite3
import pandas as pd

DB_PATH = 'eba_data.db'

def check_amounts():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT row_id, row_label, amount FROM facts_pillar3 WHERE template_code='IRRBB1' AND bank_name='Eurobank'"
    df = pd.read_sql(query, conn)
    print(df.to_string())
    conn.close()

if __name__ == "__main__":
    check_amounts()
