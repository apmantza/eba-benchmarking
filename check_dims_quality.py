import sqlite3
import pandas as pd

conn = sqlite3.connect('data/eba_data.db')

def check_join(fact_table, dim_table, join_col, label_col='label'):
    print(f"\nChecking JOIN {fact_table}.{join_col} -> {dim_table}.{join_col}...")
    try:
        # Check types
        f_type = pd.read_sql(f"SELECT typeof({join_col}) as t FROM {fact_table} LIMIT 1", conn).iloc[0]['t']
        d_type = pd.read_sql(f"SELECT typeof({join_col}) as t FROM {dim_table} LIMIT 1", conn).iloc[0]['t']
        print(f"Types: Fact={f_type}, Dim={d_type}")
        
        # Check match rate
        query = f"""
        SELECT 
            COUNT(*) as total,
            COUNT(d.{label_col}) as matched,
            (CAST(COUNT(d.{label_col}) AS FLOAT) / COUNT(*)) * 100 as pct_matched
        FROM {fact_table} f
        LEFT JOIN {dim_table} d ON f.{join_col} = d.{join_col}
        """
        res = pd.read_sql(query, conn)
        print(res)
        
        if res.iloc[0]['pct_matched'] < 100:
            print("Missed Examples:")
            missed = pd.read_sql(f"""
            SELECT DISTINCT f.{join_col} 
            FROM {fact_table} f 
            LEFT JOIN {dim_table} d ON f.{join_col} = d.{join_col} 
            WHERE d.{label_col} IS NULL LIMIT 5""", conn)
            print(missed)
            
    except Exception as e:
        print(f"Error: {e}")

# Market Risk Checks
check_join('facts_mrk', 'dim_portfolio', 'portfolio')
check_join('facts_mrk', 'dim_mkt_modprod', 'mkt_modprod')
check_join('facts_mrk', 'dim_mkt_risk', 'mkt_risk')

# Credit Risk Checks
check_join('facts_cre', 'dim_portfolio', 'portfolio')
check_join('facts_cre', 'dim_exposure', 'exposure')
check_join('facts_cre', 'dim_status', 'status')
check_join('facts_cre', 'dim_perf_status', 'perf_status')
check_join('facts_cre', 'dim_country', 'country')
check_join('facts_cre', 'dim_nace_codes', 'nace_codes')

conn.close()
