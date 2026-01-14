import sqlite3
import pandas as pd

def check_specific():
    conn = sqlite3.connect('eba_data.db')
    rids = ['1', '5', '12', '14', '15', '20']
    query = """
    SELECT bank_name, f.row_id, f.row_label, f.amount, f.source_page 
    FROM facts_pillar3 f
    WHERE f.bank_name IN ('Alpha Bank', 'Eurobank') AND f.template_code = 'KM1'
    AND f.row_id IN ({})
    ORDER BY bank_name, CAST(f.row_id AS INTEGER), f.row_id
    """.format(','.join(['?']*len(rids)))
    df = pd.read_sql_query(query, conn, params=rids)
    print(df.to_string())
    conn.close()

if __name__ == "__main__":
    check_specific()
