import requests
import pandas as pd
import sqlite3
import io
import re
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from eba_benchmarking.config import DB_NAME, ROOT_DIR
from eba_benchmarking.utils import normalize_period

# --- CONFIGURATION ---
CATALOG_URL = "https://www.bankofgreece.gr/OpenDataSetsCatalog/catalog.xml"
START_DATE = '2020-01-01'
RAW_BOG_DIR = os.path.join(ROOT_DIR, 'data', 'raw', 'bog')

# Target Definitions
TARGETS = {
    "Interest Rates": {
        "keywords": ["Bank interest rates", "new euro-denominated deposits"],
        "table": "bog_macro",
        "processor": "mir",
        "filename": "bog_mir_latest.xlsx"
    },
    "Real Estate": {
        "keywords": ["Index of Apartment Prices"],
        "table": "bog_macro",
        "processor": "real_estate",
        "filename": "bog_hpi_latest.xlsx"
    }
}

def download_and_save(url, target_name):
    """Downloads content and saves to RAW_BOG_DIR."""
    if not os.path.exists(RAW_BOG_DIR):
        os.makedirs(RAW_BOG_DIR)
    
    path = os.path.join(RAW_BOG_DIR, target_name)
    print(f"   📥 Downloading to: {target_name}...", end=" ", flush=True)
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        with open(path, 'wb') as f:
            f.write(resp.content)
        print("✅")
        return path
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def fetch_latest_links():
    # ... (Keep existing RDF parsing logic)
    print(f"📥 Fetching Catalog...", end=" ", flush=True)
    try:
        resp = requests.get(CATALOG_URL, timeout=30)
        if resp.status_code != 200:
            print(f"❌ Error {resp.status_code}")
            return {}
            
        root = ET.fromstring(resp.content)
        print("✅ Parsing RDF...")
        
        found_latest = {}
        for desc in root.findall(".//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description"):
            title_node = desc.find("{http://purl.org/dc/terms/}title")
            if title_node is None: continue
            title = title_node.text
            
            matched_key = None
            for key, meta in TARGETS.items():
                if any(kw.lower() in title.lower() for kw in meta['keywords']):
                    matched_key = key
                    break
            
            if matched_key:
                links = []
                for dist in desc.findall("{http://www.w3.org/ns/dcat#}distribution"):
                    url = dist.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource")
                    if url and url.lower().endswith(('.xls', '.xlsx')):
                        links.append(url)
                
                if links:
                    def extract_date(url):
                        match = re.search(r'(\d{4}-\d{2}-\d{2})', url)
                        return match.group(1) if match else "1900-01-01"
                    links.sort(key=extract_date, reverse=True)
                    found_latest[matched_key] = links[0]
                    print(f"   🎯 {matched_key}: Found Latest ({links[0].split('/')[-1]})")

        return found_latest
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

def process_real_estate(file_path):
    """
    Normalizes Real Estate Index (Quarterly -> Monthly) from local file.
    """
    print("   ⏳ Parsing Real Estate...", end=" ", flush=True)
    try:
        df = pd.read_excel(file_path)
        # Handle BoG's ":" for missing values
        df = df.replace(':', pd.NA)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Find Year and Quarter columns
        col_year = next((c for c in df.columns if 'year' in c.lower() or 'έτος' in c.lower()), None)
        col_q = next((c for c in df.columns if 'quarter' in c.lower() or 'τρίμηνο' in c.lower()), None)
        
        if not col_year or not col_q: 
            print(f"❌ Columns not found. Headers: {df.columns.tolist()}")
            return None

        def parse_q(row):
            try:
                y = int(row[col_year])
                q_val = str(row[col_q])
                q = int(''.join(filter(str.isdigit, q_val)))
                # Map Quarter to end of month
                return pd.Timestamp(year=y, month=q*3, day=1) + pd.offsets.MonthEnd(0)
            except:
                return None

        df['date'] = df.apply(parse_q, axis=1)
        df = df.dropna(subset=['date']).set_index('date').sort_index()
        
        # Identify metric columns (avoid year/quarter/status)
        exclude = [col_year, col_q, 'Status', 'Κατάσταση']
        metric_cols = [c for c in df.columns if c not in exclude and c != 'date']
        
        if not metric_cols:
            print("❌ No metric columns found.")
            return None

        # Process each metric column
        all_metrics = []
        for col in metric_cols:
            # Upsample Q -> M
            temp = df[[col]].copy()
            temp[col] = pd.to_numeric(temp[col], errors='coerce')
            df_monthly = temp.resample('ME').ffill().reset_index()
            df_monthly = df_monthly[df_monthly['date'] >= START_DATE]
            
            df_monthly.columns = ['date', 'value']
            df_monthly['metric'] = col
            df_monthly['category'] = 'Real Estate Indices (BoG)'
            all_metrics.append(df_monthly)
            
        if not all_metrics: return None
        
        final_df = pd.concat(all_metrics, ignore_index=True)
        print(f"✅ Done ({len(final_df)} records).")
        return final_df
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def process_mir(file_path):
    """
    Normalizes Interest Rates (MIR) from local file.
    """
    print("   ⏳ Parsing Interest Rates...", end=" ", flush=True)
    try:
        df = pd.read_excel(file_path)
        # Handle BoG's ":" for missing values
        df = df.replace(':', pd.NA)
        df.columns = [str(c).strip() for c in df.columns]
        
        col_year = next((c for c in df.columns if 'year' in c.lower()), None)
        col_month = next((c for c in df.columns if 'month' in c.lower()), None)
        
        if not col_year or not col_month:
            print(f"❌ Year/Month columns not found. Headers: {df.columns.tolist()}")
            return None
            
        def parse_date(row):
            try:
                y = int(row[col_year])
                m = int(row[col_month])
                return pd.Timestamp(year=y, month=m, day=1) + pd.offsets.MonthEnd(0)
            except:
                return None

        df['date'] = df.apply(parse_date, axis=1)
        df = df.dropna(subset=['date']).set_index('date').sort_index()
        df = df[df.index >= START_DATE]
        
        # Identify numeric columns
        exclude = [col_year, col_month, 'Status']
        metric_cols = [c for c in df.columns if c not in exclude and c != 'date']
        
        all_data = []
        for col in metric_cols:
            temp = df[[col]].copy().reset_index()
            temp.columns = ['date', 'value']
            temp['value'] = pd.to_numeric(temp['value'], errors='coerce')
            temp = temp.dropna(subset=['value'])
            temp['metric'] = col
            temp['category'] = 'Interest Rates (BoG)'
            all_data.append(temp)
            
        if not all_data:
            print("❌ No valid data found.")
            return None

        final_df = pd.concat(all_data, ignore_index=True)
        print(f"✅ Done. ({len(final_df)} records)")
        return final_df
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def save_to_db(df):
    if df is None or df.empty: return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bog_macro (
            date TEXT,
            category TEXT,
            metric TEXT,
            value REAL,
            PRIMARY KEY (date, metric)
        )
    ''')
    df['date'] = df['date'].dt.strftime('%Y-%m-%d').apply(normalize_period)
    records = df[['date', 'category', 'metric', 'value']].values.tolist()
    cursor.executemany('INSERT OR REPLACE INTO bog_macro VALUES (?,?,?,?)', records)
    conn.commit()
    conn.close()
    print(f"      💾 Saved {len(records)} records to DB.")

def main():
    links = fetch_latest_links()
    
    for key, url in links.items():
        print(f"\n--- Processing {key} ---")
        filename = TARGETS[key]['filename']
        local_path = download_and_save(url, filename)
        
        if local_path:
            if key == "Real Estate":
                df = process_real_estate(local_path)
            elif key == "Interest Rates":
                df = process_mir(local_path)
            
            save_to_db(df)

if __name__ == "__main__":
    main()