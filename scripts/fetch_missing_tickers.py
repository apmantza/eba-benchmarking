
import os
import sys
import pandas as pd
import sqlite3
import requests
import time
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from eba_benchmarking.config import DB_NAME, ROOT_DIR

DATA_DIR = os.path.join(ROOT_DIR, 'data', 'raw')
OUTPUT_FILE = os.path.join(DATA_DIR, 'generated_tickers.csv')

def search_yahoo(query):
    """
    Search Yahoo Finance for a ticker symbol using the query API.
    """
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {
        'q': query,
        'quotesCount': 5,
        'newsCount': 0,
        'enableFuzzyQuery': 'true',
        'quotesQueryId': 'tss_match_phrase_query'
    }
    # User-Agent is required to avoid 403 Forbidden
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'quotes' in data and data['quotes']:
                # Filter for Equity or ETF
                candidates = [
                    q for q in data['quotes'] 
                    if q.get('quoteType') in ['EQUITY', 'ETF'] and q.get('isYahooFinance', True)
                ]
                
                if candidates:
                    # Return the first (most relevant) symbol
                    return candidates[0]['symbol']
        return None
    except Exception as e:
        safe_q = query.encode('ascii', 'replace').decode('ascii')
        print(f"  Error searching for '{safe_q}': {e}")
        return None

def main():
    print("--- Yahoo Finance Ticker Discovery ---")
    
    if not os.path.exists(DB_NAME):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    
    # Get all institutions
    # We prioritize finding tickers for those that don't have one
    query = "SELECT lei, name, commercial_name, country_iso, ticker FROM institutions"
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"Total Institutions: {len(df)}")
    
    # Check if we already have a generated file to resume/merge
    if os.path.exists(OUTPUT_FILE):
        print(f"Loading existing mapping from {OUTPUT_FILE}...")
        df_existing = pd.read_csv(OUTPUT_FILE)
        # Merge to avoid re-searching
        df = pd.merge(df, df_existing[['lei', 'ticker']], on='lei', how='left', suffixes=('', '_new'))
        # If ticker was null in DB but found in file, use file
        df['ticker'] = df['ticker'].fillna(df['ticker_new'])
        df.drop(columns=['ticker_new'], inplace=True)
    
    missing = df[df['ticker'].isna()]
    print(f"Institutions without tickers: {len(missing)}")
    
    if missing.empty:
        print("All institutions have tickers (or are ignored).")
        return

    new_tickers = []
    
    print("\nStarting search (this may take a while)...")
    
    for idx, row in missing.iterrows():
        lei = row['lei']
        name = row['commercial_name'] if pd.notna(row['commercial_name']) else row['name']
        country = row['country_iso']
        
        if pd.isna(name):
            print(f"[SKIP] LEI {lei} has no name")
            continue
            
        # Cleanup name for better search results
        # Remove common legal suffixes
        clean_name = str(name)
        for suffix in ['S.A.', 'AG', 'p.l.c.', 'plc', 'NV', 'S.p.A.', 'SE', 'Group', 'Corporation', 'Bancorp', 'Oyj', 'Ltd', 'Limited']:
            clean_name = clean_name.replace(suffix, '').replace(suffix.lower(), '')
        
        clean_name = clean_name.strip().strip(',').strip()
        
        # Search Query: Name
        ticker = search_yahoo(clean_name)
        
        # Fallback: Name + Country (helps with generic names like "National Bank")
        if not ticker and country:
             ticker = search_yahoo(f"{clean_name} {country}")
             
        safe_name = name.encode('ascii', 'replace').decode('ascii')
        if ticker:
            print(f"[FOUND] {safe_name[:30]:<30} -> {ticker}")
            new_tickers.append({'lei': lei, 'ticker': ticker, 'name': name})
        else:
            print(f"[MISSING] {safe_name[:30]:<30}")
            
        # Be polite to the API
        time.sleep(0.3)
        
    if new_tickers:
        print(f"\nDiscovered {len(new_tickers)} new tickers.")
        
        # Save to CSV
        df_new = pd.DataFrame(new_tickers)
        
        # Merge with existing file if any
        if os.path.exists(OUTPUT_FILE):
            df_old = pd.read_csv(OUTPUT_FILE)
            # Concat and dedup based on LEI, keeping new
            df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=['lei'], keep='last')
        else:
            df_final = df_new
            
        df_final.to_csv(OUTPUT_FILE, index=False)
        print(f"Saved mappings to {OUTPUT_FILE}")
        
        # Also update the database immediately for this session
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        print("Updating database text...")
        updates = [(r['ticker'], r['lei']) for r in new_tickers]
        cursor.executemany("UPDATE institutions SET ticker = ? WHERE lei = ?", updates)
        conn.commit()
        conn.close()
        print("Database updated.")
        
    else:
        print("No new tickers found.")

if __name__ == "__main__":
    main()
