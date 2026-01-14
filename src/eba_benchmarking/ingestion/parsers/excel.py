"""
Pillar III Excel Parser
Handles Excel files for Piraeus and Bank of Cyprus.
"""
import pandas as pd
import sqlite3
import os
import re
from pathlib import Path
import sys

# Add script dir to path to import mappings
from eba_benchmarking.ingestion.parsers.common import TEMPLATE_ROWS, clean_number
from eba_benchmarking.ebadb import main as setup_database
from eba_benchmarking.config import DB_NAME

DB_PATH = Path(DB_NAME)

def detect_bank_from_file(path):
    filename = os.path.basename(path).upper()
    if 'PIRAEUS' in filename:
        return 'Piraeus', '213800OYHR4PPVA77574'
    if 'CYPRUS' in filename:
        return 'Bank of Cyprus', '635400L14KNHJ3DMBX37'
    if 'NBG' in filename:
        return 'NBG', '5UMCZOEYKCVFAW8ZLO05'
    if 'ALPHA' in filename:
        return 'Alpha Bank', 'NLPK02SGC0U1AABDLL56'
    if 'EUROBANK' in filename:
        return 'Eurobank', 'JEUVK5RWVJEN8W0C9M24'
    return None, None

def parse_excel_report(path):
    bank_name, lei = detect_bank_from_file(path)
    if not bank_name:
        print(f"Unknown bank for file: {path}")
        return []
    
    # Extract period from filename (e.g., 2025-09-30_Piraeus.xlsx -> 2025-09-30)
    fname = os.path.basename(path)
    period_match = re.search(r'(\d{4}-\d{2}-\d{2})', fname)
    target_period = period_match.group(1) if period_match else None
    
    print(f"\nProcessing Excel: {fname} ({bank_name})")
    print(f"  Target period: {target_period}")
    
    try:
        xl = pd.ExcelFile(path)
    except Exception as e:
        print(f"Error opening Excel: {e}")
        return []
    
    all_data = []
    
    for sheet_name in xl.sheet_names:
        template_code = None
        # Identify template
        s_upper = sheet_name.upper()
        if 'KM1' in s_upper: template_code = 'KM1'
        elif 'OV1' in s_upper: template_code = 'OV1'
        elif 'CC1' in s_upper and 'COMMENTARY' not in s_upper: template_code = 'CC1'
        elif 'CC2' in s_upper: template_code = 'CC2'
        elif 'LR1' in s_upper: template_code = 'LR1'
        elif 'LR2' in s_upper: template_code = 'LR2'
        elif 'LR3' in s_upper: template_code = 'LR3'
        elif 'LIQ1' in s_upper: template_code = 'LIQ1'
        elif 'LIQ2' in s_upper: template_code = 'LIQ2'
        elif s_upper == 'KEY METRICS': template_code = 'KM1'
        
        if not template_code:
            continue
            
        print(f"  Parsing template {template_code} from sheet '{sheet_name}'...")
        
        try:
            df = pd.read_excel(path, sheet_name=sheet_name, header=None)
        except Exception as e:
            print(f"    Error reading sheet {sheet_name}: {e}")
            continue
            
        # Determine Units: Target is MILLIONS
        units = 1.0
        # Check first 20 rows for unit declarations
        unit_scan_text = ""
        for i in range(min(20, len(df))):
            unit_scan_text += " ".join(str(x) for x in df.iloc[i].values if pd.notna(x)) + " "
        
        unit_text = unit_scan_text.upper()
        if re.search(r'(?:AMOUNTS\s+IN|IN|€)\s*(?:EURO|EUR)?\s*(?:MILLION|MIO)', unit_text) or '€M' in unit_text or 'EUR M' in unit_text:
            units = 1.0
            print(f"    Detected units: Millions (multiplier 1.0)")
        elif re.search(r'(?:AMOUNTS\s+IN|IN|€)\s*(?:EURO|EUR)?\s*(?:\'000|000|THOUSAND)', unit_text):
            units = 0.001
            print(f"    Detected units: Thousands (multiplier 0.001)")
        elif 'MILLION' in unit_text:
            units = 1.0
            print(f"    Detected units: Millions (fallback)")
        elif '000' in unit_text:
            units = 0.001
            print(f"    Detected units: Thousands (fallback)")
        else:
            # Check if any value is > 100,000 for a ratio? No.
            # Check if CET1 (usually 1st template row) is > 1,000,000
            # For Cyprus/Piraeus, they often have absolute euros.
            units = 0.000001 # Absolute to Millions
            print(f"    Detected units: Absolute Euros (multiplier 1.0e-6)")

        # Map Col -> Date
        date_cols = {} # index -> YYYY-MM-DD
        
        # Look for date headers in first 15 rows
        for i in range(min(15, len(df))):
            for j in range(len(df.columns)):
                val = str(df.iloc[i, j]).strip()
                if not val or val == 'nan': continue
                
                # Try to parse date
                # Formats: "Sep 2025", "30/06/2025", "30.06.2025", "30 JUNE 2025"
                # We normalize everything to 30-06, 30-09, 31-12, 31-03
                found_date = None
                v_up = val.upper()
                
                year_match = re.search(r'(202\d)', v_up)
                if year_match:
                    year = year_match.group(1)
                    if 'SEP' in v_up or '30/09' in v_up or '30.09' in v_up or '09/' in v_up:
                        found_date = f"{year}-09-30"
                    elif 'JUN' in v_up or '30/06' in v_up or '30.06' in v_up or '06/' in v_up:
                        found_date = f"{year}-06-30"
                    elif 'MAR' in v_up or '31/03' in v_up or '31.03' in v_up or '03/' in v_up:
                        found_date = f"{year}-03-31"
                    elif 'DEC' in v_up or '31/12' in v_up or '31.12' in v_up or '12/' in v_up:
                        found_date = f"{year}-12-31"
                
                if found_date:
                    date_cols[j] = found_date

        if not date_cols:
            print(f"    WARNING: No date columns detected in sheet '{sheet_name}'. Skipping.")
            continue
        
        # Filter to only the target period from the filename
        if target_period:
            filtered_date_cols = {k: v for k, v in date_cols.items() if v == target_period}
            if filtered_date_cols:
                date_cols = filtered_date_cols
                print(f"    Using only target period column(s): {target_period}")
            else:
                print(f"    WARNING: Target period {target_period} not found in sheet. Using first available: {list(date_cols.values())[0]}")
                # Use only the first column if target not found
                first_key = list(date_cols.keys())[0]
                date_cols = {first_key: date_cols[first_key]}
        
        print(f"    Extracting from periods: {sorted(list(set(date_cols.values())))}")

        # Row ID and Label columns
        id_col = 0
        label_col = 1
        if bank_name == 'Piraeus' and template_code == 'KM1':
            id_col = 1
            label_col = 2
            
        row_defs = TEMPLATE_ROWS.get(template_code, {})
        
        for i, row in df.iterrows():
            row_id_raw = str(row[id_col]).strip() if pd.notna(row[id_col]) else ""
            row_id = re.sub(r'^EU\s+', '', row_id_raw, flags=re.IGNORECASE)
            row_label = str(row[label_col]).strip() if pd.notna(row[label_col]) else ""
            
            mapping = row_defs.get(row_id)
            if not mapping:
                # Try splitting KM1-1 -> 1
                row_id_short = row_id.split('-')[-1].strip()
                mapping = row_defs.get(row_id_short)

            # Extract for each detected date column
            for j, period in date_cols.items():
                val_raw = row[j]
                amount = clean_number(val_raw)
                
                if amount is not None:
                    is_ratio = False
                    if mapping:
                        # Common ratio IDs in Pillar 3
                        ratio_ids = ['5', '6', '7', '14', '17', '20', '11', '11a', '12']
                        if row_id in ratio_ids or 'ratio' in mapping[0].lower() or '%' in mapping[0]:
                            is_ratio = True
                    else:
                        is_ratio = (abs(amount) < 2.0 and abs(amount) > 0) or "%" in row_label or "ratio" in row_label.lower() or "percentage" in row_label.lower()
                    
                    if not is_ratio:
                        amount *= units
                    
                    # Normalize ratios: only if > 3.0 (e.g. 15.5 for 15.5%)
                    # If it's 1.29 (NSFR), it's already a decimal ratio, don't divide.
                    if is_ratio and abs(amount) >= 3.0 and abs(amount) < 1000:
                        # Exception: LCR (Row 17) can be > 300% (e.g. 3.11)
                        # If row 17 and < 10, assume it's 3.11 (311%), not 3.11%
                        if str(row_id) == '17' and abs(amount) < 10.0:
                            pass
                        else:
                            amount /= 100.0
                    
                    eba_id = mapping[1] if mapping else None
                    label_mapped = mapping[0] if mapping else row_label
                    
                    all_data.append({
                        'bank_name': bank_name,
                        'lei': lei,
                        'period': period,
                        'template_code': template_code,
                        'row_id': row_id,
                        'row_label': label_mapped,
                        'amount': amount,
                        'eba_item_id': eba_id,
                        'table_title': f"Sheet {sheet_name}",
                        'raw_label': row_label,
                        'dimension_name': 'Default',
                        'source_page': 0
                    })

    return all_data

def save_to_db(all_data):
    if not all_data:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    added_count = 0
    for item in all_data:
        cur.execute("""
            SELECT id FROM facts_pillar3 
            WHERE bank_name = ? AND period = ? AND template_code = ? AND row_id = ?
        """, (item['bank_name'], item['period'], item['template_code'], item['row_id']))
        
        if cur.fetchone():
            cur.execute("""
                UPDATE facts_pillar3 
                SET amount = ?, eba_item_id = ?, row_label = ?
                WHERE bank_name = ? AND period = ? AND template_code = ? AND row_id = ?
            """, (item['amount'], item['eba_item_id'], item['row_label'], 
                  item['bank_name'], item['period'], item['template_code'], item['row_id']))
        else:
            cur.execute("""
                INSERT INTO facts_pillar3 
                (bank_name, lei, period, template_code, row_id, row_label, amount, eba_item_id, table_title, raw_label, dimension_name, source_page)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item['bank_name'], item['lei'], item['period'], item['template_code'], 
                  item['row_id'], item['row_label'], item['amount'], item['eba_item_id'], 
                  item['table_title'], item['raw_label'], item['dimension_name'], item['source_page']))
        added_count += 1
    
    conn.commit()
    conn.close()
    print(f"Saved/Updated {added_count} records to database.")

def main():
    setup_database(DB_PATH)
    
    report_dir = 'data/raw/Pillar3reports'
    files = [os.path.join(report_dir, f) for f in os.listdir(report_dir) if f.endswith('.xlsx')]
    
    overall_data = []
    for f in files:
        if os.path.exists(f):
            data = parse_excel_report(f)
            if data:
                overall_data.extend(data)
        else:
            print(f"File not found: {f}")
            
    save_to_db(overall_data)

if __name__ == "__main__":
    main()
