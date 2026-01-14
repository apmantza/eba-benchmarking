"""
Pillar III Enhanced Parser - Version 4
Uses page text to identify templates, then parses tables on that page.

Creates:
1. pillar3_dictionary - Maps Pillar III items to EBA items  
2. facts_pillar3 - Stores parsed data with full metadata
"""

import os
import re
import argparse
import sqlite3
import pandas as pd
import pdfplumber
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'eba_data.db')

# =====================================
# TEMPLATE DEFINITIONS - VERIFIED MAPPINGS
# Maps row IDs to (label, eba_item_id)
# EBA mappings verified against 2025-06-30 data match
# =====================================

TEMPLATE_ROWS = {
    'KM1': {
        '1': ('CET1 Capital', '2520102'),
        '2': ('Tier 1 Capital', '2520133'),  # Verified: TIER 1 CAPITAL
        '3': ('Total Capital', '2520101'),
        '4': ('Total RWA', '2520138'),
        '4a': ('Total RWA pre-floor', '2520154'),
        '5': ('CET1 Ratio', '2520146'),  # Fully loaded ratio
        '5b': ('CET1 Ratio', '2520146'),
        '6': ('Tier 1 Ratio', '2520147'),
        '6b': ('Tier 1 Ratio', '2520147'),
        '7': ('Total Capital Ratio', '2520148'),
        '7b': ('Total Capital Ratio', '2520148'),
        '8': ('Capital Conservation Buffer', None),
        '9': ('Countercyclical Buffer', None),
        'EU 10a': ('O-SII Buffer', None),
        '11': ('Combined Buffer Requirement', None),
        'EU 11a': ('Overall Capital Requirements', None),
        '13': ('Leverage Ratio Exposure', '2520903'),  # Verified match
        '14': ('Total Exposure Measure', '2520903'),
        '15': ('Total HQLA', None),
        '16': ('Total Net Cash Outflows', None),
        '17': ('LCR Ratio', None),
        '18': ('Available Stable Funding', None),
        '19': ('Required Stable Funding', None),
        '20': ('NSFR Ratio', None),
    },
    'CC1': {
        '1': ('Capital Instruments', '2520103'),  # Verified
        '2': ('Retained Earnings', '2520104'),    # Verified
        '3': ('AOCI', '2520105'),                 # Verified
        'EU-3a': ('Funds for general banking risk', '2520107'),
        '5': ('Minority Interests in CET1', '2520108'),
        '6': ('CET1 Before Adjustments', None),
        '7': ('Prudent Valuation Adjustments', '2520109'),
        '8': ('Intangible assets', '2520110'),    # Verified
        '10': ('DTAs future profitability', '2520111'), # Verified
        '28': ('Total regulatory adjustments CET1', None),
        '29': ('CET1 Capital', '2520102'),        # Verified
        '36': ('AT1 before adjustments', None),
        '43': ('Total regulatory adjustments AT1', None),
        '44': ('Tier 1 Capital', '2520133'),      # Verified
        '45': ('Tier 2 instruments', '2520135'),  # Verified
        '51': ('Tier 2 before adjustments', None),
        '57': ('Total regulatory adjustments Tier2', None),
        '58': ('Total Capital', '2520101'),       # Verified
        '59': ('Total RWA', '2520138'),           # Verified
        '60': ('CET1 Ratio', '2520140'),
        '61': ('Tier 1 Ratio', '2520141'),
        '62': ('Total Capital Ratio', '2520142'),
    },
    'OV1': {
        '1': ('Credit Risk excl CCR', '2520201'),      # Verified: exact match
        '2': ('Of which SA', '2520202'),               # Verified: exact match
        '3': ('Of which FIRB', '2520203'),
        '4': ('Of which Slotting', '2520204'),
        '5': ('Of which Equities IRB', '2520205'),
        '6': ('Counterparty Credit Risk', '2520206'),  # Verified
        '7': ('CCR SA-CCR', None),
        '10': ('CVA Risk', '2520207'),                 # Verified
        'EU 10b': ('CVA Basic Approach', '2520207'),
        '15': ('Settlement Risk', '2520208'),
        '16': ('Securitisation Banking Book', '2520209'), # Verified
        '18': ('Securitisation SEC-ERBA', None),
        '19': ('Securitisation SEC-SA', None),
        '20': ('Position FX Commodities Risk', '2520210'), # Verified
        '21': ('Market Risk SA', '2520211'),
        '22': ('Market Risk IMA', '2520212'),
        '23': ('Operational Risk', '2520215'),         # Verified
        '24': ('Operational Risk', '2520215'),
        '25': ('Operational Risk SA', '2520217'),
        '26': ('Output Floor Amount', None),
        '29': ('Total RWA', '2520220'),                # Verified
    },
    'LR1': {
        '1': ('Total assets per FS', None),
        '13': ('Leverage Ratio Exposure', '2520903'),  # Verified: exact match
    },
    'LR2': {
        '13': ('Total On-Balance Sheet Exposures', None),
        'EU-19a': ('Tier 1 Capital', '2520133'),
        '20': ('Leverage Ratio', '2520905'),
        '21': ('Leverage Ratio excl CB Deposits', None),
    },
    'LR3': {
        '1': ('Total assets per FS', None),
        '13': ('Leverage Ratio Exposure', '2520903'),  # Verified: exact match
    },
    'LIQ1': {
        '1': ('Total HQLA', None),
        '2': ('Retail deposits', None),
        '3': ('Stable deposits', None),
        '4': ('Less stable deposits', None),
        '5': ('Unsecured wholesale funding', None),
        '16': ('Total Cash Outflows', None),
        '19': ('Total Cash Inflows', None),
        '20': ('Total Cash Inflows capped', None),
        '21': ('LCR HQLA', None),
        '22': ('Total Net Cash Outflows', None),
        '23': ('LCR Ratio', None),
    },
    'LIQ2': {
        '1': ('Capital items', None),
        '2': ('Own funds', None),
        '4': ('Retail deposits', None),
        '5': ('Stable deposits', None),
        '12': ('Total ASF', None),
        '13': ('Total HQLA for NSFR', None),
        '26': ('Total RSF', None),
        '27': ('NSFR Ratio', None),
    },
    'KM2': {
        '1': ('Own funds and eligible liabilities', None),
        'EU-1a': ('Own Funds', '2520101'),             # Verified
        '2': ('Total RWA', '2520138'),                 # Verified
        '3': ('MREL ratio (% of RWA)', None),
        '4': ('Total exposure measure', '2520903'),    # Verified
        '5': ('MREL ratio (% of TEM)', None),
    },
}


def clean_number(value):
    """Convert string number to float."""
    if value is None or pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    value = str(value).strip()
    
    # Handle empty or non-numeric
    if not value or value in ['-', '–', '—', 'N/A', 'n/a', '']:
        return None
    
    # Check for percentage
    is_pct = '%' in value
    value = value.replace('%', '').replace(' ', '').replace('\n', '').replace('\xa0', '')
    
    # Handle negative in parentheses
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]
    
    # Handle different minus signs
    value = value.replace('−', '-').replace('–', '-')
    
    # Handle European number format
    if ',' in value and '.' in value:
        if value.rfind(',') > value.rfind('.'):
            value = value.replace('.', '').replace(',', '.')
        else:
            value = value.replace(',', '')
    elif ',' in value:
        parts = value.split(',')
        if len(parts) == 2 and len(parts[1]) == 3:
            value = value.replace(',', '')
        else:
            value = value.replace(',', '.')
    
    try:
        result = float(value)
        if is_pct:
            result = result / 100
        return result
    except ValueError:
        return None


def find_template_on_page(page_text):
    """Find Pillar III template codes in page text."""
    patterns = [
        r'EU\s*(KM1|KM2|CC1|CC2|OV1|LR1|LR2|LR3|LIQ1|LIQ2|IRRBB1)',
        r'Table\s+\d+:\s*EU\s*(KM1|KM2|CC1|CC2|OV1|LR1|LR2|LR3|LIQ1|LIQ2)',
    ]
    
    results = []
    for pattern in patterns:
        matches = re.findall(pattern, page_text.upper())
        results.extend(matches)
    
    return list(set(results))


def parse_table_rows(table, template_code):
    """Parse rows from a table using template-specific row definitions."""
    
    row_defs = TEMPLATE_ROWS.get(template_code, {})
    results = []
    
    for row in table:
        if not row or len(row) < 2:
            continue
        
        # Get row ID (first column, often a number)
        row_id = str(row[0]).strip() if row[0] else ''
        
        # Get row label (second column)
        row_label = str(row[1]).strip() if len(row) > 1 and row[1] else ''
        
        # Skip header/empty rows
        if not row_id and not row_label:
            continue
        if row_id.lower() in ['', 'none', 'ref']:
            continue
        
        # Find the first numeric value (looking at columns 2+)
        value = None
        for cell in row[2:]:
            val = clean_number(cell)
            if val is not None:
                value = val
                break
        
        if value is None:
            continue
        
        # Match to row definition
        eba_item_id = None
        matched_label = row_label[:80]
        
        # Try exact row_id match first
        if row_id in row_defs:
            matched_label, eba_item_id = row_defs[row_id]
        else:
            # Try partial label match
            for def_id, (def_label, def_eba) in row_defs.items():
                if def_label.lower() in row_label.lower():
                    eba_item_id = def_eba
                    matched_label = def_label
                    break
        
        results.append({
            'row_id': row_id,
            'row_label': matched_label,
            'raw_label': row_label[:100],
            'value': value,
            'eba_item_id': eba_item_id,
            'is_new': eba_item_id is None
        })
    
    return results


def parse_pillar3_pdf(pdf_path, lei, period):
    """Parse Pillar III PDF extracting all recognized templates."""
    
    print(f"\n{'='*60}")
    print(f"PILLAR III PARSER")
    print(f"{'='*60}")
    print(f"PDF: {os.path.basename(pdf_path)}")
    print(f"LEI: {lei}")
    print(f"Period: {period}")
    
    all_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Pages: {len(pdf.pages)}\n")
        
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            
            # Find templates on this page
            templates = find_template_on_page(page_text)
            
            if not templates:
                continue
            
            tables = page.extract_tables()
            if not tables:
                continue
            
            for template_code in templates:
                print(f"Page {page_num}: Found {template_code}")
                
                # Parse the largest table on this page
                main_table = max(tables, key=lambda t: len(t) if t else 0)
                
                if not main_table or len(main_table) < 3:
                    continue
                
                # Extract table title from page text
                title_match = re.search(rf'Table\s+\d+:\s*(EU\s*{template_code}[^\n]*)', page_text, re.IGNORECASE)
                table_title = title_match.group(1).strip() if title_match else f"EU {template_code}"
                
                rows = parse_table_rows(main_table, template_code)
                
                for row in rows:
                    row['lei'] = lei
                    row['period'] = period
                    row['template'] = template_code
                    row['table_title'] = table_title
                    row['page'] = page_num
                
                if rows:
                    print(f"  Extracted {len(rows)} rows")
                    all_data.extend(rows)
    
    return pd.DataFrame(all_data)


def setup_database(db_path):
    """Create database tables."""
    
    conn = sqlite3.connect(db_path)
    
    # Pillar III Dictionary
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pillar3_dictionary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_code TEXT NOT NULL,
            row_id TEXT,
            row_label TEXT NOT NULL,
            eba_item_id TEXT,
            is_new_metric BOOLEAN DEFAULT 0,
            UNIQUE(template_code, row_id, row_label)
        )
    """)
    
    # Facts Pillar III
    conn.execute("""
        CREATE TABLE IF NOT EXISTS facts_pillar3 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lei TEXT NOT NULL,
            period TEXT NOT NULL,
            template_code TEXT NOT NULL,
            table_title TEXT,
            row_id TEXT,
            row_label TEXT,
            raw_label TEXT,
            amount REAL,
            eba_item_id TEXT,
            is_new_metric BOOLEAN DEFAULT 0,
            source_page INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lei, period, template_code, row_id, row_label)
        )
    """)
    
    # Pillar III Reports tracking
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pillar3_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lei TEXT NOT NULL,
            period TEXT NOT NULL,
            filename TEXT,
            parse_date TEXT DEFAULT CURRENT_TIMESTAMP,
            total_items INTEGER,
            new_items INTEGER,
            UNIQUE(lei, period)
        )
    """)
    
    conn.commit()
    conn.close()


def save_to_database(df, db_path, filename):
    """Save parsed data to database."""
    
    if df.empty:
        return
    
    conn = sqlite3.connect(db_path)
    
    # Update dictionary
    for _, row in df.iterrows():
        try:
            conn.execute("""
                INSERT OR IGNORE INTO pillar3_dictionary 
                (template_code, row_id, row_label, eba_item_id, is_new_metric)
                VALUES (?, ?, ?, ?, ?)
            """, (row['template'], row['row_id'], row['row_label'], 
                  row['eba_item_id'], row['is_new']))
        except:
            pass
    
    # Save facts
    for _, row in df.iterrows():
        conn.execute("""
            INSERT OR REPLACE INTO facts_pillar3 
            (lei, period, template_code, table_title, row_id, row_label, raw_label, 
             amount, eba_item_id, is_new_metric, source_page)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (row['lei'], row['period'], row['template'], row.get('table_title', ''),
              row['row_id'], row['row_label'], row.get('raw_label', ''),
              row['value'], row['eba_item_id'], row['is_new'], row.get('page', 0)))
    
    # Record report
    lei = df['lei'].iloc[0]
    period = df['period'].iloc[0]
    new_count = int(df['is_new'].sum())
    
    conn.execute("""
        INSERT OR REPLACE INTO pillar3_reports 
        (lei, period, filename, total_items, new_items)
        VALUES (?, ?, ?, ?, ?)
    """, (lei, period, filename, len(df), new_count))
    
    conn.commit()
    conn.close()
    
    print(f"\nSaved: {len(df)} items ({new_count} new metrics)")


def print_summary(df):
    """Print extraction summary."""
    
    if df.empty:
        print("\nNo data extracted.")
        return
    
    print(f"\n{'='*60}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*60}")
    
    # By template
    for template in df['template'].unique():
        t_df = df[df['template'] == template]
        new_count = t_df['is_new'].sum()
        print(f"\n{template} ({len(t_df)} items, {new_count} new):")
        
        for _, row in t_df.iterrows():
            mapping = f" → EBA {row['eba_item_id']}" if row['eba_item_id'] else " [NEW]"
            print(f"  {row['row_id']:>5} {row['row_label'][:35]:<35} {row['value']:>12,.2f}{mapping}")


def main():
    parser = argparse.ArgumentParser(description='Parse Pillar III PDF')
    parser.add_argument('--pdf', required=True, help='Path to PDF')
    parser.add_argument('--lei', required=True, help='Bank LEI')
    parser.add_argument('--period', required=True, help='Period (YYYY-MM-DD)')
    parser.add_argument('--db', default=DB_PATH, help='Database path')
    parser.add_argument('--dry-run', action='store_true', help='Do not save')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"ERROR: PDF not found: {args.pdf}")
        return 1
    
    # Parse
    df = parse_pillar3_pdf(args.pdf, args.lei, args.period)
    
    if df.empty:
        print("\nNo data extracted!")
        return 1
    
    # Summary
    print_summary(df)
    
    # Save
    if not args.dry_run:
        setup_database(args.db)
        save_to_database(df, args.db, os.path.basename(args.pdf))
    else:
        print("\n[DRY RUN - Not saved]")
    
    return 0


if __name__ == '__main__':
    exit(main())
