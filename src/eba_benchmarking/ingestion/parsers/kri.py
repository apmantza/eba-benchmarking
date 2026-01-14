import pandas as pd
import sqlite3
import os
import glob
from eba_benchmarking.config import ROOT_DIR, DB_NAME
from eba_benchmarking.utils import normalize_period

def main():
    print("--- [KRI] Processing EBA Risk Dashboard Data Annex ---")
    
    # 1. Locate the file
    search_pattern = os.path.join(ROOT_DIR, 'data', 'raw', 'Data Annex InteractiveRiskDashboard*.xlsx')
    files = glob.glob(search_pattern)
    
    if not files:
        print(f"⚠️ No file found matching {search_pattern}")
        return
    
    file_path = files[0] # Take the latest one if multiple exist
    print(f"  > Reading: {os.path.basename(file_path)}")
    
    try:
        # 2. Read the specific sheet
        df = pd.read_excel(file_path, sheet_name='KRIs by country and EU')
        
        # 3. Normalize Columns
        # Original columns are [Period] [Country] [Number] [Name] [Ratio]
        df.columns = [str(c).replace('[', '').replace(']', '').strip().lower() for c in df.columns]
        
        # 4. Standardize Data
        print("  > Normalizing periods and cleaning data...")
        df['period'] = df['period'].astype(str).apply(normalize_period)
        
        # Ensure country is string and uppercase
        df['country'] = df['country'].astype(str).str.upper().str.strip()
        
        # Clean KPI names (remove newlines etc)
        df['name'] = df['name'].astype(str).str.replace('\n', ' ').str.strip()
        
        # Ensure ratio is numeric
        df['ratio'] = pd.to_numeric(df['ratio'], errors='coerce')
        df = df.dropna(subset=['ratio'])
        
        # 5. Save to Database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS eba_kris (
            period TEXT,
            country TEXT,
            kri_code TEXT,
            kri_name TEXT,
            value REAL,
            PRIMARY KEY (period, country, kri_code)
        )
        ''')
        
        # Mapping columns to DB schema
        df_save = df[['period', 'country', 'number', 'name', 'ratio']].copy()
        df_save.columns = ['period', 'country', 'kri_code', 'kri_name', 'value']
        
        data = df_save.values.tolist()
        cursor.executemany('INSERT OR REPLACE INTO eba_kris VALUES (?,?,?,?,?)', data)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Success! Imported {len(data)} country-level KRIs into 'eba_kris'.")
        
    except Exception as e:
        print(f"❌ Error processing KRI Annex: {e}")

if __name__ == '__main__':
    main()
