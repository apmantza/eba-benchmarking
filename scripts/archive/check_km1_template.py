import sqlite3
import pandas as pd

def check_templates():
    conn = sqlite3.connect('eba_data.db')
    ids = ['5','12','14','15','16','17','18','19','20']
    df = pd.read_sql_query(f"SELECT row_id, row_label FROM pillar3_templates WHERE template_code='KM1' AND row_id IN ({','.join(['?' for _ in ids])})", conn, params=ids)
    print("Specific KM1 Template Rows:")
    print(df)
    conn.close()

if __name__ == "__main__":
    check_templates()
