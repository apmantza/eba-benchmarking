import pandas as pd
import sqlite3
import requests
import io
from eba_benchmarking.config import DB_NAME
from eba_benchmarking.utils import normalize_period

# --- CONSTANTS ---
ITEM_MAP = {
    'I4008': 'CET1 Ratio (%)',
    'I4009': 'Tier 1 Ratio (%)',
    'I4010': 'Total Capital Ratio (%)',
    'I4011': 'Leverage Ratio (%)',
    'I3010': 'Return on Equity (%)',
    'I3011': 'Return on Assets (%)',
    'I3012': 'Cost-to-Income Ratio (%)',
    'I7005': 'NPL Ratio (%)',
    'I6001': 'Liquidity Coverage Ratio (%)',
    'I6002': 'Net Stable Funding Ratio (%)'
}

BIZ_MODEL_MAP = {
    '_T': 'SSM Average',
    '1': 'Universal & Investment Banks',
    '2': 'Corporate/Wholesale Lenders',
    '3': 'Retail-orientated Lenders',
    '4': 'Small Market Lenders',
    '5': 'Consumer Credit Lenders',
    '6': 'G-SIBs',
    '7': 'Asset Managers & Custodians',
    '8': 'Central Savings/Coop Banks',
    '9': 'Other Specialized Lenders'
}

# --- HELPER ---
def fetch_ecb_sdmx(key):
    """Fetches CSV data from ECB SDMX API (SUP Dataflow)."""
    base_url = "https://data-api.ecb.europa.eu/service/data/SUP"
    url = f"{base_url}/{key}?format=csvdata&startPeriod=2020-Q1"
    
    print(f"Fetching: {url}")
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
        else:
            print(f"  [!] Failed ({response.status_code})")
            return None
    except Exception as e:
        print(f"  [!] Error: {e}")
        return None

def main():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ecb_stats (
        period TEXT,
        variable TEXT,
        group_type TEXT,
        group_name TEXT,
        value REAL,
        PRIMARY KEY (period, variable, group_type, group_name)
    )
    ''')
    conn.commit()

    item_codes = "+".join(ITEM_MAP.keys())

    # ==============================================================================
    # JOB 1: COUNTRY AVERAGES
    # ==============================================================================
    print("\n--- Processing Country Averages ---")
    countries = "AT+BE+BG+CY+CZ+DE+DK+EE+ES+FI+FR+GR+HR+HU+IE+IT+LT+LU+LV+MT+NL+PL+PT+RO+SE+SI+SK"
    key_country = f"Q.{countries}.W0._Z.{item_codes}._T.SII._Z._Z._Z.PCT.C"

    df_country = fetch_ecb_sdmx(key_country)

    if df_country is not None:
        if 'CB_ITEM' in df_country.columns and 'REF_AREA' in df_country.columns:
            df_country['variable'] = df_country['CB_ITEM'].map(ITEM_MAP)
            df_country['group_type'] = 'Country'
            df_country['period'] = df_country['TIME_PERIOD'].apply(normalize_period)
            
            df_save = df_country[['period', 'variable', 'group_type', 'REF_AREA', 'OBS_VALUE']].copy()
            df_save.columns = ['period', 'variable', 'group_type', 'group_name', 'value']
            
            data = df_save.dropna(subset=['variable', 'value']).values.tolist()
            cursor.executemany('INSERT OR REPLACE INTO ecb_stats VALUES (?,?,?,?,?)', data)
            conn.commit()
            print(f"  > Saved {len(data)} country benchmarks.")

    # ==============================================================================
    # JOB 2: BUSINESS MODEL AVERAGES
    # ==============================================================================
    print("\n--- Processing Business Model Averages ---")
    # Using wildcard (..) for the 6th dimension (Breakdown)
    key_biz = f"Q.B01.W0._Z.{item_codes}..SII._Z._Z._Z.PCT.C"

    df_biz = fetch_ecb_sdmx(key_biz)

    if df_biz is not None:
        if 'SBS_BREAKDOWN' in df_biz.columns:
            df_biz['variable'] = df_biz['CB_ITEM'].map(ITEM_MAP)
            df_biz['group_type'] = 'Business Model'
            df_biz['group_name'] = df_biz['SBS_BREAKDOWN'].map(BIZ_MODEL_MAP).fillna(df_biz['SBS_BREAKDOWN'])
            df_biz['period'] = df_biz['TIME_PERIOD'].apply(normalize_period)
            
            df_save = df_biz[['period', 'variable', 'group_type', 'group_name', 'OBS_VALUE']].copy()
            df_save.columns = ['period', 'variable', 'group_type', 'group_name', 'value']
            
            data = df_save.dropna(subset=['variable', 'value']).values.tolist()
            cursor.executemany('INSERT OR REPLACE INTO ecb_stats VALUES (?,?,?,?,?)', data)
            conn.commit()
            print(f"  > Saved {len(data)} business model benchmarks.")

    conn.close()
    print("\nUpdate complete.")

if __name__ == "__main__":
    main()