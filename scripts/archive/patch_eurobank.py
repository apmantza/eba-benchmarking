import sys
import os
import sqlite3
import pdfplumber
import re
import time
from operator import itemgetter

# Import parse functions from the batch script
try:
    from scripts.parse_pillar3_batch import TEMPLATE_ROWS, parse_text_rows, clean_number
except ImportError:
    from parse_pillar3_batch import TEMPLATE_ROWS, parse_text_rows, clean_number

# DB Path
DB_PATH = 'eba_data.db'

def reconstruct_page_text(page):
    """
    Reconstructs page text by grouping words visually (Y-coordinate).
    Fixes Eurobank's 'spaced text' and 'columnar block' issues found in Q3 reports.
    Uses geometric distance to merge characters/numbers while preserving column gaps.
    """
    words = page.extract_words()
    if not words:
        return page.extract_text() or ""
        
    # Sort by Y (top) then X (x0)
    words.sort(key=itemgetter('top', 'x0'))
    
    lines = []
    current_line = []
    last_top = 0
    
    # Group by line (tolerance 3px is standard for text lines)
    for w in words:
        if not current_line:
            current_line.append(w)
            last_top = w['top']
            continue
            
        if abs(w['top'] - last_top) < 3:
            current_line.append(w)
        else:
            lines.append(current_line)
            current_line = [w]
            last_top = w['top']
    if current_line: lines.append(current_line)
    
    # Reconstruct strings with Geometry-based merging
    text_lines = []
    
    for line in lines:
        row_text = ""
        for i, w in enumerate(line):
            if i == 0:
                row_text += w['text']
                continue
            
            prev = line[i-1]
            dist = w['x0'] - prev['x1']
            
            # Threshold: 1.5px. 
            # Letters in Eurobank condensed font are very close (0-1px).
            # Spaces are usually > 3px.
            # Numbers "5 1 , 7 5 6" often have intra-digit spacing around 1-2px?
            # We treat < 1.5 as "Same Word/Number".
            if dist < 1.5: 
                row_text += w['text']
            else:
                row_text += " " + w['text']
        
        # Merge numbers split by comma/dot: "51 , 756" -> "51,756"
        row_text = re.sub(r'\s*([,.])\s*', r'\1', row_text)
            
        text_lines.append(row_text)
        
    return "\n".join(text_lines)

def save_eurobank_data(rows, page_num, pdf_filename):
    conn = sqlite3.connect(DB_PATH)
    
    # Detect Period from Filename
    period = '2025-06-30' # Default
    if '092025' in pdf_filename or 'Sep' in pdf_filename:
        period = '2025-09-30'
    elif '062025' in pdf_filename or 'Jun' in pdf_filename:
        period = '2025-06-30'
    elif '122025' in pdf_filename or 'Dec' in pdf_filename:
        period = '2025-12-31'
    elif '032025' in pdf_filename or 'Mar' in pdf_filename:
        period = '2025-03-31'
        
    count = 0
    for r in rows:
        # Default metadata for Eurobank
        conn.execute("""
            INSERT OR REPLACE INTO facts_pillar3 
            (lei, period, template_code, table_title, row_id, row_label, raw_label, 
             amount, eba_item_id, is_new_metric, source_page, bank_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('JEUVK5RWVJEN8W0C9M24', period, r.get('template_code') or r.get('template'), 
              'Eurobank Patch', r['row_id'], r['row_label'], r['raw_label'],
              r['value'], r['eba_item_id'], r['is_new'], page_num, 'Eurobank'))
        count += 1
    conn.commit()
    conn.close()
    return count

def scan_index_pages(pdf):
    """Scan the first few pages to build a map of Template -> Page Number."""
    page_map = {}
    print("Scanning Index of Tables...")
    
    combined_toc_text = ""
    for i in range(min(10, len(pdf.pages))):
        text = pdf.pages[i].extract_text() or ""
        combined_toc_text += text + "\n"
        
    target_codes = ['KM1', 'CC1', 'OV1', 'KM2', 'LR1', 'LR2', 'CR1', 'CR3', 'CQ1', 'CCR1', 'LIQ1']
    
    lines = combined_toc_text.split('\n')
    for line in lines:
        line = line.strip()
        for code in target_codes:
            if (f" {code} " in line or f" {code}-" in line or f": {code} " in line) and len(line) > 10:
                parts = line.split()
                last_part = parts[-1].replace('.', '')
                if last_part.isdigit():
                    page_num = int(last_part)
                    if code not in page_map:
                        page_map[code] = []
                    if page_num not in page_map[code]:
                        page_map[code].append(page_num)
                        print(f"  -> Detected {code} on Page {page_num}")

    return page_map

def patch_eurobank():
    print("Running Eurobank Patch Parser (Dynamic Page Detection)...")
    
    # Allow CLI override
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = 'data/raw/Pillar3reports/consolidated-pillar-3-report.pdf'
        
    print(f"Target PDF: {pdf_path}")
    
    # OVERRIDE TEMPLATE_ROWS for Eurobank nuances (Q3 Short Labels)
    if 'OV1' in TEMPLATE_ROWS:
        TEMPLATE_ROWS['OV1']['29'] = ('Total', '2520220')
        TEMPLATE_ROWS['OV1']['1'] = ('Credit risk', '2520201') 
        TEMPLATE_ROWS['OV1']['24'] = ('Operational risk', '2520215')
        TEMPLATE_ROWS['OV1']['20'] = ('Market risk', '2520210')
        TEMPLATE_ROWS['OV1']['6'] = ('Counterparty credit risk', '2520206')
    
    targets = ['KM1', 'CC1', 'OV1', 'KM2', 'LR1', 'LR2', 'CR1', 'CR3', 'CQ1', 'CCR1', 'LIQ1']
    
    total_saved = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        dynamic_map = scan_index_pages(pdf)
        
        fallback_defaults = {
            'KM1': [20], 'CC1': [113, 114, 115], 'OV1': [27, 28, 29], 
            'CQ1': [30], 'CR1': [31], 'CR3': [37], 'CCR1': [48], 'LIQ1': [55],
            'KM2': [20, 51, 113], 'LR1': [51, 153], 'LR2': [51, 154]
        }
        
        final_map = {}
        for t in targets:
            pages = dynamic_map.get(t, [])
            if not pages:
                pages = fallback_defaults.get(t, [])
            final_map[t] = pages
            
        print(f"Final Page Map: {final_map}")

        print(f"Scanning {len(pdf.pages)} pages...")
        
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            
            should_process_templates = [t for t, pages in final_map.items() if page_num in pages]
            
            # Use Reconstruction ONLY for known fragmented templates (OV1)
            # For others (KM1), standard extraction works better.
            if 'OV1' in should_process_templates:
                text = reconstruct_page_text(page)
            else:
                text = page.extract_text() or ""
            
            # Check for range matching (Window +1)
            # e.g. If OV1 is Page 25, we process 25. The window logic below adds redundancy.
            # But the reconstruction logic above already fired.
            # We simply check if we should parse.
            
            current_page_templates = []
            for code, target_pages in final_map.items():
                for p in target_pages:
                    if page_num >= p and page_num <= p + 1:
                        current_page_templates.append(code)
            
            current_page_templates = list(set(current_page_templates))
            
            for code in current_page_templates:
                # Use multiplier 1,000,000 (Millions) for Eurobank
                rows = parse_text_rows(text, code, multiplier=1000000.0)
                
                if rows:
                    mapped_count = sum(1 for r in rows if r['eba_item_id'])
                    print(f"  Page {page_num}: Found {len(rows)} items ({mapped_count} mapped) for {code}")
                    for r in rows:
                        r['template'] = code
                    
                    saved = save_eurobank_data(rows, page_num, pdf_path)
                    total_saved += saved

    print(f"Eurobank Patch Complete. Total items saved: {total_saved}")

if __name__ == "__main__":
    patch_eurobank()
