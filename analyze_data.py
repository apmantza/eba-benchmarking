
import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect('data/eba_data.db')
    
    # Check for latest period first
    query_period = "SELECT MAX(period) as max_period FROM facts_oth"
    cursor = conn.cursor()
    cursor.execute(query_period)
    max_period = cursor.fetchone()[0]
    print(f"Latest Period: {max_period}")

    query = f"""
    SELECT 
        d.category, 
        COUNT(*) as count, 
        SUM(f.amount) as total_amount 
    FROM facts_oth f 
    JOIN dictionary d ON f.item_id = d.item_id 
    WHERE f.period = '{max_period}'
    GROUP BY d.category 
    ORDER BY count DESC
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_markdown())
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
