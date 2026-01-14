"""
Pillar 3 PDF Batch Parser (Enhanced v2)
========================================
Features:
- Filename normalization and metadata extraction
- Report-type aware thresholds (H1/FY vs Q1/Q3)
- Dynamic table detection from PDF index
- Eurobank-style geometric reconstruction fallback
- Improved LIQ1 parsing with unit detection
- Comprehensive logging and summary report
"""

import os
import sys
import re
import sqlite3
import pdfplumber
import pandas as pd
from datetime import datetime
from operator import itemgetter

# Add scripts to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eba_benchmarking.ingestion.parsers.common import TEMPLATE_ROWS, parse_text_rows, clean_number
try:
    from eba_benchmarking.ingestion.parsers.ocr_utils import is_ocr_available, extract_text_from_image
except ImportError:
    is_ocr_available = lambda: False
    extract_text_from_image = lambda x: ""

from eba_benchmarking.config import DB_NAME, ROOT_DIR

# Configuration
DB_PATH = DB_NAME
RAW_DATA_DIR = os.path.join(ROOT_DIR, 'data', 'raw', 'Pillar3reports')
REPORT_DIR = os.path.join(ROOT_DIR, 'data', 'output')

# Expected template structure for FULL YEAR / H1 reports
EXPECTED_TEMPLATES_FULL = {
    'KM1': (15, True),   # Key Metrics - Critical
    'CC1': (20, True),   # Capital Composition - Critical
    'OV1': (10, True),   # RWA Overview - Critical
    'LR1': (5, False),   # Leverage Ratio
    'LR2': (3, False),   # Leverage Ratio
    'LR3': (5, False),   # Leverage Ratio
    'LIQ1': (8, True),   # Liquidity - Critical
    'LIQ2': (5, False),  # NSFR
    'CR1': (3, False),   # Credit Risk
    'CR3': (2, False),   # Credit Risk - SA exposures
    'CR4': (5, False),   # Credit Risk - IRB
    'CR5': (3, False),   # Credit Risk - CCR
    'CCR1': (2, False),  # Counterparty Credit Risk
    'KM2': (5, False),   # Key Metrics Part 2 (MREL)
    'IRRBB1': (5, True), # Interest Rate Risk in Banking Book - Critical
    'MR1': (3, False),   # Market Risk
    'MR2': (3, False),   # Market Risk Flow
    'CQ1': (3, False),   # Credit Quality
    'CQ7': (3, False),   # Asset Encumbrance
    'CC2': (2, False),   # Capital Reconciliation
}

# Expected template structure for Q1/Q3 reports (abbreviated)
EXPECTED_TEMPLATES_QUARTERLY = {
    'KM1': (10, True),   # Key Metrics - Critical
    'CC1': (10, False),  # Capital Composition - NOT critical for Q1/Q3
    'OV1': (6, True),    # RWA Overview - Critical
    'LR1': (3, False),   # Leverage Ratio
    'LR2': (2, False),   # Leverage Ratio
    'LR3': (3, False),   # Leverage Ratio
    'LIQ1': (5, True),   # Liquidity - Critical
    'LIQ2': (3, False),  # Liquidity
    'CR1': (2, False),   # Credit Risk
    'CR3': (1, False),   # Credit Risk
    'CCR1': (1, False),  # Counterparty Credit Risk
    'KM2': (3, False),   # Key Metrics Part 2
    'IRRBB1': (3, False), # Interest Rate Risk - may not be in all Q1/Q3 reports
}

# Bank identification patterns
# Format: (search_patterns, lei, common_filename_patterns)
BANK_CONFIG = {
    'NBG': {
        'text_patterns': ['NATIONAL BANK OF GREECE', 'NBG S.A.', 'NBG GROUP'],
        'filename_patterns': ['nbg', 'national-bank', 'pillar-3-q'],
        'lei': '5UMCZOEYKCVFAW8ZLO05',
    },
    'Alpha Bank': {
        'text_patterns': ['ALPHA BANK', 'ALPHA SERVICES', 'ALPHA HOLDINGS'],
        'filename_patterns': ['alpha', '20250930-pillar-III-disclosures'],
        'lei': 'NLPK02SGC0U1AABDLL56',
    },
    'Eurobank': {
        'text_patterns': ['EUROBANK', 'EUROBANK ERGASIAS', 'EUROBANK HOLDINGS'],
        'filename_patterns': ['eurobank', 'consolidated-pillar-3', 'Pillar-3-092025-Holdings'],
        'lei': 'JEUVK5RWVJEN8W0C9M24',
    },
    'Piraeus': {
        'text_patterns': ['PIRAEUS', 'PIRAEUS BANK', 'PIRAEUS FINANCIAL'],
        'filename_patterns': ['piraeus', 'Pillar_III_EN'],
        'lei': '213800OYHR4PPVA77574',
    },
    'Bank of Cyprus': {
        'text_patterns': ['BANK OF CYPRUS', 'BOC PCL'],
        'filename_patterns': ['cyprus', 'boc'],
        'lei': '635400L14KNHJ3DMBX37',
    },
}


class FileMetadata:
    """Normalized file metadata."""
    def __init__(self):
        self.bank_name = "Unknown"
        self.lei = None
        self.period = None
        self.report_type = "quarterly"  # 'full' (H1/FY) or 'quarterly' (Q1/Q3)
        self.quarter = None  # Q1, Q2, Q3, Q4
        self.year = None
        self.original_filename = None
        self.normalized_name = None


class ParserLogger:
    """Handles logging for the parsing process."""
    def __init__(self):
        self.logs = []
        self.warnings = []
        self.errors = []
        self.stats = {
            'files_processed': 0,
            'files_failed': 0,
            'total_items_extracted': 0,
            'total_items_mapped': 0,
            'templates_found': {},
            'fallback_used': 0,
            'file_gaps': {},  # Normalized name -> [missing templates]
        }
        
    def info(self, msg):
        self.logs.append(f"[INFO] {msg}")
        print(f"  {msg}")
        
    def warn(self, msg):
        self.warnings.append(f"[WARN] {msg}")
        print(f"  ⚠ {msg}")
        
    def error(self, msg):
        self.errors.append(f"[ERROR] {msg}")
        print(f"  ✗ {msg}")
        
    def success(self, msg):
        self.logs.append(f"[OK] {msg}")
        print(f"  ✓ {msg}")


def normalize_file_metadata(filename, pdf_text=""):
    """
    Extract and normalize metadata from filename and PDF content.
    Returns a FileMetadata object with bank, period, report type, etc.
    """
    meta = FileMetadata()
    meta.original_filename = filename
    
    filename_lower = filename.lower()
    text_upper = pdf_text.upper()
    
    # ========== BANK DETECTION ==========
    for bank_name, config in BANK_CONFIG.items():
        # Check text patterns first (more reliable)
        for pattern in config['text_patterns']:
            if pattern in text_upper:
                meta.bank_name = bank_name
                meta.lei = config['lei']
                break
        
        if meta.bank_name != "Unknown":
            break
            
        # Fallback to filename patterns
        for pattern in config['filename_patterns']:
            if pattern.lower() in filename_lower:
                meta.bank_name = bank_name
                meta.lei = config['lei']
                break
    
    # ========== PERIOD DETECTION ==========
    # Check for quarter indicators
    q_match = re.search(r'[_-]?q([1-4])[_-]?(\d{4})?', filename_lower)
    if q_match:
        meta.quarter = f"Q{q_match.group(1)}"
        if q_match.group(2):
            meta.year = q_match.group(2)
    
    # Check for month/date patterns
    month_patterns = [
        (r'092025|09[-_]?2025|september.*2025', '2025-09-30', 'Q3', '2025'),
        (r'062025|06[-_]?2025|june.*2025|30.*june.*2025', '2025-06-30', 'Q2', '2025'),
        (r'032025|03[-_]?2025|march.*2025', '2025-03-31', 'Q1', '2025'),
        (r'122025|12[-_]?2025|december.*2025', '2025-12-31', 'Q4', '2025'),
        (r'092024|09[-_]?2024|september.*2024', '2024-09-30', 'Q3', '2024'),
        (r'062024|06[-_]?2024|june.*2024', '2024-06-30', 'Q2', '2024'),
    ]
    
    combined_text = filename_lower + " " + pdf_text.lower()
    for pattern, period, quarter, year in month_patterns:
        if re.search(pattern, combined_text):
            meta.period = period
            if not meta.quarter:
                meta.quarter = quarter
            if not meta.year:
                meta.year = year
            break
    
    # Default period if not detected
    if not meta.period:
        meta.period = '2025-06-30'
        meta.quarter = 'Q2'
        meta.year = '2025'
    
    # ========== REPORT TYPE DETECTION ==========
    # Q2 (H1) and Q4 (FY) are comprehensive, Q1 and Q3 are abbreviated
    if meta.quarter in ['Q2', 'Q4']:
        meta.report_type = 'full'
    else:
        meta.report_type = 'quarterly'
    
    # Check for explicit indicators in filename/text that override quarter-based detection
    full_indicators = ['annual', 'full year', 'fy ', 'interim', 'half year', 'h1 ', '6 months', 'six months']
    quarterly_indicators = ['q1 report', 'q3 report', 'three months', '3 months ended']
    
    for indicator in full_indicators:
        if indicator in combined_text:
            meta.report_type = 'full'
            break
    
    # Only override to quarterly if explicitly a Q1/Q3 quarterly report
    for indicator in quarterly_indicators:
        if indicator in combined_text and meta.quarter in ['Q1', 'Q3']:
            meta.report_type = 'quarterly'
            break
    
    # ========== NORMALIZED NAME ==========
    meta.normalized_name = f"{meta.bank_name}_{meta.quarter}_{meta.year}"
    
    return meta


def reconstruct_page_text(page):
    """
    Eurobank-style geometric reconstruction.
    Groups words by Y-coordinate and merges based on horizontal distance.
    """
    words = page.extract_words()
    if not words:
        return page.extract_text() or ""
        
    words.sort(key=itemgetter('top', 'x0'))
    
    lines = []
    current_line = []
    last_top = 0
    
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
    if current_line:
        lines.append(current_line)
    
    text_lines = []
    for line in lines:
        row_text = ""
        for i, w in enumerate(line):
            if i == 0:
                row_text += w['text']
                continue
            
            prev = line[i-1]
            dist = w['x0'] - prev['x1']
            
            if dist < 1.5:
                row_text += w['text']
            else:
                row_text += " " + w['text']
        
        row_text = re.sub(r'\s*([,.])\s*', r'\1', row_text)
        text_lines.append(row_text)
        
    return "\n".join(text_lines)


def detect_multiplier(page_text):
    """
    Detect the unit multiplier from page text.
    Returns multiplier value (1000 for thousands, 1000000 for millions, etc.)
    """
    text_lower = page_text.lower()
    
    # Check for unit indicators
    if "€ 000's" in page_text or "000's" in page_text or "(€ 000" in page_text:
        return 1000.0  # Thousands
    if "€ million" in text_lower or "€ mn" in text_lower or "(€ million" in text_lower:
        return 1000000.0  # Millions
    if "€ billion" in text_lower or "€ bn" in text_lower:
        return 1000000000.0  # Billions
    if "€m" in text_lower or "€ m" in text_lower:
        return 1000000.0  # Millions
    if "€000" in text_lower or "€ 000" in text_lower:
        return 1000.0  # Thousands
    
    # Default to millions (most common for Greek banks)
    return 1000000.0


def scan_index_pages(pdf, logger):
    """Scan first pages for table of contents / index of tables.
    Returns tuple: (page_map for expected templates, all_templates_detected)
    """
    page_map = {}  # For expected templates
    all_detected = {}  # For all templates found
    
    logger.info("Scanning Index of Tables...")
    
    combined_toc_text = ""
    for i in range(min(15, len(pdf.pages))):
        text = pdf.pages[i].extract_text() or ""
        combined_toc_text += text + "\n"
    
    # Known Pillar 3 template prefixes
    KNOWN_PREFIXES = ['KM', 'CC', 'OV', 'LR', 'LIQ', 'CR', 'CCR', 'CQ', 'MR', 'SEC', 'IRRBB', 'ESG', 'CMS', 'AE', 'OF', 'OR']
    
    # Extended regex patterns to find templates
    template_patterns = [
        r'EU\s*([A-Z]{2,6}\d+[a-z]?)',
        r'Table\s+\d+[:\s.]*(?:EU\s+)?([A-Z]{2,6}\d+[a-z]?)',
        r'\b([A-Z]{2,6}\d+[a-z]?)\s*[–:-]',
    ]
    
    target_codes = list(EXPECTED_TEMPLATES_FULL.keys())
    
    for line in combined_toc_text.split('\n'):
        line_clean = line.strip()
        
        # First check expected templates
        for code in target_codes:
            patterns = [f" {code} ", f" {code}-", f": {code} ", f":{code} ", f"EU {code}", f"EU-{code}"]
            if any(p in line_clean for p in patterns) and len(line_clean) > 10:
                parts = line_clean.split()
                last_part = parts[-1].replace('.', '').replace(',', '')
                if last_part.isdigit():
                    page_num = int(last_part)
                    if page_num < 500:  # Sanity check
                        if code not in page_map:
                            page_map[code] = []
                        if page_num not in page_map[code]:
                            page_map[code].append(page_num)
                            logger.info(f"  -> Detected {code} on Page {page_num}")
        
        # Also detect ALL templates (including those not in expected list)
        for pattern in template_patterns:
            matches = re.findall(pattern, line_clean, re.IGNORECASE)
            for match in matches:
                code = match.upper().strip()
                if any(code.startswith(prefix) for prefix in KNOWN_PREFIXES):
                    if len(code) >= 2 and len(code) <= 8:
                        parts = line_clean.split()
                        last_part = parts[-1].replace('.', '').replace(',', '') if parts else ""
                        if last_part.isdigit():
                            page_num = int(last_part)
                            if page_num < 500:  # Sanity check
                                if code not in all_detected:
                                    all_detected[code] = []
                                if page_num not in all_detected[code]:
                                    all_detected[code].append(page_num)
                                    # Also add to page_map if it's a known template
                                    if code in target_codes:
                                        if code not in page_map:
                                            page_map[code] = []
                                        if page_num not in page_map[code]:
                                            page_map[code].append(page_num)
    
    # Log additional templates found but not in expected list
    extra_templates = [code for code in all_detected if code not in target_codes]
    if extra_templates:
        logger.info(f"  Additional templates in index (not parsed): {', '.join(sorted(extra_templates))}")
    
    return page_map, all_detected



def validate_index(page_map, expected_templates, logger):
    """Validate if expected critical templates were found in the index."""
    missing_critical = []
    missing_optional = []
    
    for template, (min_items, is_critical) in expected_templates.items():
        if template not in page_map:
            if is_critical:
                missing_critical.append(template)
            else:
                missing_optional.append(template)
    
    if missing_critical:
        logger.warn(f"Missing CRITICAL templates in index: {missing_critical}")
    if missing_optional:
        logger.info(f"Missing optional templates in index: {missing_optional}")
    
    return len(missing_critical) == 0


def parse_text_lines_fallback(page_text, template_code, multiplier):
    """
    Fallback 2: Direct text line parsing with flexible pattern matching.
    Handles fragmented text where standard regex fails.
    This is a more aggressive line-by-line parser.
    """
    results = []
    
    # Template-specific patterns: label_patterns -> (row_id, eba_item_id)
    FALLBACK_PATTERNS = {
        'LIQ1': {
            'high-quality liquid assets': ('1', '2520911'),
            'hqla': ('1', '2520911'),
            'total cash outflow': ('EU-19a', '2520922'),
            'cash outflow': ('EU-19a', '2520922'),
            'net cash outflow': ('21', '2520924'),
            'liquidity buffer': ('22', '2520925'),
            'liquidity coverage ratio': ('23', '2520926'),
            'lcr (%)': ('23', '2520926'),
        },
        'KM1': {
            'common equity tier 1': ('1', '2520102'),
            'cet1 capital': ('1', '2520102'),
            'tier 1 capital': ('2', '2520107'),
            'total capital': ('3', '2520112'),
            'total risk exposure': ('4', '2520116'),
            'cet1 ratio': ('5', '2520140'),
            'tier 1 ratio': ('6', '2520141'),
            'total capital ratio': ('7', '2520142'),
            'leverage ratio': ('13', '2520143'),
        },
        'OV1': {
            'credit risk': ('1', '2520201'),
            'counterparty credit risk': ('6', '2520206'),
            'market risk': ('20', '2520210'),
            'operational risk': ('24', '2520215'),
            'total': ('29', '2520220'),
        },
        'CC1': {
            'capital instruments': ('1', '2520103'),
            'retained earnings': ('2', '2520104'),
            'share premium': ('1', '2520103'),
            'minority interests': ('5', None),
            'cet1 capital before': ('28', '2520110'),
        },
        'IRRBB1': {
            'parallel up': ('1', None),
            'parallel down': ('2', None),
            'steepener': ('3', None),
            'flattener': ('4', None),
            'short rates up': ('5', None),
            'short rates down': ('6', None),
        },
    }
    
    patterns = FALLBACK_PATTERNS.get(template_code, {})
    
    # If no manual patterns, try to generate them from TEMPLATE_ROWS
    if not patterns and template_code in TEMPLATE_ROWS:
        row_defs = TEMPLATE_ROWS[template_code]
        for r_id, (r_label, eba_id) in row_defs.items():
            # Create a simple lowercase keyword from the label
            # e.g. "Common Equity Tier 1" -> "common equity tier 1"
            # Remove ( ) for cleaner matching
            clean_lbl = r_label.lower().replace('(', '').replace(')', '').replace('-', ' ').strip()
            if len(clean_lbl) > 5: # Avoid very short generic labels
                patterns[clean_lbl] = (r_id, eba_id)
                
    if not patterns:
        return results
        
    # Sort patterns by length (longest first) to match more specific labels first
    # e.g. "Total capital ratio" should match before "Total capital"
    sorted_patterns = sorted(patterns.items(), key=lambda x: len(x[0]), reverse=True)
    
    lines = page_text.split('\n')
    
    for line in lines:
        line_lower = line.lower().strip()
        
        for pattern, (row_id, eba_id) in sorted_patterns:
            # Stricter matching for short patterns
            if len(pattern) < 15:
                # Require word boundaries for short patterns
                match_obj = re.search(r'\b' + re.escape(pattern) + r'\b', line_lower)
            else:
                match_obj = pattern in line_lower

            if match_obj:
                # Find start position of the label to ignore preceding numbers
                if isinstance(match_obj, re.Match):
                    label_start = match_obj.start()
                    text_to_search = line[label_start:]
                else:
                    label_start = line_lower.find(pattern)
                    text_to_search = line[label_start:]

                # Found a matching pattern - now extract numbers from the remaining text
                # Look for number patterns: 123, -123, (123)
                numbers = re.findall(r'(?:-?\d[\d,.]*|\(\d[\d,.]*\))', text_to_search)
                
                if numbers:
                    # Take the first substantial number (skip row numbers like "1", "2")
                    for num_str in numbers:
                        try:
                            value = clean_number(num_str)
                            if value is None:
                                continue
                            
                            # Skip if it's likely just a row number (small integer)
                            # But keep if it matches our expected negative formatting or has decimals
                            if abs(value) < 100 and '.' not in num_str and '(' not in num_str and '-' not in num_str:
                                continue
                            
                            # Apply multiplier
                            # Robust ratio detection
                            is_ratio = (
                                "%" in num_str or 
                                "ratio" in line.lower() or 
                                "percentage" in line.lower() or 
                                (template_code == 'KM1' and row_id in ['5', '6', '7', '13', '14', '15']) or
                                (template_code == 'LIQ1' and row_id == '23') or
                                (abs(value) < 1.0 and value != 0) # Small float without units
                            )
                            
                            # Ratio detection logic
                            is_ratio = (
                                "%" in num_str or 
                                "ratio" in line.lower() or 
                                "percentage" in line.lower() or
                                (abs(value) < 1.0 and value != 0) # Small float without units
                            )
                            
                            if template_code == 'IRRBB1':
                                is_ratio = False 
                                
                            # KM1 specifics: amounts vs ratios
                            if template_code == 'KM1':
                                km1_amount_rows = ['1', '2', '3', '4', '4a', '13', '15', '17', '19']
                                km1_ratio_rows = ['5', '5b', '6', '6b', '7', '7b', '8', '9', '10', '11', '12', '14', '14a', '14b', '14c', '14d', '14e', '16', '18', '20', '21', '23']
                                
                                # Exact match or starts with if handling sub-rows
                                rid_clean = row_id.strip().lower()
                                if rid_clean in km1_ratio_rows:
                                    is_ratio = True
                                elif rid_clean in km1_amount_rows:
                                    is_ratio = False
                                    
                            # KM2 specifics: amounts vs ratios
                            if template_code == 'KM2':
                                km2_amount_rows = ['1', 'EU-1a', '2', '4', '7']
                                km2_ratio_rows = ['3', '5', '6', '8']
                                rid_clean = row_id.strip().lower()
                                if rid_clean in km2_ratio_rows:
                                    is_ratio = True
                                elif rid_clean in km2_amount_rows:
                                    is_ratio = False
                                    
                            if not is_ratio:
                                value *= multiplier
                            elif abs(value) > 1.0 and "%" not in num_str:
                                # Normalize ratio (e.g. 15.5 -> 0.155) if it's clearly a % but lacks sign
                                # Greek metrics are rarely > 100% (except Liquidity ones which we handle later)
                                if abs(value) > 1.0 and abs(value) < 100:
                                    value /= 100.0
                            elif abs(value) < 1.0 and "%" in num_str:
                                pass
                            
                            results.append({
                                'row_id': row_id,
                                'row_label': line[:50].strip(),
                                'raw_label': line[:80].strip(),
                                'value': value,
                                'eba_item_id': eba_id,
                                'is_new': 0 if eba_id else 1,
                                'dimension_name': 'EVE' if template_code == 'IRRBB1' else 'Default'
                            })
                            
                            # --- IRRBB1 SPECIAL HANDLING FOR NII (Column 3) ---
                            if template_code == 'IRRBB1' and row_id in ['1', '2']: # Parallel up/down
                                # Try to find the 3rd valid number for NII
                                # We need to collect ALL valid numbers first to be safe
                                valid_values = []
                                for ns in numbers:
                                    v = clean_number(ns)
                                    if v is not None and not ((str(int(v)) == str(row_id)) or (v > 0 and v < 10 and '.' not in ns)):
                                         valid_values.append(v)
                                
                                if len(valid_values) >= 3:
                                    nii_val = valid_values[2] # 0=EVE Curr, 1=EVE Last, 2=NII Curr
                                    nii_val *= multiplier # NII is always an amount
                                    
                                    nii_id_map = {'1': '2525011', '2': '2525012'} # Parallel Up / Down
                                    
                                    results.append({
                                        'row_id': f"EU-{row_id}", # e.g. EU-1
                                        'row_label': f"{line[:30].strip()} (NII)",
                                        'raw_label': line[:80].strip(),
                                        'value': nii_val,
                                        'eba_item_id': nii_id_map.get(row_id),
                                        'is_new': 0,
                                        'dimension_name': 'NII'
                                    })
                            
                            break  # Found a value, move to next pattern
                        except ValueError:
                            continue
                break  # Found this pattern, don't check other patterns for this line
    
    return results


def parse_liq1_table(page, multiplier, logger):
    """
    Special parser for LIQ1 tables which often have complex multi-column layouts.
    Returns list of parsed rows.
    """
    results = []
    
    # Try table extraction
    tables = page.extract_tables()
    if not tables:
        return results
    
    # LIQ1 key items we're looking for
    liq1_items = {
        'Total high-quality liquid assets': ('1', '2520911'),
        'Total HQLA': ('1', '2520911'),
        'HQLA': ('1', '2520911'),
        'Total cash outflows': ('EU-19a', '2520922'),
        'Cash outflows': ('EU-19a', '2520922'),
        'Net cash outflows': ('21', '2520924'),
        'Liquidity buffer': ('22', '2520925'),
        'Total net cash outflows': ('21', '2520924'),
        'Liquidity Coverage Ratio': ('23', '2520926'),
        'LCR': ('23', '2520926'),
    }
    
    for table in tables:
        if not table:
            continue
            
        for row in table:
            if not row or len(row) < 2:
                continue
            
            # Find label cell
            label_cell = None
            value_cell = None
            
            for i, cell in enumerate(row):
                if cell and isinstance(cell, str):
                    cell_clean = cell.strip()
                    
                    # Check if this looks like a label
                    for pattern, (row_id, eba_id) in liq1_items.items():
                        if pattern.lower() in cell_clean.lower():
                            label_cell = (cell_clean, row_id, eba_id)
                            # Look for value in subsequent cells
                            for j in range(i+1, len(row)):
                                if row[j]:
                                    val = clean_number(row[j])
                                    if val is not None:
                                        value_cell = val * multiplier
                                        break
                            break
            
            if label_cell and value_cell:
                results.append({
                    'row_id': label_cell[1],
                    'row_label': label_cell[0][:50],
                    'raw_label': label_cell[0][:50],
                    'value': value_cell,
                    'eba_item_id': label_cell[2],
                    'is_new': 0,
                    'dimension_name': 'Default'
                })
    
    return results


def parse_pdf_file(pdf_path, logger):
    """Parse a single PDF file with validation and fallback."""
    filename = os.path.basename(pdf_path)
    logger.info(f"Processing: {filename}")
    
    results = []
    templates_parsed = {}
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Get first few pages for metadata
            first_text = ""
            for i in range(min(5, len(pdf.pages))):
                first_text += pdf.pages[i].extract_text() or ""
            
            # Normalize metadata
            meta = normalize_file_metadata(filename, first_text)
            
            logger.info(f"Bank: {meta.bank_name}, Period: {meta.period}, Type: {meta.report_type}")
            logger.info(f"Normalized: {meta.normalized_name}")
            
            # Select appropriate thresholds
            if meta.report_type == 'full':
                expected_templates = EXPECTED_TEMPLATES_FULL
            else:
                expected_templates = EXPECTED_TEMPLATES_QUARTERLY
            
            # Scan index
            page_map, all_detected = scan_index_pages(pdf, logger)

            # Record template gaps (detected in index but not in our expected/parsed list)
            gaps = [code for code in all_detected if code not in page_map]
            if gaps:
                logger.stats['file_gaps'][meta.normalized_name] = gaps
                logger.info(f"  Gap templates (detected but not parsed): {', '.join(sorted(gaps))}")

            if not page_map:
                logger.warn("No templates detected in index - using fallback page scan")
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    for code in expected_templates.keys():
                        if f" {code} " in page_text or f":{code}" in page_text or f"EU {code}" in page_text:
                            if code not in page_map:
                                page_map[code] = []
                            if (i+1) not in page_map[code]:
                                page_map[code].append(i+1)
            
            validate_index(page_map, expected_templates, logger)
            
            # Process each page
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                
                # Determine which templates to try on this page
                templates_to_try = []
                for code, pages in page_map.items():
                    for p in pages:
                        if page_num >= p and page_num <= p + 2:  # Window of 3 pages
                            templates_to_try.append(code)
                
                templates_to_try = list(set(templates_to_try))
                if not templates_to_try:
                    continue
                
                # Standard extraction
                page_text = page.extract_text() or ""
                
                # Detect multiplier for this page
                multiplier = detect_multiplier(page_text)
                
                for code in templates_to_try:
                    rows = []
                    
                    # Special handling for LIQ1
                    if code == 'LIQ1':
                        rows = parse_liq1_table(page, multiplier, logger)
                        if rows:
                            logger.info(f"  Page {page_num}: LIQ1 table parser found {len(rows)} items")
                    
                    # Standard text parsing
                    if not rows:
                        rows = parse_text_rows(page_text, code, multiplier)
                    
                    mapped_count = sum(1 for r in rows if r.get('eba_item_id'))
                    
                    # Check if we need fallbacks
                    min_expected = expected_templates.get(code, (3, False))[0]
                    
                    # FALLBACK 1: Geometric reconstruction (Eurobank-style)
                    if mapped_count < min_expected // 2:
                        reconstructed_text = reconstruct_page_text(page)
                        fallback_rows = parse_text_rows(reconstructed_text, code, multiplier)
                        fallback_mapped = sum(1 for r in fallback_rows if r.get('eba_item_id'))
                        
                        if fallback_mapped > mapped_count:
                            logger.info(f"  Page {page_num}: Fallback 1 (geometric) improved {code} from {mapped_count} to {fallback_mapped} items")
                            rows = fallback_rows
                            mapped_count = fallback_mapped
                            logger.stats['fallback_used'] += 1
                    
                    # FALLBACK 2: Direct text line parsing (for fragmented text)
                    if mapped_count < min_expected // 2:
                        fallback2_rows = parse_text_lines_fallback(page_text, code, multiplier)
                        fallback2_mapped = sum(1 for r in fallback2_rows if r.get('eba_item_id'))
                        
                        if fallback2_mapped > mapped_count:
                            logger.info(f"  Page {page_num}: Fallback 2 (line parsing) improved {code} from {mapped_count} to {fallback2_mapped} items")
                            rows = fallback2_rows
                            mapped_count = fallback2_mapped
                            logger.stats['fallback_used'] += 1

                    
                    # FALLBACK 3: OCR (if available)
                    if mapped_count < min_expected // 2 and is_ocr_available():
                        # Crop page to just text content if needed, but full page is safer for now
                        try:
                            # PdfPlumber page.to_image() returns a PageImage object
                            # We use resolution=300 for better OCR
                            page_image = page.to_image(resolution=300)
                            ocr_text = extract_text_from_image(page_image)
                            
                            if ocr_text and len(ocr_text) > 100:
                                fallback3_rows = parse_text_rows(ocr_text, code, multiplier)
                                fallback3_mapped = sum(1 for r in fallback3_rows if r.get('eba_item_id'))

                                if fallback3_mapped > mapped_count:
                                    logger.info(f"  Page {page_num}: Fallback 3 (OCR) improved {code} from {mapped_count} to {fallback3_mapped} items")
                                    rows = fallback3_rows
                                    mapped_count = fallback3_mapped
                                    logger.stats['fallback_used'] += 1
                        except Exception as e:
                            logger.warn(f"OCR failed for page {page_num}: {e}")

                    if rows:
                        for r in rows:
                            r['bank_name'] = meta.bank_name
                            r['lei'] = meta.lei
                            r['period'] = meta.period
                            r['template'] = code
                            r['source_page'] = page_num
                            r['source_file'] = filename
                        
                        results.extend(rows)
                        
                        if code not in templates_parsed:
                            templates_parsed[code] = 0
                        templates_parsed[code] += len(rows)
            
            # Validate extraction results
            for code, (min_expected, is_critical) in expected_templates.items():
                found = templates_parsed.get(code, 0)
                if found < min_expected:
                    if is_critical and found == 0:
                        logger.error(f"CRITICAL: {code} not extracted (expected {min_expected}+)")
                    elif found > 0:
                        logger.warn(f"{code}: Only {found} items (expected {min_expected}+)")
                else:
                    logger.success(f"{code}: {found} items extracted")
            
            logger.stats['templates_found'][filename] = templates_parsed
            
    except Exception as e:
        import traceback
        logger.error(f"Failed to process {filename}: {str(e)}")
        logger.error(traceback.format_exc())
        logger.stats['files_failed'] += 1
        return []
    
    logger.stats['files_processed'] += 1
    logger.stats['total_items_extracted'] += len(results)
    logger.stats['total_items_mapped'] += sum(1 for r in results if r.get('eba_item_id'))
    
    return results


def save_results(results, logger):
    """Save parsed results to database."""
    if not results:
        logger.warn("No results to save")
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    count = 0
    
    for r in results:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO facts_pillar3 
                (lei, period, template_code, table_title, row_id, row_label, raw_label, 
                 amount, eba_item_id, is_new_metric, source_page, bank_name, dimension_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get('lei'),
                r.get('period'),
                r.get('template'),
                r.get('source_file', 'Batch Parser'),
                r.get('row_id'),
                r.get('row_label'),
                r.get('raw_label', ''),
                r.get('value'),
                r.get('eba_item_id'),
                r.get('is_new', 0),
                r.get('source_page'),
                r.get('bank_name'),
                r.get('dimension_name', 'Default')
            ))
            count += 1
        except Exception as e:
            logger.error(f"DB insert error: {e}")
    
    conn.commit()
    conn.close()
    
    return count


def generate_report(logger, saved_count):
    """Generate summary report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORT_DIR, f'parsing_report_{timestamp}.txt')
    
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    report = []
    report.append("=" * 70)
    report.append("PILLAR 3 PARSING SUMMARY REPORT (v2)")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 70)
    
    report.append(f"\nFiles Processed: {logger.stats['files_processed']}")
    report.append(f"Files Failed: {logger.stats['files_failed']}")
    report.append(f"Total Items Extracted: {logger.stats['total_items_extracted']}")
    report.append(f"Total Items Mapped to EBA: {logger.stats['total_items_mapped']}")
    report.append(f"Fallback (Geometric) Used: {logger.stats['fallback_used']} times")
    report.append(f"Items Saved to DB: {saved_count}")
    
    # ----------------------------------------------------------------------
    # TEMPLATE GAPS SECTION
    # ----------------------------------------------------------------------
    report.append("\n" + "-" * 70)
    report.append("TEMPLATE GAPS IDENTIFIED (Detected in Index but NOT Parsed):")
    report.append("-" * 70)
    
    if logger.stats['file_gaps']:
        for file_name, gaps in logger.stats['file_gaps'].items():
            if gaps:
                report.append(f"\n{file_name}:")
                report.append(f"  Gap Templates: {', '.join(sorted(gaps))}")
    else:
        report.append("\nNo gaps detected.")

    report.append("\n" + "-" * 70)
    report.append("EXTRACTION BY FILE:")
    report.append("-" * 70)
    
    for filename, templates in logger.stats['templates_found'].items():
        report.append(f"\n{filename}:")
        for template, count in sorted(templates.items()):
            report.append(f"  {template}: {count} items")
    
    if logger.warnings:
        report.append("\n" + "-" * 70)
        report.append("WARNINGS:")
        report.append("-" * 70)
        for w in logger.warnings[:20]:  # Limit to 20
            report.append(w)
        if len(logger.warnings) > 20:
            report.append(f"... and {len(logger.warnings) - 20} more warnings")
    
    if logger.errors:
        report.append("\n" + "-" * 70)
        report.append("ERRORS:")
        report.append("-" * 70)
        for e in logger.errors[:20]:  # Limit to 20
            report.append(e)
    
    report.append("\n" + "=" * 70)
    report.append("END OF REPORT")
    report.append("=" * 70)
    
    report_content = "\n".join(report)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print("\n" + report_content)
    print(f"\nReport saved to: {report_path}")
    
    return report_path


def main():
    """Main entry point."""
    print("=" * 70)
    print("PILLAR 3 BATCH PARSER (Enhanced v2 with Report-Type Awareness)")
    print("=" * 70)
    
    logger = ParserLogger()
    
    # Find all PDF files
    pdf_files = []
    for f in os.listdir(RAW_DATA_DIR):
        if f.endswith('.pdf'):
            pdf_files.append(os.path.join(RAW_DATA_DIR, f))
    
    print(f"\nFound {len(pdf_files)} PDF files to process")
    
    all_results = []
    
    for pdf_path in sorted(pdf_files):
        print("\n" + "-" * 50)
        results = parse_pdf_file(pdf_path, logger)
        all_results.extend(results)
    
    print("\n" + "=" * 70)
    print("SAVING RESULTS TO DATABASE")
    print("=" * 70)
    
    saved_count = save_results(all_results, logger)
    print(f"Saved {saved_count} records to database")
    
    # Export to CSV
    export_csv(logger)
    
    # Generate report
    generate_report(logger, saved_count)


def export_csv(logger):
    """Export all Pillar 3 data to CSV."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(REPORT_DIR, f'facts_pillar3_{timestamp}.csv')
    
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    query = """
        SELECT 
            bank_name,
            lei,
            period,
            template_code,
            row_id,
            row_label,
            amount,
            eba_item_id,
            is_new_metric,
            source_page,
            table_title as source_file
        FROM facts_pillar3
        ORDER BY bank_name, period, template_code, CAST(row_id AS INTEGER)
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    df.to_csv(csv_path, index=False)
    
    print(f"\n{'='*70}")
    print("CSV EXPORT")
    print(f"{'='*70}")
    print(f"Exported {len(df)} records to: {csv_path}")
    
    # Also export a "latest" version for easy access
    latest_path = os.path.join(REPORT_DIR, 'facts_pillar3_latest.csv')
    df.to_csv(latest_path, index=False)
    print(f"Also saved as: {latest_path}")
    
    logger.info(f"CSV exported: {len(df)} records")
    
    return csv_path


if __name__ == "__main__":
    main()
