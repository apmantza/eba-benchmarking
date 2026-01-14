import sqlite3
import pandas as pd

def check_alpha():
    conn = sqlite3.connect('eba_data.db')
    query = """
    SELECT f.row_id, f.row_label, d.category, f.amount, f.source_page 
    FROM facts_pillar3 f
    LEFT JOIN pillar3_dictionary d ON f.template_code = d.template_code AND f.row_id = d.row_id
    WHERE f.bank_name = 'Alpha Bank' AND f.template_code = 'KM1'
    ORDER BY CAST(f.row_id AS INTEGER), f.row_id
    """
    df = pd.read_sql_query(query, conn)
    print("Alpha Bank KM1 Results:")
    print(df.to_string())
    
    query2 = """
    SELECT f.row_id, f.row_label, d.category, f.amount, f.source_page 
    FROM facts_pillar3 f
    LEFT JOIN pillar3_dictionary d ON f.template_code = d.template_code AND f.row_id = d.row_id
    WHERE f.bank_name = 'Eurobank' AND f.template_code = 'KM1'
    ORDER BY CAST(f.row_id AS INTEGER), f.row_id
    """
    df2 = pd.read_sql_query(query2, conn)
    print("\nEurobank KM1 Results:")
    print(df2.to_string())
    
    conn.close()

if __name__ == "__main__":
    check_alpha()
