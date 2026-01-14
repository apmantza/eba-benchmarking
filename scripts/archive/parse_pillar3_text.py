"""
Pillar III Text-Based Parser - Universal for Greek Banks
Handles PDFs where table extraction doesn't work properly.
"""

import os
import re
import sqlite3
import pandas as pd
import pdfplumber
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR.parent / 'eba_data.db'

# Bank patterns
BANK_PATTERNS = {
    'National Bank of Greece': '5UMCZOEYKCVFAW8ZLO05',
    'NBG': '5UMCZOEYKCVFAW8ZLO05',
    'Eurobank': 'JEUVK5RWVJEN8W0C9M24',
    'Eurobank Ergasias': 'JEUVK5RWVJEN8W0C9M24',
    'Alpha Bank': 'KLQDKFP5ACPO4FAJ9Y58',
    'Alpha Services': 'KLQDKFP5ACPO4FAJ9Y58',
    'Piraeus Bank': '213800OYHR1MPQ5VJL60',
    'Piraeus Financial Holdings': '213800OYHR1MPQ5VJL60',
    'Piraeus': '213800OYHR1MPQ5VJL60',
}

# KM1 row patterns - extract first number after row label
KM1_PATTERNS = [
    (r'(?:^\s*1\s+|)Common\s+Equity\s+Tier\s+[1I].*?capital.*?([\d\.,\s]+)', '1', 'CET1 Capital', '2520102'),
    (r'(?:^\s*2\s+|)Tier\s+1\s+capital.*?([\d\.,\s]+)', '2', 'Tier 1 Capital', '2520133'),
    (r'(?:^\s*3\s+|)Total\s+capital.*?([\d\.,\s]+)', '3', 'Total Capital', '2520101'),
    (r'(?:^\s*4\s+|)Total\s+risk.*?exposure.*?amount.*?([\d\.,\s]+)', '4', 'Total RWA', '2520138'),
    (r'(?:^\s*4a\s+|)Total\s+risk.*?pre-floor.*?([\d\.,\s]+)', '4a', 'Total RWA pre-floor', '2520154'),
    (r'(?:^\s*5\s+|)Common\s+Equity.*?ratio.*?([\d\.,\s]+%?)', '5', 'CET1 Ratio', '2520146'),
    (r'(?:^\s*6\s+|)Tier\s+1\s+ratio.*?([\d\.,\s]+%?)', '6', 'Tier 1 Ratio', '2520147'),
    (r'(?:^\s*7\s+|)Total\s+capital\s+ratio.*?([\d\.,\s]+%?)', '7', 'Total Capital Ratio', '2520148'),
    (r'(?:^\s*14\s+|)Leverage\s+ratio.*?([\d\.,\s]+%?)', '14', 'Leverage Ratio', '2520905'),
]

# OV1 row patterns
OV1_PATTERNS = [
    (r'(?:^\s*1\s+|)Credit\s+risk.*?excluding.*?([\d\.,\s]+)', '1', 'Credit Risk excl CCR', '2520201'),
    (r'(?:^\s*29\s+|)Total.*?([\d\.,\s]+)', '29', 'Total RWA', '2520220'),
]


def clean_number(value):
    """Convert string number to float. Robustly handles US and European formats."""
    if not value:
        return None
    
    value = str(value).strip()
    is_pct = '%' in value
    
    # Remove percentage sign and non-break spaces
    value = value.replace('%', '').replace('\xa0', ' ').strip()
    
    # Handle negative signs
    is_negative = False
    if value.startswith('(') and value.endswith(')'):
        is_negative = True
        value = value[1:-1].strip()
    elif value.startswith('-') or value.startswith('–') or value.startswith('—'):
        is_negative = True
        value = value[1:].strip()

    # Detect format pattern
    # 1. contains both . and ,
    if ',' in value and '.' in value:
        if value.rfind(',') > value.rfind('.'):
            # European: 1.234,56 -> omit dots, comma to dot
            value = value.replace('.', '').replace(',', '.')
        else:
            # US: 1,234.56 -> omit commas
            value = value.replace(',', '')
    
    # 2. contains only ,
    elif ',' in value:
        # If it looks like a European decimal (e.g. "16,08")
        # Or if it's a thousands separator with 3 digits after (e.g. "1,234")
        parts = value.split(',')
        if len(parts) == 2 and len(parts[1]) == 3:
            # Most likely thousands separator
            value = value.replace(',', '')
        else:
            # Most likely decimal separator
            value = value.replace(',', '.')
            
    # 3. contains only .
    elif '.' in value:
        # THIS IS THE TRICKY ONE for Alpha Bank (e.g. "4.921" is 4921)
        # If there are exactly 3 digits after the dot, and it's not a ratio page,
        # it might be a thousands separator.
        # Ratios usually have 2 digits after decimal.
        parts = value.split('.')
        # If more than one dot, definitely thousands
        if len(parts) > 2:
            value = value.replace('.', '')
        # If one dot followed by 3 digits and is a large number context
        elif len(parts) == 2 and len(parts[1]) == 3:
            # Let's check if it's likely a thousands separator
            # In Pillar 3, absolute amounts are large, ratios are small.
            # We'll assume dots followed by 3 digits are thousands unless it's a very small number
            # But "4.921" is ambiguous. However, Alpha Bank uses comma for decimals (16,08%).
            # So if we see a dot and no comma, and it's 3 digits, we'll treat as thousands.
            value = value.replace('.', '')
        # Else treat as standard decimal "."

    try:
        result = float(value)
        if is_negative:
            result = -result
        if is_pct:
            result = result / 100
        return result
    except:
        return None


# Bank name patterns to LEI and Canonical Name mapping
BANK_PATTERNS = {
    'National Bank of Greece': ('5UMCZOEYKCVFAW8ZLO05', 'NBG'),
    'NBG': ('5UMCZOEYKCVFAW8ZLO05', 'NBG'),
    'Eurobank': ('JEUVK5RWVJEN8W0C9M24', 'Eurobank'),
    'Alpha Bank': ('KLQDKFP5ACPO4FAJ9Y58', 'Alpha Bank'),
    'Alpha Services': ('KLQDKFP5ACPO4FAJ9Y58', 'Alpha Bank'),
    'Piraeus Bank': ('213800OYHR1MPQ5VJL60', 'Piraeus'),
    'Piraeus Financial Holdings': ('213800OYHR1MPQ5VJL60', 'Piraeus'),
    'Piraeus': ('213800OYHR1MPQ5VJL60', 'Piraeus'),
}



def detect_bank(text, filename):
    """Detect bank from text or filename."""
    combined = (text + ' ' + filename).upper()
    for pattern, (lei, canonical_name) in BANK_PATTERNS.items():
        if pattern.upper() in combined:
            return canonical_name, lei
    return None, None


def detect_period(text, filename):
    """Detect period from text or filename."""
    # Look for date patterns
    patterns = [
        r'30[\./]06[\./](\d{4})',
        r'(\d{4})[\./\-]06[\./\-]30',
        r'30\s*June\s*(\d{4})',
        r'June\s*30.*?(\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}-06-30"
    
    # Try filename
    year_match = re.search(r'(\d{4})', filename)
    if year_match:
        return f"{year_match.group(1)}-06-30"
    
    return "2025-06-30"


def normalize_text(text):
    """Clean up text that might have spaces between characters (e.g. 'C E T 1')."""
    # First, handle the common '1 0 7 , 1 0 0' -> '107,100' case
    # If we see a pattern of char-space-char-space
    # This is tricky because it might merge words.
    # Let's just try to remove extra spaces within a line if it looks like spaced text
    lines = []
    for line in text.split('\n'):
        # If line has lots of single-char "words", it's likely spaced
        words = line.split()
        if len(words) > 10 and all(len(w) <= 2 for w in words):
            # Reconstruct by joining and then splitting on multiple spaces
            # Actually, let's just remove ALL spaces and see if we can still match
            # But regex patterns usually expect some spaces.
            # Better: remove spaces only if they are between digits or letters of the same word.
            cleaned = re.sub(r'(\b\w)\s(?=\w\b)', r'\1', line)
            cleaned = re.sub(r'(\d)\s+(?=\d)', r'\1', cleaned)
            cleaned = re.sub(r'(\d)\s*,\s*(\d)', r'\1,\2', cleaned)
            lines.append(cleaned)
        else:
            lines.append(line)
    return '\n'.join(lines)

def parse_text_patterns(text, patterns, template_code):
    """Parse text using regex patterns."""
    results = []
    
    # Normalize text for better matching
    text = normalize_text(text)
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        for pattern, row_id, label, eba_id in patterns:
            # Flexible pattern that allows for some extra spaces
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                value = clean_number(match.group(1))
                if value is not None:
                    results.append({
                        'row_id': row_id,
                        'row_label': label,
                        'raw_label': line[:100],
                        'value': value,
                        'eba_item_id': eba_id,
                        'is_new': eba_id is None,
                        'template': template_code,
                    })
                break
    
    return results

# Expanded Patterns
CC2_PATTERNS = [
    (r'Total\s+assets.*?(\d[\d\.,\s]+)', '1', 'Total Assets (CC2)', None),
    (r'Total\s+equity.*?(\d[\d\.,\s]+)', '3', 'Total Equity (CC2)', None),
    (r'Common\s+Equity\s+Tier\s+I\s+capital.*?(\d[\d\.,\s]+)', 'CET1', 'CET1 Capital', '2520102'),
]

LR1_PATTERNS = [
    (r'Total\s+assets\s+per\s+financial\s+statements.*?(\d[\d\.,\s]+)', '1', 'Total assets per FS', None),
    (r'Leverage\s+ratio\s+total\s+exposure\s+measure.*?(\d[\d\.,\s]+)', '13', 'Leverage Exposure', '2520903'),
]

LIQ1_PATTERNS = [
    (r'Liquidity\s+buffer.*?(\d[\d\.,\s]+)', '21', 'Liquidity Buffer (LCR)', None),
    (r'Total\s+net\s+cash\s+outflows.*?(\d[\d\.,\s]+)', '22', 'Total Net Cash Outflows', None),
    (r'Liquidity\s+coverage\s+ratio.*?([\d\.,\s]+%?)', '23', 'LCR Ratio', None),
]

def is_toc_page(text):
    """Detect if a page is likely a Table of Contents."""
    text_upper = text.upper()
    toc_indicators = ['TABLE OF CONTENTS', 'CONTENTS', 'INDEX']
    if any(ind in text_upper for ind in toc_indicators) and text_upper.count('.') > 50:
        return True
    dots_count = text.count('.') + text.count('·')
    if dots_count > 100:
        return True
    patterns = [r'EU\s*[A-Z0-9-]+\s*\.{5,}\s*\d+', r'Template\s*\d+.*\.{5,}\s*\d+']
    matches = []
    for p in patterns:
        matches.extend(re.findall(p, text, re.IGNORECASE))
    if len(matches) > 3:
        return True
    return False

def extract_text_from_words(page):
    """Reconstruct text from words if extract_text() fails or returns garbage."""
    words = page.extract_words()
    if not words:
        return ""
    
    # Sort words by top, then x0
    # pdfplumber words have 'x0', 'x1', 'top', 'bottom'
    try:
        words.sort(key=lambda x: (x['top'], x['x0']))
    except KeyError:
        # Fallback if keys are different
        return page.extract_text() or ""
    
    lines = []
    current_line = []
    current_top = words[0]['top']
    
    tolerance = 3 # pixels for same line
    
    for w in words:
        if abs(w['top'] - current_top) < tolerance:
            current_line.append(w)
        else:
            # End of line, join words
            current_line.sort(key=lambda x: x['x0'])
            lines.append(" ".join([x['text'] for x in current_line]))
            current_line = [w]
            current_top = w['top']
    
    if current_line:
        current_line.sort(key=lambda x: x['x0'])
        lines.append(" ".join([x['text'] for x in current_line]))
        
    return "\n".join(lines)

def parse_pdf_text(pdf_path):
    """Parse PDF using text-based extraction."""
    
    filename = os.path.basename(pdf_path)
    print(f"\n{'='*70}")
    print(f"TEXT PARSER: {filename}")
    print(f"{'='*70}")
    
    all_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        
        # Get full text for detection
        first_pages_text = ""
        for page in pdf.pages[:10]:
            first_pages_text += (page.extract_text() or "") + "\n"
        
        bank_name, lei = detect_bank(first_pages_text, filename)
        period = detect_period(first_pages_text, filename)
        
        print(f"Bank: {bank_name}")
        print(f"LEI: {lei}")
        print(f"Period: {period}")
        
        if not lei:
            lei = "UNKNOWN"
        
        # Parse each page
        for page_num, page in enumerate(pdf.pages, start=1):
            # Try both regular extraction and word-based reconstruction
            text = page.extract_text(layout=True) or ""
            
            # If text is very short but bank is Eurobank, try word-based reconstruction
            if (len(text.strip()) < 100 or bank_name == 'Eurobank') and page.extract_words():
                text = extract_text_from_words(page)
            
            if is_toc_page(text):
                continue
                
            text_upper = text.upper()
            
            # KM1 template
            if 'KM1' in text_upper and ('KEY METRICS' in text_upper or 'COMMON' in text_upper):
                results = parse_text_patterns(text, KM1_PATTERNS, 'KM1')
                for r in results:
                    r['lei'] = lei
                    r['period'] = period
                    r['page'] = page_num
                    r['bank_name'] = bank_name
                    r['table_title'] = 'EU KM1 - Key Metrics'
                all_data.extend(results)
            
            # CC2 template
            if 'CC2' in text_upper and ('RECONCILIATION' in text_upper or 'BALANCE SHEET' in text_upper):
                results = parse_text_patterns(text, CC2_PATTERNS, 'CC2')
                for r in results:
                    r['lei'] = lei
                    r['period'] = period
                    r['page'] = page_num
                    r['bank_name'] = bank_name
                    r['table_title'] = 'EU CC2 - Reconciliation'
                all_data.extend(results)

            # OV1 template
            if 'OV1' in text_upper and ('RWA' in text_upper or 'CAPITAL REQUIREMENTS' in text_upper):
                results = parse_text_patterns(text, OV1_PATTERNS, 'OV1')
                for r in results:
                    r['lei'] = lei
                    r['period'] = period
                    r['page'] = page_num
                    r['bank_name'] = bank_name
                    r['table_title'] = 'EU OV1 - Overview of RWA'
                all_data.extend(results)

            # LR1 template
            if 'LR1' in text_upper and 'LEVERAGE' in text_upper:
                results = parse_text_patterns(text, LR1_PATTERNS, 'LR1')
                for r in results:
                    r['lei'] = lei
                    r['period'] = period
                    r['page'] = page_num
                    r['bank_name'] = bank_name
                    r['table_title'] = 'EU LR1 - Leverage Summary'
                all_data.extend(results)

            # LIQ1 template
            if 'LIQ1' in text_upper and 'LCR' in text_upper:
                results = parse_text_patterns(text, LIQ1_PATTERNS, 'LIQ1')
                for r in results:
                    r['lei'] = lei
                    r['period'] = period
                    r['page'] = page_num
                    r['bank_name'] = bank_name
                    r['table_title'] = 'EU LIQ1 - LCR'
                all_data.extend(results)
    
    # Remove duplicates (keep first occurrence)
    seen = set()
    unique_data = []
    for item in all_data:
        key = (item['template'], item['row_id'])
        if key not in seen:
            seen.add(key)
            unique_data.append(item)
    
    print(f"\nExtracted: {len(unique_data)} unique items")
    return pd.DataFrame(unique_data), lei, period, bank_name


def save_to_database(df, db_path):
    """Save parsed data to database."""
    if df.empty:
        return 0
    
    conn = sqlite3.connect(db_path)
    
    for _, row in df.iterrows():
        try:
            conn.execute("""
                INSERT OR REPLACE INTO facts_pillar3 
                (lei, period, template_code, table_title, row_id, row_label, raw_label, 
                 amount, eba_item_id, is_new_metric, source_page, bank_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (row['lei'], row['period'], row['template'], row.get('table_title', ''),
                  row['row_id'], row['row_label'], row.get('raw_label', ''),
                  row['value'], row['eba_item_id'], row['is_new'], row.get('page', 0),
                  row.get('bank_name', '')))
        except Exception as e:
            print(f"Error: {e}")
    
    conn.commit()
    conn.close()
    
    return len(df)


if __name__ == '__main__':
    pdfs = [
        "data/raw/Pillar3reports/20250630-pillar-III-disclosures-final.pdf",  # Alpha Bank
        "data/raw/Pillar3reports/consolidated-pillar-3-report.pdf",  # Eurobank
        "data/raw/Pillar3reports/Pillar_III_EN_20250630.pdf",  # Piraeus
    ]
    
    total_saved = 0
    
    for pdf_path in pdfs:
        if not os.path.exists(pdf_path):
            print(f"Not found: {pdf_path}")
            continue
        
        df, lei, period, bank = parse_pdf_text(pdf_path)
        
        if not df.empty:
            print("\nExtracted data:")
            for tmpl in df['template'].unique():
                t_df = df[df['template'] == tmpl]
                mapped = t_df['eba_item_id'].notna().sum()
                print(f"  {tmpl}: {len(t_df)} items ({mapped} mapped)")
            
            saved = save_to_database(df, str(DB_PATH))
            total_saved += saved
            print(f"Saved {saved} records")
    
    print(f"\n=== Total saved: {total_saved} ===")
