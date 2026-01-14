import requests
import pandas as pd
import sqlite3
import io
import time
from eba_benchmarking.config import DB_NAME

# --- CONFIGURATION ---
BASE_URL = "https://data-api.ecb.europa.eu/service/data/MIR"

def get_countries():
    # Target Eurozone
    return ['AT','BE','CY','DE','EE','ES','FI','FR','GR','IE','IT','LT','LU','LV','MT','NL','PT','SI','SK']

def fetch_with_fallback(iso, key_template):
    """
    Tries 'N' (New Business standard) then 'P' (Pure New Loans).
    """
    # 1. Try N (Standard)
    url_n = f"{BASE_URL}/{key_template.format(iso=iso, coverage='N')}?startPeriod=2020-01-01&format=csvdata"
    try:
        resp = requests.get(url_n, timeout=5)
        if resp.status_code == 200:
            return pd.read_csv(io.StringIO(resp.text))
    except:
        pass

    # 2. Try P (Pure - for GR/IE)
    url_p = f"{BASE_URL}/{key_template.format(iso=iso, coverage='P')}?startPeriod=2020-01-01&format=csvdata"
    try:
        resp = requests.get(url_p, timeout=5)
        if resp.status_code == 200:
            return pd.read_csv(io.StringIO(resp.text))
    except:
        pass
        
    return None

def fetch_data_iterative(countries):
    results = []
    print(f"--- Starting Golden Key Fetch (Corrected Dimensions) ---")
    
    for iso in countries:
        print(f"Processing {iso}...", end=" ", flush=True)
        found_cnt = 0
        
        # --- THE CORRECTED KEYS ---
        # Structure: M.{iso}.B.{Instrument}.{Maturity}.{RateType}.{AmountCat}.{Sector}.EUR.{Coverage}
        
        # 1. SME Loans (Up to 1M)
        # Instrument: A2A (Loans other than revolving)
        # AmountCat: 0 (Up to 1M)
        # Sector: 2240 (NFC)
        k_sme = "M.{iso}.B.A2A.F.R.0.2240.EUR.{coverage}"
        
        # 2. Large Corp (Over 1M)
        # AmountCat: 1 (Over 1M)
        # Sector: 2240 (NFC)
        k_large = "M.{iso}.B.A2A.F.R.1.2240.EUR.{coverage}"

        # 3. Consumer Credit
        # Instrument: A2B (Consumption)
        # AmountCat: A (All)
        # Sector: 2250 (Households)
        k_cons = "M.{iso}.B.A2B.F.R.A.2250.EUR.{coverage}"
        
        # 4. Mortgages - Variable
        # Instrument: A2C (House Purchase)
        k_mort_float = "M.{iso}.B.A2C.F.R.A.2250.EUR.{coverage}"

        # 5. Mortgages - Fixed 1-5Y
        # Maturity: I (1-5Y)
        k_mort_fixed = "M.{iso}.B.A2C.I.R.A.2250.EUR.{coverage}"
        
        queries = [
            ("Corporate Rate (SME)", k_sme),
            ("Corporate Rate (Large)", k_large),
            ("Consumer Credit Rate", k_cons),
            ("Mortgage Rate (Variable)", k_mort_float),
            ("Mortgage Rate (Fixed 1-5Y)", k_mort_fixed)
        ]
        
        for label, template in queries:
            df = fetch_with_fallback(iso, template)
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    results.append((
                        row['TIME_PERIOD'], 
                        'Lending Rates', 
                        label, 
                        iso, 
                        row['OBS_VALUE']
                    ))
                found_cnt += 1
        
        if found_cnt == 5:
            print(f"✅ (5/5)")
        elif found_cnt > 0:
            print(f"⚠️ ({found_cnt}/5)")
        else:
            print(f"❌")
            
    return results

def save_to_db(data):
    if not data:
        print("No data fetched.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Ensure Schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS market_data (
        lei TEXT,
        bank_name TEXT,
        ticker TEXT,
        collection_date TEXT,
        market_cap REAL,
        stock_price REAL,
        currency TEXT,
        date TEXT,
        category TEXT,
        metric TEXT,
        value REAL,
        region TEXT,
        PRIMARY KEY (date, metric, region)
    )
    ''')
    
    print(f"Saving {len(data)} records...")
    cursor.executemany(
        'INSERT OR REPLACE INTO market_data (date, category, metric, region, value) VALUES (?,?,?,?,?)', 
        data
    )
    conn.commit()
    conn.close()
    print("Done.")

def main():

    country_list = get_countries()

    data = fetch_data_iterative(country_list)

    save_to_db(data)



if __name__ == "__main__":

    main()
