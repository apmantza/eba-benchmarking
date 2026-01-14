import sqlite3
import pandas as pd

DB_PATH = 'eba_data.db'

def inspect_categories():
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT template_code, category, COUNT(*) as count 
    FROM pillar3_dictionary 
    GROUP BY template_code, category
    ORDER BY category, template_code
    """
    
    df = pd.read_sql(query, conn)
    
    with open('current_categories.txt', 'w', encoding='utf-8') as f:
        f.write(df.to_string())
        
    print("Done. See current_categories.txt")
    conn.close()

if __name__ == "__main__":
    inspect_categories()
