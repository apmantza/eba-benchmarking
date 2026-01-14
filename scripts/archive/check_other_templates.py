import sqlite3
import pandas as pd

def check_template(template_code):
    conn = sqlite3.connect('eba_data.db')
    query = f"""
    SELECT bank_name, period, template_code, row_id, amount, row_label, dimension_name
    FROM facts_pillar3
    WHERE template_code = '{template_code}'
    ORDER BY bank_name, period, row_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"\n--- {template_code} Data ---")
    if df.empty:
        print("No data found.")
    else:
        # Pivot to see rows per bank/period
        pivot = df.pivot_table(index=['bank_name', 'period'], columns='row_id', values='amount', aggfunc='count')
        print(f"Row Counts per Bank/Period:\n{pivot.to_string()}")
        
        # Show sample data
        print("\nSample Data:")
        print(df.head(20).to_string())

if __name__ == "__main__":
    check_template('KM2')
