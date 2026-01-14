import sqlite3
import pandas as pd

DB_PATH = 'eba_data.db'

def check_db():
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT template_code, row_id, p3_label, eba_item_id 
    FROM pillar3_dictionary 
    WHERE template_code IN ('LIQ1', 'LIQ2', 'CC2') 
    AND row_id IN ('21', '22', '23', '27', '2', '3')
    ORDER BY template_code, row_id
    """
    
    df = pd.read_sql(query, conn)
    
    with open('db_state_check.txt', 'w', encoding='utf-8') as f:
         f.write(df.to_string())
    print("Done. See db_state_check.txt")
    conn.close()

if __name__ == "__main__":
    check_db()
