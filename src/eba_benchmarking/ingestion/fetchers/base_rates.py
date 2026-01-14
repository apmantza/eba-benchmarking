import requests
import pandas as pd
import sqlite3
import io
import time
from eba_benchmarking.config import DB_NAME
from eba_benchmarking.utils import normalize_period

# --- CONFIGURATION ---
API_BASE = "https://data-api.ecb.europa.eu/service/data"

def fetch_and_resample(dataset, key, label, freq='D'):
    """
    Fetches Daily data and resamples to Monthly Average.
    """
    url = f"{API_BASE}/{dataset}/{key}?startPeriod=2020-01-01&format=csvdata"
    
    print(f"  > {label}...", end=" ", flush=True)
    
    for i in range(2):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                df = pd.read_csv(io.StringIO(resp.text))
                
                # Resample if Daily
                if freq == 'D':
                    df['date'] = pd.to_datetime(df['TIME_PERIOD'])
                    # 'ME' is Month End (pandas 2.0+), use 'M' for older versions
                    try:
                        df_monthly = df.resample('ME', on='date')['OBS_VALUE'].mean().reset_index()
                    except:
                         df_monthly = df.resample('M', on='date')['OBS_VALUE'].mean().reset_index()
                         
                    df_monthly['TIME_PERIOD'] = df_monthly['date'].dt.strftime('%Y-%m')
                    df_final = df_monthly
                else:
                    df_final = df
                
                df_final = df_final[['TIME_PERIOD', 'OBS_VALUE']].copy()
                df_final['metric'] = label
                print("✅")
                return df_final
                
            elif resp.status_code == 404:
                print(f"❌ (404 Not Found - Key: {key})")
                return None
        except Exception as e:
            time.sleep(1)
            
    print("❌ (Error)")
    return None

def main():
    print("--- Fetching ECB Base Rates (Final Fixed) ---")
    all_data = []

    # --- 1. POLICY RATES (Fetch Daily -> Resample Monthly) ---
    # Keys verified: FM.D.U2.EUR.4F.KR.MRR_FR.LEV (Daily)
    keys_policy = [
        ("FM", "D.U2.EUR.4F.KR.MRR_FR.LEV", "MRO Rate"),
        ("FM", "D.U2.EUR.4F.KR.DFR.LEV",    "Deposit Facility Rate"),
        ("FM", "D.U2.EUR.4F.KR.MLFR.LEV",   "Marginal Lending Facility")
    ]
    
    # --- 2. EURIBOR (Monthly Average) ---
    # UPDATED KEY: 12M is '1YD_' (1 Year), not '12MD_'
    keys_euribor = [
        ("FM", "M.U2.EUR.RT.MM.EURIBOR1MD_.HSTA", "Euribor 1M"),
        ("FM", "M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA", "Euribor 3M"),
        ("FM", "M.U2.EUR.RT.MM.EURIBOR6MD_.HSTA", "Euribor 6M"),
        ("FM", "M.U2.EUR.RT.MM.EURIBOR1YD_.HSTA", "Euribor 12M") # <--- FIXED KEY
    ]

    # --- 3. ESTR (Daily -> Resample Monthly) ---
    # Key: EST.B.EU000A2X2A25.WT
    keys_estr = [
        ("EST", "B.EU000A2X2A25.WT", "ESTR (Overnight)")
    ]

    # EXECUTE FETCH
    
    print("\n1. Policy Rates (Daily -> Monthly Avg):")
    for dataset, key, label in keys_policy:
        df = fetch_and_resample(dataset, key, label, freq='D')
        if df is not None: all_data.append(df)

    print("\n2. Market Rates (Daily -> Monthly Avg):")
    for dataset, key, label in keys_estr:
        df = fetch_and_resample(dataset, key, label, freq='D')
        if df is not None: all_data.append(df)

    print("\n3. Euribor (Monthly):")
    for dataset, key, label in keys_euribor:
        df = fetch_and_resample(dataset, key, label, freq='M')
        if df is not None: all_data.append(df)

    # --- SAVE ---
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        full_df.rename(columns={'TIME_PERIOD': 'date', 'OBS_VALUE': 'value'}, inplace=True)
        full_df['date'] = full_df['date'].apply(normalize_period)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Ensure Schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS base_rates (
                date TEXT,
                metric TEXT,
                value REAL,
                PRIMARY KEY (date, metric)
            )
        ''')
        
        print(f"\nSaving {len(full_df)} records...")
        records = full_df[['date', 'metric', 'value']].values.tolist()
        cursor.executemany('INSERT OR REPLACE INTO base_rates VALUES (?,?,?)', records)
        conn.commit()
        conn.close()
        print("Done.")
    else:
        print("No data fetched.")

if __name__ == "__main__":
    main()