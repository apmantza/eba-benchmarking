import requests
import pandas as pd
import sqlite3
import io
import time
from eba_benchmarking.config import DB_NAME

# --- CONFIGURATION ---
API_BASE = "https://data-api.ecb.europa.eu/service/data"

def get_start_date():
    """Finds the earliest date in our DB to align timelines."""
    conn = sqlite3.connect(DB_NAME)
    try:
        val = pd.read_sql("SELECT MIN(date) FROM market_data", conn).iloc[0,0]
        if not val: val = '2019-01-01'
    except:
        val = '2019-01-01'
    conn.close()
    return val

def fetch_and_normalize(dataset, key, label, freq_hint='Q'):
    """
    Fetches data from ECB and upsamples (Forward Fill) to Monthly.
    """
    url = f"{API_BASE}/{dataset}/{key}?startPeriod=2015-01-01&format=csvdata"
    
    print(f"  > {label}...", end=" ", flush=True)
    
    for i in range(2):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                df = pd.read_csv(io.StringIO(resp.text))
                
                # 1. Parse Date
                # ECB Quarterly data comes as "2023-Q1". pandas handles this well.
                df['date'] = pd.PeriodIndex(df['TIME_PERIOD'], freq=freq_hint).to_timestamp()
                
                # 2. Filter Start Date
                start_dt = pd.to_datetime(get_start_date())
                df = df[df['date'] >= start_dt].copy()
                
                # 3. UPSAMPLE: Quarterly -> Monthly (Forward Fill)
                # We set the index and resample to Month End ('ME')
                df = df.set_index('date').sort_index()
                
                # 'ME' for Month End. We ffill() to keep the index value constant for the 3 months
                df_monthly = df.resample('ME')['OBS_VALUE'].ffill().reset_index()
                
                # 4. Format
                df_monthly['date'] = df_monthly['date'].dt.strftime('%Y-%m-%d')
                df_monthly['metric'] = label
                df_monthly['category'] = 'Real Estate Indices'
                
                print(f"✅ (Fetched {len(df)} {freq_hint} -> Expanded to {len(df_monthly)} Monthly)")
                return df_monthly[['date', 'category', 'metric', 'OBS_VALUE']]
                
            elif resp.status_code == 404:
                print("❌ (404 Not Found)")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)
            
    return None

def main():
    print("--- Fetching Real Estate Indices (Source: ECB/BoG) ---")
    all_data = []

    # --- 1. RESIDENTIAL PRICES (BoG Dataset 5) ---
    # Dataset: RESR (Residential Real Estate Prices)
    # Key: Q.GR.N.RTF.TVAL.GR2.TB.N.IX
    # Q=Quarterly, GR=Greece, N=National, RTF=Flats(Apartments), TVAL=TransActionValue, IX=Index
    keys_res = [
        ("RESR", "Q.GR._T.N.RTF.TVAL.GR2.TB.N.IX", "Prop. Prices: National (Apartments)"),
        ("RESR", "Q.GR.AT.N.RTF.TVAL.GR2.TB.N.IX", "Prop. Prices: Athens (Apartments)"),
        ("RESR", "Q.GR.TE.N.RTF.TVAL.GR2.TB.N.IX", "Prop. Prices: Thessaloniki (Apartments)")
    ]

    # --- 2. COMMERCIAL PRICES (BoG Dataset 8) ---
    # Dataset: CPP (Commercial Property Prices)
    # Note: These are often experimental/less frequent.
    keys_com = [
        ("CPP", "Q.GR._T.N.O.TVAL._T.TB.N.IX", "Prop. Prices: Offices (Commercial)"),
        ("CPP", "Q.GR._T.N.S.TVAL._T.TB.N.IX", "Prop. Prices: Retail (Commercial)")
    ]

    # EXECUTE
    for dataset, key, label in keys_res + keys_com:
        df = fetch_and_normalize(dataset, key, label, freq_hint='Q')
        if df is not None: 
            all_data.append(df)

    # --- SAVE TO DB ---
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        # Rename OBS_VALUE to value for DB consistency
        full_df.rename(columns={'OBS_VALUE': 'value'}, inplace=True)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Use 'bog_macro' table (or 'market_data' if you prefer one table)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bog_macro (
                date TEXT,
                category TEXT,
                metric TEXT,
                value REAL,
                PRIMARY KEY (date, metric)
            )
        ''')
        
        print(f"\n💾 Saving {len(full_df)} records to 'bog_macro'...")
        records = full_df.values.tolist()
        cursor.executemany('INSERT OR REPLACE INTO bog_macro VALUES (?,?,?,?)', records)
        conn.commit()
        conn.close()
        print("Done.")
    else:
        print("No data fetched. Check internet connection or ECB availability.")

if __name__ == "__main__":
    main()