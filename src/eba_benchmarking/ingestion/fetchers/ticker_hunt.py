import sqlite3
import pandas as pd
import yfinance as yf
import time
import os
from eba_benchmarking.config import ROOT_DIR, DB_NAME

def main():
    conn = sqlite3.connect(DB_NAME)
    # Get banks that have a commercial name but no ticker yet
    df = pd.read_sql("SELECT lei, commercial_name, country_name FROM institutions WHERE ticker IS NULL", conn)
    conn.close()

    print(f"Searching tickers for {len(df)} banks...")

    results = []

    for idx, row in df.iterrows():
        name = row['commercial_name']
        country = row['country_name']
        lei = row['lei']
        
        # Search Query: "Bank Name stock" or "Bank Name Country"
        query = f"{name} {country} stock"
        
        try:
            # Use Yahoo Finance Ticker Search (Requires internet)
            # Note: yfinance doesn't have a direct "search" function, 
            # so usually we rely on a manual map or an external search API.
            # However, for this script, we create a CSV for you to fill.
            
            # Heuristic: Guess the suffix based on country
            suffix_map = {
                'Greece': '.AT', 'Germany': '.DE', 'France': '.PA', 
                'Italy': '.MI', 'Spain': '.MC', 'Netherlands': '.AS'
            }
            suffix = suffix_map.get(country, '')
            
            results.append({
                'lei': lei,
                'name': name,
                'country': country,
                'suggested_ticker': f"{name.upper().replace(' ', '')}{suffix} (Verify Me!)"
            })
            
        except Exception as e:
            print(f"Error for {name}: {e}")

    # Save to CSV for Manual Verification
    df_res = pd.DataFrame(results)
    output_path = os.path.join(ROOT_DIR, 'suggested_tickers.csv')
    df_res.to_csv(output_path, index=False)
    print(f"\nDone! Open '{output_path}', fix the tickers, and then upload it.")

if __name__ == '__main__':
    main()