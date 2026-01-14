import requests
import pandas as pd
import sqlite3
import io
import time
from eba_benchmarking.config import DB_NAME

class ECBConnector:
    """
    A robust connector for the ECB Data Portal (SDMX 2.1 API).
    """
    BASE_URL = "https://data-api.ecb.europa.eu/service/data"
    
    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path

    def fetch_series(self, flow_ref, key, start_date='2020-01-01'):
        """
        Fetches a time series from ECB.
        flow_ref: The dataset ID (e.g., 'YC' for Yield Curve, 'EXR' for Exchange Rates)
        key: The specific dimensions (e.g., 'B.U2.EUR.4F.G_N_A.SV_C_YM.SR_1Y')
        """
        url = f"{self.BASE_URL}/{flow_ref}/{key}"
        params = {
            'startPeriod': start_date,
            'format': 'csvdata'
        }
        
        print(f"📡 Connecting to ECB: {flow_ref}...")
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse CSV
            df = pd.read_csv(io.StringIO(response.text))
            return df
        except requests.exceptions.HTTPError as err:
            if response.status_code == 404:
                print(f"   [!] Data not found (404). Check your Key: {key}")
            else:
                print(f"   [!] HTTP Error: {err}")
            return None
        except Exception as e:
            print(f"   [!] Error: {e}")
            return None

    def save_to_db(self, df, category, metric_name_map):
        """
        Saves the fetched data into a 'market_data' table.
        metric_name_map: Dictionary mapping ECB codes to readable names.
        """
        if df is None or df.empty:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ecb_market_data (
            date TEXT,
            category TEXT,
            metric TEXT,
            value REAL,
            PRIMARY KEY (date, metric)
        )
        ''')
        
        # Process Data
        # ECB CSV usually has: TIME_PERIOD, OBS_VALUE, and dimension columns
        data_to_insert = []
        
        for _, row in df.iterrows():
            date = row['TIME_PERIOD']
            val = row['OBS_VALUE']
            
            # Find which key matches this row (if we fetched multiple)
            # We look at the columns to find the specific code
            # Usually the differentiator column varies by dataset
            metric_label = "Unknown"
            
            # Heuristic: Look for the code in the mapped columns
            for col in df.columns:
                if row[col] in metric_name_map:
                    metric_label = metric_name_map[row[col]]
                    break
            
            if metric_label != "Unknown":
                data_to_insert.append((date, category, metric_label, val))
        
        if data_to_insert:
            cursor.executemany(
                'INSERT OR REPLACE INTO ecb_market_data (date, category, metric, value) VALUES (?, ?, ?, ?)', 
                data_to_insert
            )
            conn.commit()
            print(f"   ✅ Saved {len(data_to_insert)} rows for {category}.")
        else:
            print("   ⚠️ No matching metrics found in data.")
            
        conn.close()

def main():
    # --- MAIN EXECUTION ---
    connector = ECBConnector()

    # 1. YIELD CURVES (AAA Govt Bonds)
    # Key: Daily (B), Euro Area (U2), Euro (EUR), AAA (4F), Govt (G_N_A), Spot Yield (SV_C_YM)
    print("\n--- 1. Fetching Yield Curves ---")
    yc_key = "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_1Y+SR_5Y+SR_10Y"
    df_yc = connector.fetch_series("YC", yc_key)
    
    yc_map = {
        'SR_1Y': 'Yield 1Y (AAA)',
        'SR_5Y': 'Yield 5Y (AAA)',
        'SR_10Y': 'Yield 10Y (AAA)'
    }
    connector.save_to_db(df_yc, "Yield Curve", yc_map)

    # 2. EXCHANGE RATES
    # Key: Daily (D), USD+GBP+CHF, EUR, Spot (SP00), Average (A)
    print("\n--- 2. Fetching FX Rates ---")
    fx_key = "D.USD+GBP+CHF.EUR.SP00.A"
    df_fx = connector.fetch_series("EXR", fx_key)
    
    fx_map = {
        'USD': 'EUR/USD',
        'GBP': 'EUR/GBP',
        'CHF': 'EUR/CHF'
    }
    connector.save_to_db(df_fx, "FX", fx_map)

    # 3. INTERBANK RATES (ESTR / EURIBOR)
    # Key for ESTR: Daily, Euro Area, ESTR, Total
    print("\n--- 3. Fetching Money Market Rates ---")
    # FM (Financial Market Data)
    # Key: D.U2.EUR.4F.KR.ESTR.40.EONIA (Example key, checking specific ESTR/Euribor codes is vital)
    # Let's use EURIBOR 3M: D.U2.EUR.RT.MM.EURIBOR3MD_.4F
    # Note: ECB keys are complex. This is a common Euribor 3M key structure.
    mm_key = "D.U2.EUR.RT.MM.EURIBOR3MD_.4F" 
    df_mm = connector.fetch_series("FM", mm_key)
    
    mm_map = {'EURIBOR3MD_': 'Euribor 3M'}
    connector.save_to_db(df_mm, "Interest Rates", mm_map)

    print("\nDone. Database updated.")

if __name__ == "__main__":
    main()