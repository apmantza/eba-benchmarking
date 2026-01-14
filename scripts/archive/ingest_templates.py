import pandas as pd
import sqlite3
import os
import re

DB_PATH = 'eba_data.db'
TEMPLATES_DIR = 'data/templates'

def clean_label(l):
    if pd.isna(l): return ""
    l = str(l).strip()
    l = re.sub(r'\s+', ' ', l)
    return l

def ingest_sheet(file_name, sheet_pattern, template_code):
    file_path = os.path.join(TEMPLATES_DIR, file_name)
    if not os.path.exists(file_path):
        print(f"File {file_name} not found")
        return
        
    excel = pd.ExcelFile(file_path)
    sheet_name = None
    for s in excel.sheet_names:
        if sheet_pattern.lower() in s.lower():
            sheet_name = s
            break
            
    if not sheet_name:
        print(f"Sheet matching '{sheet_pattern}' not found in {file_name}")
        return
        
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pillar3_templates (
        template_code TEXT,
        row_id TEXT,
        row_label TEXT,
        is_ratio BOOLEAN,
        PRIMARY KEY (template_code, row_id)
    )
    """)
    
    count = 0
    id_col = -1
    label_col = -1
    
    # Robust search for columns
    # Look for '1' and something that looks like a label next to it
    for c in range(min(10, len(df.columns) - 1)):
        col_vals = df.iloc[:, c].astype(str).str.strip().tolist()
        for val in ['1', '1.0', '1)']:
            if val in col_vals:
                # Check if next column has text
                c_idx = col_vals.index(val)
                potential_label = clean_label(df.iloc[c_idx, c+1])
                if len(potential_label) > 10:
                    id_col = c
                    label_col = c + 1
                    break
        if id_col != -1: break

    if id_col == -1:
        # Fallback: look for 'Common Equity Tier 1' and take its ID
        for c in range(min(10, len(df.columns) - 1)):
            col_vals = df.iloc[:, c].astype(str).str.lower().tolist()
            if any('common equity tier 1' in v for v in col_vals):
                label_col = c
                id_col = c - 1
                break

    if id_col == -1:
        print(f"Could not find ID/Label columns for {template_code}")
        return

    print(f"Using col {id_col} for ID and col {label_col} for Label in {template_code}")
    
    for idx, row in df.iterrows():
        try:
            rid = str(row.iloc[id_col]).strip()
            if rid.endswith('.0'): rid = rid[:-2]
            
            label = clean_label(row.iloc[label_col])
            
            if rid and label and len(label) > 3:
                # Be more inclusive with rid mapping
                is_valid_id = (
                    re.match(r'^([A-Z]*\s*)?\d+[a-z]?$', rid, re.I) or 
                    rid.startswith('EU') or 
                    rid.startswith('UK') or
                    re.match(r'^[A-Z]\d+$', rid) # e.g. A1, B2
                )
                
                if is_valid_id:
                    is_ratio = '%' in label or 'ratio' in label.lower() or 'percentage' in label.lower()
                    if "total exposure measure" in label.lower():
                        is_ratio = False
                    
                    cur.execute("""
                        INSERT OR REPLACE INTO pillar3_templates (template_code, row_id, row_label, is_ratio)
                        VALUES (?, ?, ?, ?)
                    """, (template_code, rid, label, is_ratio))
                    count += 1
        except:
            continue
            
    conn.commit()
    conn.close()
    print(f"Ingested {count} rows for {template_code}")

if __name__ == "__main__":
    templates = [
        ('1 Disclosure of overview of risk management, key prudential metrics.xlsx', 'EU KM1', 'KM1'),
        ('1 Disclosure of overview of risk management, key prudential metrics.xlsx', 'EU OV1', 'OV1'),
        ('7 Disclosure of own funds-2024-Version 1.xlsx', 'EU CC1', 'CC1'),
        ('7 Disclosure of own funds-2024-Version 1.xlsx', 'EU CC2', 'CC2'),
        ('11 Disclosure of leverage ratio-2024-Version 1.xlsx', 'EU LR2', 'LR2'),
        ('13 Disclosure of liquidity requirements-2024-Version1.xlsx', 'EU LIQ1', 'LIQ1'),
        ('37 Disclosure of interest rate risks of non-trading book activities-2024-Version 1.xlsx', 'EU IRRBB1', 'IRRBB1'),
    ]
    
    for f, s, t in templates:
        ingest_sheet(f, s, t)
