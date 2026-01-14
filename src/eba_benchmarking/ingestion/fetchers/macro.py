import pandas as pd
import sqlite3
import requests
import os
from eba_benchmarking.config import DB_NAME
from eba_benchmarking.utils import normalize_period

def fetch_eurostat_data(dataset_code, params, indicator_name, countries_map):
    """
    Generic fetcher for Eurostat JSON-STAT API.
    countries_map: mapping from Eurostat code to DB code (e.g. {'EL': 'GR'})
    """
    geo_params = "&".join([f"geo={c}" for c in countries_map.keys()])
    url = f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset_code}?format=JSON&lang=en&{geo_params}&{params}"
    
    records = []
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            dims = data['dimension']
            values = data['value']
            
            # Get Index Maps
            def get_map(dim_name):
                idx_obj = dims[dim_name]['category']['index']
                if isinstance(idx_obj, dict):
                    return {k: v for k, v in idx_obj.items()}
                else: # list
                    return {k: i for i, k in enumerate(idx_obj)}

            geo_indices = get_map('geo')
            time_indices = get_map('time')
            
            ids = data['id']
            sizes = data['size']
            
            strides = [1] * len(sizes)
            for i in range(len(sizes) - 2, -1, -1):
                strides[i] = strides[i+1] * sizes[i+1]
            
            geo_dim_idx = ids.index('geo')
            time_dim_idx = ids.index('time')
            
            for geo_code, g_pos in geo_indices.items():
                db_geo = countries_map.get(geo_code, geo_code)
                
                for time_label, t_pos in time_indices.items():
                    flat_idx_val = 0
                    flat_idx_val += g_pos * strides[geo_dim_idx]
                    flat_idx_val += t_pos * strides[time_dim_idx]
                    
                    str_idx = str(flat_idx_val)
                    if str_idx in values:
                        records.append((
                            db_geo,
                            normalize_period(time_label),
                            indicator_name,
                            float(values[str_idx]),
                            'Eurostat'
                        ))
            return records
    except Exception as e:
        print(f"  [!] Error fetching {indicator_name}: {e}")
    return []

def main():
    # Connect to your existing DB
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Create the Macro Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS macro_economics (
        country TEXT,
        period TEXT,
        indicator TEXT,
        value REAL,
        source TEXT,
        PRIMARY KEY (country, period, indicator)
    )
    ''')
    conn.commit()

    # --- PART A: WORLD BANK DATA ---
    wb_indicators = {
        'NY.GDP.MKTP.KD.ZG': 'GDP Growth (%)',
        'SL.UEM.TOTL.ZS': 'Unemployment Rate (%)',
        'FP.CPI.TOTL.ZG': 'Inflation (CPI) (%)'
    }

    try:
        df_countries = pd.read_sql("SELECT DISTINCT country_iso FROM institutions", conn)
        countries = [str(c) for c in df_countries['country_iso'].dropna().unique().tolist() if c]
        print(f"--- Fetching Macro Data for {len(countries)} countries ---")
    except Exception as e:
        print(f"Note: Could not load country list from DB ({e}). Using default list.")
        countries = ['DE', 'FR', 'IT', 'ES', 'NL', 'GR', 'AT', 'BE', 'PT', 'IE']

    # Batch World Bank
    batch_size = 15
    for i in range(0, len(countries), batch_size):
        batch = countries[i:i + batch_size]
        c_str = ';'.join(batch).lower()
        
        for code, name in wb_indicators.items():
            url = f"https://api.worldbank.org/v2/country/{c_str}/indicator/{code}?format=json&per_page=500&date=2020:2024"
            try:
                resp = requests.get(url, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    if len(data) > 1 and isinstance(data[1], list):
                        records = []
                        for entry in data[1]:
                            if entry['value'] is not None:
                                records.append((
                                    entry['country']['id'], # ISO2
                                    normalize_period(entry['date']),
                                    name,
                                    float(entry['value']),
                                    'World Bank'
                                ))
                        cursor.executemany('INSERT OR REPLACE INTO macro_economics VALUES (?,?,?,?,?)', records)
                        print(f"  > Saved {len(records)} rows for {name} (WB Batch {i//batch_size + 1})")
            except Exception as e:
                print(f"  [!] WB Error ({name}): {e}")
    conn.commit()

    # --- PART B: EUROSTAT DATA ---
    print("\n--- Fetching Eurostat Data ---")
    
    # Prepare country mapping (ISO2 -> Eurostat)
    # Ensure each 'c' is a string before calling .replace()
    euro_to_db = {}
    for c in countries:
        if isinstance(c, str):
            euro_code = c.replace('GR', 'EL').replace('GB', 'UK')
            euro_to_db[euro_code] = c
        else:
            # Fallback or skip
            euro_to_db[str(c)] = str(c)
            
    # We need the inverse in the fetcher to map back
    euro_map_back = euro_to_db

    euro_jobs = [
        {
            'code': 'prc_hpi_q',
            'params': 'unit=I15_Q&purchase=TOTAL&sinceTimePeriod=2020-Q1',
            'name': 'House Price Index (2015=100)'
        },
        {
            'code': 'namq_10_gdp',
            'params': 'unit=CLV_PCH_PRE&na_item=B1GQ&s_adj=SCA&sinceTimePeriod=2020-Q1',
            'name': 'GDP Growth (QoQ %)'
        },
        {
            'code': 'une_rt_m',
            'params': 's_adj=SA&age=TOTAL&unit=PC_ACT&sex=T&sinceTimePeriod=2020-M01',
            'name': 'Unemployment Rate (%)'
        },
        {
            'code': 'prc_hicp_manr',
            'params': 'unit=RCH_A&coicop=CP00&sinceTimePeriod=2020-M01',
            'name': 'Inflation (HICP Annual %)'
        }
    ]

    for job in euro_jobs:
        print(f"  > {job['name']}...", end=" ", flush=True)
        results = fetch_eurostat_data(job['code'], job['params'], job['name'], euro_map_back)
        if results:
            cursor.executemany('INSERT OR REPLACE INTO macro_economics VALUES (?,?,?,?,?)', results)
            conn.commit()
            print(f"✅ ({len(results)} rows)")
        else:
            print("❌ (No data)")

    conn.close()
    print("\nDone. Macroeconomic data updated.")

if __name__ == '__main__':
    main()