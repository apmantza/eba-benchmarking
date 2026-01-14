import sqlite3
import pandas as pd
from eba_benchmarking.config import DB_NAME
from eba_benchmarking.utils import normalize_period

def cleanup_table(conn, table_name, date_col):
    print(f"Cleaning table: {table_name}...")
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        if df.empty:
            print(f"  - Table {table_name} is empty.")
            return
        
        orig_count = len(df)
        df[date_col] = df[date_col].apply(normalize_period)
        
        # Deduplicate after normalization (important if we collapsed periods)
        # We find identifying columns (all except value?)
        identifying_cols = [c for c in df.columns if c != 'value']
        df = df.drop_duplicates(subset=identifying_cols)
        
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"  - Success. {orig_count} -> {len(df)} records.")
    except Exception as e:
        print(f"  - Error cleaning {table_name}: {e}")

def main():
    conn = sqlite3.connect(DB_NAME)
    
    # List of (table, date_column)
    tasks = [
        ('macro_economics', 'period'),
        ('bog_macro', 'date'),
        ('ecb_stats', 'period'),
        ('base_rates', 'date'),
        ('ecb_market_data', 'date'),
        ('market_data', 'fetch_date'),
        ('facts_oth', 'period'),
        ('facts_cre', 'period'),
        ('facts_mrk', 'period'),
        ('facts_sov', 'period')
    ]
    
    for table, col in tasks:
        cleanup_table(conn, table, col)
        
    conn.close()
    print("\nDatabase cleanup complete.")

if __name__ == "__main__":
    main()
