import pandas as pd
import sqlite3
import os
import re
from eba_benchmarking.config import ROOT_DIR, DB_NAME

# --- CONFIGURATION ---
RAW_FOLDER = os.path.join(ROOT_DIR, 'data', 'raw')

# Region Mapping
REGION_MAP = {
    'BG': 'CEE', 'CZ': 'CEE', 'EE': 'CEE', 'HR': 'CEE', 'HU': 'CEE', 
    'LT': 'CEE', 'LV': 'CEE', 'PL': 'CEE', 'RO': 'CEE', 'SI': 'CEE', 'SK': 'CEE',
    'DK': 'Northern Europe', 'FI': 'Northern Europe', 'IS': 'Northern Europe',
    'NO': 'Northern Europe', 'SE': 'Northern Europe', 
    'CY': 'Southern Europe', 'ES': 'Southern Europe', 'GR': 'Southern Europe', 
    'IT': 'Southern Europe', 'MT': 'Southern Europe', 'PT': 'Southern Europe',
    'AT': 'Western Europe', 'BE': 'Western Europe', 'DE': 'Western Europe', 
    'FR': 'Western Europe', 'IE': 'Western Europe', 'LI': 'Western Europe', 
    'LU': 'Western Europe', 'NL': 'Western Europe',
    'GB': 'Western Europe', 'UK': 'Western Europe'
}

# GSIBs List (known large banks in EBA exercises)
GSIBS = [
    'BNP Paribas', 'Deutsche Bank', 'Banco Santander', 'Societe Generale', 
    'HSBC', 'UniCredit', 'ING Groep', 'BPCE', 'Credit Agricole'
]

# Tickers Mapping
TICKER_MAPPINGS = {
    'National Bank of Greece': 'ETE.AT', 'Alpha Bank': 'ALPHA.AT',
    'Eurobank': 'EUROB.AT', 'Piraeus': 'TPEIR.AT', 'Deutsche Bank': 'DBK.DE',
    'Commerzbank': 'CBK.DE', 'BNP Paribas': 'BNP.PA', 'Société générale': 'GLE.PA',
    'Crédit Agricole': 'ACA.PA', 'Banco Santander': 'SAN.MC', 'Intesa Sanpaolo': 'ISP.MI',
    'UNICREDIT': 'UCG.MI', 'ING Groep': 'INGA.AS', 'KBC': 'KBC.BR', 'Erste Group': 'EBS.VI',
    'Raiffeisen Bank International': 'RBI.VI', 'Bank of Cyprus': 'BOCH.CY'
}

def get_path(filename):
    return os.path.join(RAW_FOLDER, filename)

def read_excel_smart(filepath, sheet_name, key_col):
    """
    Reads an Excel sheet and automatically finds the header row 
    by looking for a specific column name (key_col).
    """
    # Read first 10 rows without a header to scan them
    df_temp = pd.read_excel(filepath, sheet_name=sheet_name, header=None, nrows=10)
    
    header_row_idx = -1
    for idx, row in df_temp.iterrows():
        # Check if the key column name exists in this row (case insensitive cleanup)
        row_values = [str(x).strip() for x in row.values]
        if key_col in row_values:
            header_row_idx = idx
            break
    
    if header_row_idx == -1:
        raise ValueError(f"Could not find column '{key_col}' in sheet '{sheet_name}'")
        
    # Reload with the correct header
    return pd.read_excel(filepath, sheet_name=sheet_name, header=header_row_idx)

def main():
    print(f"Connecting to database: {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Create Tables
    cursor.execute('DROP TABLE IF EXISTS institutions')
    cursor.execute('''
    CREATE TABLE institutions (
        lei TEXT PRIMARY KEY,
        name TEXT,
        country_iso TEXT,
        country_name TEXT,
        commercial_name TEXT,
        short_name TEXT,
        ticker TEXT,
        region TEXT,
        Systemic_Importance TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dictionary (
        item_id TEXT PRIMARY KEY,
        label TEXT,
        template TEXT,
        category TEXT,
        tab_name TEXT
    )
    ''')
    conn.commit()

    # 2. Load Institutions
    meta_path = get_path('TR_Metadata.xlsx')
    print(f"Reading metadata from: {meta_path}")

    if not os.path.exists(meta_path):
        print(f"ERROR: File not found at {meta_path}")
    else:
        # Load Main List
        print("  - Processing 'List of Institutions'...")
        try:
            df_main = read_excel_smart(meta_path, 'List of Institutions', 'LEI_Code')
        except:
            print("  - Fallback: 'List of institutions' (lowercase)")
            df_main = read_excel_smart(meta_path, 'List of institutions', 'LEI_Code')
        
        # Create a mapping for Country ISO -> Country Name
        country_map = df_main.set_index('Country')['Desc_country'].to_dict()
        # Add common fallbacks for countries not in the main list
        fallbacks = {'IS': 'Iceland', 'UK': 'United Kingdom', 'GB': 'United Kingdom'}
        country_map.update(fallbacks)
        
        # Load Other Banks
        print("  - Processing 'Other banks'...")
        df_other = read_excel_smart(meta_path, 'Other banks', 'LEI_Code')

        # Clean columns and rename
        cols_map = {'LEI_Code': 'lei', 'Name': 'name', 'Country': 'country_iso', 'Desc_country': 'country_name'}
        
        # For df_other, we fix the country_name using our map before renaming
        df_other['Desc_country'] = df_other['Country'].map(country_map)
        
        df_main = df_main[cols_map.keys()].rename(columns=cols_map)
        df_other = df_other[cols_map.keys()].rename(columns=cols_map)
        
        df_banks = pd.concat([df_main, df_other]).drop_duplicates(subset=['lei'])
        
        # Remove dummy/sum rows
        df_banks = df_banks[~df_banks['lei'].str.lower().str.contains('x{10,}', na=False)]
        
        # --- ENRICHMENT ---
        print("  - Enriching with regions and systemic importance...")
        df_banks['region'] = df_banks['country_iso'].map(REGION_MAP).fillna('Other')
        
        # Default Systemic Importance
        def classify_importance(row):
            name = str(row['name']) if pd.notna(row['name']) else ''
            name = name.lower()
            iso = str(row['country_iso']) if pd.notna(row['country_iso']) else ''
            if any(gsib.lower() in name for gsib in GSIBS):
                return 'GSIB'
            if iso == 'GR' or 'cyprus' in name.lower():
                return 'OSII'
            return 'Other'
            
        df_banks['Systemic_Importance'] = df_banks.apply(classify_importance, axis=1)
        
        # Tickers
        # Tickers from auto-discovery
        lei_to_ticker = {}
        generated_tickers_path = get_path('generated_tickers.csv')
        if os.path.exists(generated_tickers_path):
             try:
                 df_gen = pd.read_csv(generated_tickers_path)
                 lei_to_ticker = df_gen.set_index('lei')['ticker'].to_dict()
                 print(f"  - Loaded {len(lei_to_ticker)} generated tickers.")
             except Exception as e:
                 print(f"  Warning: Could not load generated tickers: {e}")

        def find_ticker(row):
            lei = row.get('lei')
            if lei in lei_to_ticker and pd.notna(lei_to_ticker[lei]):
                return lei_to_ticker[lei]
                
            name = row.get('name')
            if pd.isna(name):
                return None
            name_str = str(name)
            for pattern, ticker in TICKER_MAPPINGS.items():
                if pattern.lower() in name_str.lower():
                    return ticker
            return None
            
        df_banks['ticker'] = df_banks.apply(find_ticker, axis=1)
        
        # Populate commercial_name and short_name from name (required by app.py)
        df_banks['commercial_name'] = df_banks['name']
        df_banks['short_name'] = df_banks['name'].apply(
            lambda x: str(x)[:30] if pd.notna(x) else None
        )
        
        df_banks.to_sql('institutions', conn, if_exists='append', index=False)
        print(f"  > Success: Saved {len(df_banks)} institutions to DB.")

    # 3. Load Dictionary and Mappings
    sdd_path = get_path('SDD.xlsx')
    print(f"Reading dictionary from: {sdd_path}")

    if os.path.exists(sdd_path):
        print("  - Processing 'SDD' mappings...")
        df_sdd = read_excel_smart(sdd_path, 'SDD', 'Item')
        
        # 3a. Save Main Dictionary (Latest IDs)
        # We drop and recreate to ensure the PRIMARY KEY is enforced
        cursor.execute('DROP TABLE IF EXISTS dictionary')
        cursor.execute('''
        CREATE TABLE dictionary (
            item_id TEXT PRIMARY KEY,
            label TEXT,
            template TEXT,
            category TEXT,
            tab_name TEXT
        )
        ''')
        
        dict_map = {'Item': 'item_id', 'Label': 'label', 'Template': 'template', 'Category': 'category'}
        df_dict = df_sdd[dict_map.keys()].rename(columns=dict_map)
        df_dict = df_dict.dropna(subset=['item_id'])
        
        # Define Tab Mapping
        category_to_tab = {
            'Capital': 'Solvency',
            'Leverage': 'Solvency',
            'NPE': 'Asset Quality',
            'Forborne exposures': 'Asset Quality',
            'RWA': 'RWA',
            'P&L': 'Profitability',
            'Market Risk': 'Market Risk',
            'Credit Risk': 'Credit Risk',
            'Sovereign': 'Sovereign',
            'Assets': 'Balance Sheet',
            'Liabilities': 'Balance Sheet',
            'NACE': 'Credit Risk',
            'Collateral': 'Credit Risk'
        }
        df_dict['tab_name'] = df_dict['category'].map(category_to_tab)
        
        # We use INSERT OR REPLACE to handle potential duplicates in the Excel itself
        dict_records = df_dict[['item_id', 'label', 'template', 'category', 'tab_name']].values.tolist()
        cursor.executemany('INSERT OR REPLACE INTO dictionary VALUES (?,?,?,?,?)', dict_records)
        
        # 3b. Create Mappings for Historical Data
        cursor.execute('DROP TABLE IF EXISTS item_mappings')
        cursor.execute('''
        CREATE TABLE item_mappings (
            exercise_year TEXT,
            original_item_id TEXT,
            canonical_item_id TEXT,
            PRIMARY KEY (exercise_year, original_item_id)
        )
        ''')
        
        mapping_cols = [c for c in df_sdd.columns if c.startswith('Item_TR_')]
        
        mapping_records = []
        for col in mapping_cols:
            year_match = re.search(r'\d{4}', col)
            year = year_match.group(0) if year_match else col
            
            df_map = df_sdd[['Item', col]].dropna().copy()
            for _, row in df_map.iterrows():
                # Convert to int then str to remove .0
                orig_id = str(int(row[col]))
                canon_id = str(int(row['Item']))
                mapping_records.append((year, orig_id, canon_id))
        
        # Identity mapping for 2025
        for _, row in df_sdd[['Item']].dropna().iterrows():
            id_val = str(int(row['Item']))
            mapping_records.append(('2025', id_val, id_val))

        cursor.executemany('INSERT OR REPLACE INTO item_mappings VALUES (?,?,?)', mapping_records)
        
        # 3c. Enhance Dictionary with Historical IDs
        print("  - Enhancing dictionary with historical IDs...")
        cursor.execute('''
        INSERT OR IGNORE INTO dictionary (item_id, label, template, category, tab_name)
        SELECT m.original_item_id, d.label, d.template, d.category, d.tab_name
        FROM item_mappings m
        JOIN dictionary d ON m.canonical_item_id = d.item_id
        ''')
        
        print(f"  > Success: Saved {len(df_dict)} canonical definitions and expanded dictionary with historical mappings.")

    # 4. Load Dimension Mappings from TR_Metadata.xlsx
    print("\n--- 4. Loading Dimension Mappings ---")
    dim_sheets = [
        'Portfolio', 'Country', 'Financial_instruments', 'Exposure', 
        'Status', 'Perf_status', 'MKT_Modprod', 'MKT_Risk', 
        'Accounting_portfolio', 'Maturity', 'ASSETS_Stages', 
        'ASSETS_FV', 'NACE_codes'
    ]
    
    for sheet in dim_sheets:
        try:
            print(f"  - Processing dimension: {sheet}...")
            # We don't use read_excel_smart here as headers are usually at the top
            df_dim = pd.read_excel(meta_path, sheet_name=sheet)
            
            # Clean column names
            df_dim.columns = [str(c).strip().lower() for c in df_dim.columns]
            
            # Table name: e.g. dim_portfolio
            table_name = f"dim_{sheet.lower()}"
            df_dim.to_sql(table_name, conn, if_exists='replace', index=False)
            
        except Exception as e:
            print(f"  [!] Skip {sheet}: {e}")

    # Cleanup: Remove sum row from bank_models if it exists
    cursor.execute("DELETE FROM bank_models WHERE lei LIKE '%XXXX%'")

    # Optimization: Index for UI sorting
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inst_name ON institutions(commercial_name)")
    
    conn.commit()
    conn.close()
    print("\nDatabase setup complete!")

if __name__ == "__main__":
    main()