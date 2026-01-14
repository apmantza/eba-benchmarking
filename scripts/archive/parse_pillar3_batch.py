"""
Pillar III Batch Parser - Version 5
Auto-detects bank name and reporting period from PDF content.
Parses all PDFs in a directory and stores to database.

Usage:
    python scripts/parse_pillar3_batch.py --dir data/raw/Pillar3reports
    python scripts/parse_pillar3_batch.py --pdf specific_report.pdf
"""

import os
import re
import argparse
import sqlite3
import pandas as pd
import pdfplumber
from datetime import datetime
from pathlib import Path

# Get the script directory and set paths
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR.parent / 'eba_data.db'

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
    'Bank of Cyprus': ('635400L14KNHZXPUZM19', 'Bank of Cyprus'),
}

# Period patterns to detect from PDF text
PERIOD_PATTERNS = [
    r'(?:as at|as of|date|period)[:\s]+(\d{1,2})[\.\/\s]*(June|Jun|06)[\.\/\s]*(\d{4})',
    r'(\d{1,2})[\.\/\s]*(June|Jun|06)[\.\/\s]*(\d{4})',
    r'(June|Jun)[\.\/\s]*(\d{1,2})[,\s]*(\d{4})',
    r'(\d{4})[-\/]06[-\/](\d{1,2})',
    r'30\.06\.(\d{4})',
    r'30/06/(\d{4})',
    r'Q2\s*(\d{4})',
    r'H1\s*(\d{4})',
    r'(\d{2})\.(\d{2})\.(\d{4})',
]

# Template definitions with verified EBA mappings
TEMPLATE_ROWS = {
    'KM1': {
        '1': ('Common Equity Tier 1', '2520102'),
        '2': ('Tier 1 capital', '2520133'),
        '3': ('Total capital', '2520101'),
        '4': ('Total risk exposure amount', '2520138'),
        '4a': ('Total risk exposure pre-floor', '2520154'),
        '5': ('Common Equity Tier 1 ratio', '2520146'),
        '5b': ('Common Equity Tier 1 ratio', '2520146'),
        '6': ('Tier 1 ratio', '2520147'),
        '6b': ('Tier 1 ratio', '2520147'),
        '7': ('Total capital ratio', '2520148'),
        '7b': ('Total capital ratio', '2520148'),
        '8': ('Capital conservation buffer', None),
        '9': ('Countercyclical capital buffer', None),
        '11': ('Combined buffer requirement', None),
        '13': ('Leverage ratio total exposure measure', '2520903'),
        '14': ('Leverage ratio', '2520905'),
        '15': ('Total HQLA', None),
        '17': ('Liquidity coverage ratio (%)', '2521101'),
        '18': ('Total available stable funding', '2521102'),
        '19': ('Total required stable funding', '2521103'),
        '20': ('NSFR ratio (%)', '2521104'),
    },
    'KM2': {
        '1': ('Own funds and eligible liabilities', None),
        'EU-1a': ('Own Funds', '2520101'),
        '2': ('Total RWA', '2520138'),
        '3': ('MREL ratio (% of RWA)', None),
        '4': ('Total exposure measure', '2520903'),
        '5': ('MREL ratio (% of TEM)', None),
        '6': ('Combined buffer requirement (%)', None),
        '7': ('Subordinate liabilities', None),
        '8': ('Percentage of subordinate liabilities', None),
    },
    'CC1': {
        '1': ('Capital instruments and the related share premium accounts', '2520103'),
        '2': ('Retained earnings', '2520104'),
        '3': ('Accumulated other comprehensive income', '2520105'),
        '4': ('Other reserves', '2520106'),
        'EU-3a': ('Funds for general banking risk', '2520107'),
        '5': ('Minority interests', '2520108'),
        '5a': ('Independently reviewed interim profits net of foreseeable charges or dividends', None),
        '6': ('Common Equity Tier 1 (CET1) capital before regulatory adjustments', None),
        '7': ('Additional value adjustments', '2520109'),
        '8': ('Intangible assets', '2520110'),
        '10': ('Deferred tax assets that rely on future profitability', '2520111'),
        '29': ('Common Equity Tier 1', '2520102'),
        '30': ('Additional Tier 1', '2520129'),
        '36': ('Additional Tier 1 (AT1) capital before regulatory adjustments', '2520128'),
        '44': ('Tier 1 capital', '2520133'),
        '45': ('Tier 2 instruments', '2520135'),
        '58': ('Total capital', '2520101'),
        '59': ('Total risk exposure amount', '2520138'),
        '60': ('Common Equity Tier 1 ratio', '2520140'),
        '61': ('Tier 1 ratio', '2520141'),
        '62': ('Total capital ratio', '2520142'),
    },
    'CC2': {
        '1': ('Total Assets per FS', None),
        '2': ('Total Liabilities per FS', None),
        '3': ('Total Equity per FS', None),
    },
    'OV1': {
        '1': ('Credit Risk excl CCR', '2520201'),
        '2': ('Of which SA', '2520202'),
        '3': ('Of which FIRB', '2520203'),
        '4': ('Of which Slotting', '2520204'),
        '5': ('Of which Equities IRB', '2520205'),
        '6': ('Counterparty Credit Risk', '2520206'),
        '7': ('CCR SA-CCR', None),
        '10': ('CVA Risk', '2520207'),
        '15': ('Settlement Risk', '2520208'),
        '16': ('Securitisation Banking Book', '2520209'),
        '20': ('Position FX Commodities Risk', '2520210'),
        '21': ('Market Risk SA', '2520211'),
        '22': ('Market Risk IMA', '2520212'),
        '23': ('Operational Risk', '2520215'),
        '24': ('Operational Risk', '2520215'),
        '25': ('Operational Risk SA', '2520217'),
        '29': ('Total RWA', '2520220'),
    },
    'LR1': {
        '1': ('Total assets per FS', None),
        '13': ('Leverage Ratio Exposure', '2520903'),
    },
    'LR2': {
        '13': ('Total On-Balance Sheet Exposures', None),
        '20': ('Leverage Ratio', '2520905'),
        '21': ('Leverage Ratio excl CB Deposits', None),
        '23': ('Tier 1 capital', '2520133'),
        '24': ('Total exposure measure', '2520903'),
    },
    'LR3': {
        '1': ('Total assets per FS', None),
        '13': ('Leverage Ratio Exposure', '2520903'),
    },
    'LIQ1': {
        '1': ('Total HQLA', None),
        '2': ('Retail deposits', None),
        '3': ('Stable deposits', None),
        '4': ('Less stable deposits', None),
        '5': ('Unsecured wholesale funding', None),
        '16': ('Total Cash Outflows', None),
        '19': ('Total Cash Inflows', None),
        '21': ('LCR HQLA', '2520401'),
        '22': ('Total Net Cash Outflows', '2520402'),
        '23': ('LCR Ratio', '2520403'),
    },
    'LIQ2': {
        '1': ('Capital items', None),
        '2': ('Own funds', None),
        '12': ('Total ASF', None),
        '13': ('Total HQLA for NSFR', None),
        '26': ('Total RSF', None),
        '27': ('NSFR Ratio', '2520404'),
    },
    'IRRBB1': {
        '1': ('Parallel up', None),
        '2': ('Parallel down', None),
        '3': ('Steepener', None),
        '4': ('Flattener', None),
        '5': ('Short rates up', None),
        '6': ('Short rates down', None),
    },
    'CR1': {
        '1': ('Loans and advances', '2520603'),
        '2': ('Debt securities', '2520602'),
        '3': ('Off-balance sheet', '2520606'),
        'Total': ('Total gross carrying amount', '2520601'),
    },
    'CR2': {
        '1': ('Initial stock of NPLs', '2520611'),
        '2': ('Inflows to non-performing portfolios', None),
        '3': ('Outflows due to write-offs', '2520612'),
        '4': ('Outflows due to other situations', None),
        '5': ('Outflows due to cure', None),
        '6': ('Final stock of NPLs', '2520613'),
    },
    'CR3': {
        '1': ('Exposures unsecured', '2520621'),
        '2': ('Exposures secured', '2520622'),
        '3': ('Of which: secured by collateral', None),
        '4': ('Of which: secured by financial guarantees', None),
        '5': ('Of which: secured by credit derivatives', None),
    },
    'CR4': {
        '1': ('Central governments or central banks', None),
        '2': ('Regional governments or local authorities', None),
        '3': ('Public sector entities', None),
        '4': ('Multilateral development banks', None),
        '5': ('International organisations', None),
        '6': ('Institutions', None),
        '7': ('Corporates', None),
        '8': ('Of which: SME', None),
        '9': ('Retail', None),
        '10': ('Of which: SME', None),
        '11': ('Secured by mortgages on immovable property', None),
        '12': ('Of which: SME', None),
        '13': ('Exposures in default', None),
        '14': ('Items associated with particularly high risk', None),
        '15': ('Covered bonds', None),
        '16': ('Claims on institutions and corporates with short-term rating', None),
        '17': ('Collective investment undertakings', None),
        '18': ('Equity exposures', None),
        '19': ('Other exposures', None),
        'Total': ('Total', '2520521'),
    },
    'CR5': {
        '1': ('Centrally cleared SA-CCR', None),
        '2': ('Bilateral SA-CCR', None),
        '3': ('Centrally cleared IMM', None),
        '4': ('Bilateral IMM', None),
        'Total': ('Total', None),
    },
    'CCR1': {
        '1': ('SA-CCR (for derivatives)', '2520701'),
        '2': ('IMM (for derivatives and SFTs)', '2520702'),
        '3': ('Of which: SFTs', None),
        '4': ('Of which: Netting sets under cross-product netting', None),
        '5': ('Financial collateral simple method (SFTs)', None),
        '6': ('Financial collateral comprehensive method (SFTs)', None),
        '7': ('VaR for SFTs', None),
        'Total': ('Total', '2520703'),
    },
    'IRRBB1': {
        # Interest rate risks of non-trading book activities
        '1': ('Parallel up', None),
        '2': ('Parallel down', None),
        '3': ('Steepener', None),
        '4': ('Flattener', None),
        '5': ('Short rates up', None),
        '6': ('Short rates down', None),
        '1a': ('Changes of EVE - Parallel up', '2525001'),
        '2a': ('Changes of EVE - Parallel down', '2525002'),
        '3a': ('Changes of EVE - Steepener', '2525003'),
        '4a': ('Changes of EVE - Flattener', '2525004'),
        '5a': ('Changes of EVE - Short rates up', '2525005'),
        '6a': ('Changes of EVE - Short rates down', '2525006'),
        'EU 1': ('Parallel up NII', '2525011'),
        'EU 2': ('Parallel down NII', '2525012'),
        'EU-1': ('Parallel up NII', '2525011'),
        'EU-2': ('Parallel down NII', '2525012'),
        '7': ('Tier 1 capital', '2520133'),
    },
    'CC2': {
        '1': ('Property, plant and equipment', None),
        '2': ('Intangible assets', '2520110'),
        '3': ('Deferred tax assets', '2520111'),
    },
    'MR2': {
        '1': ('RWA at the beginning of the reporting period', None),
        '2': ('Movement in risk levels', None),
        '3': ('Model updates/roll-outs', None),
        '4': ('Methodology and policy', None),
        '5': ('Acquisitions and disposals', None),
        '6': ('Foreign exchange movements', None),
        '7': ('Other', None),
        '8': ('RWA at the end of the reporting period', None),
    },
    'MR3': {
        '1': ('VaR (10 day 99%)', None),
        '2': ('sVaR (10 day 99%)', None),
        '3': ('IRC (99.9%)', None),
        '4': ('CRM (99.9%)', None),
        '5': ('Other', None),
    },
    'MR4': {
        '1': ('VaR (10 day 99%)', None),
        '2': ('sVaR (10 day 99%)', None),
        '3': ('IRC (99.9%)', None),
        '4': ('CRM (99.9%)', None),
    },
    'CQ7': {
        '1': ('On-balance-sheet exposures', None),
        '2': ('Off-balance-sheet exposures', None),
        'Total': ('Total', None),
    },
    'SEC1': {
        '1': ('Institution acts as originator', None),
        '2': ('Institution acts as sponsor', None),
        '3': ('Institution acts as investor', None),
    },
}


def clean_number(value):
    """Convert string number to float. Robustly handles US and European formats."""
    if value is None or pd.isna(value):
        return None
        
    if isinstance(value, (int, float)):
        return float(value)
    
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
    if ',' in value and '.' in value:
        if value.rfind(',') > value.rfind('.'):
            # European: 1.234,56 -> omit dots, comma to dot
            value = value.replace('.', '').replace(',', '.')
        else:
            # US: 1,234.56 -> omit commas
            value = value.replace(',', '')
    elif ',' in value:
        if value.count(',') > 1:
             # Multiple commas -> Assume thousands separators (e.g. 1,234,567)
             value = value.replace(',', '')
        else:
            parts = value.split(',')
            if len(parts) == 2 and len(parts[1]) == 3:
                value = value.replace(',', '')
            else:
                value = value.replace(',', '.')
    elif '.' in value:
        parts = value.split('.')
        if len(parts) > 2:
            value = value.replace('.', '')
        elif len(parts) == 2 and len(parts[1]) == 3:
            # If exactly 3 digits after dot, might be thousands
            # For Pillar 3 absolute values, we'll assume it is if it's > 10
            # and no other decimal indicator exists.
            value = value.replace('.', '')

    try:
        result = float(value)
        if is_negative:
            result = -result
        if is_pct:
            result = result / 100
        return result
    except:
        return None


def detect_bank(text, filename):
    """Detect bank name and LEI from PDF text or filename."""
    combined = (text + ' ' + filename).upper()
    
    for pattern, (lei, canonical_name) in BANK_PATTERNS.items():
        if pattern.upper() in combined:
            return canonical_name, lei
    
    return None, None


def detect_period(text):
    """Detect reporting period from PDF text."""
    
    # Look for common date patterns
    for pattern in PERIOD_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            match = matches[0]
            
            # Handle different match formats
            if isinstance(match, tuple):
                # Q2 2025 or H1 2025
                if len(match) == 1:
                    year = match[0]
                    return f"{year}-06-30"
                # 30.06.2025 format
                elif len(match) == 3:
                    if match[0].isdigit() and len(match[0]) == 2:
                        day, month, year = match
                        if month.lower() in ['june', 'jun', '06']:
                            month = '06'
                        return f"{year}-{month}-{day}"
                    elif match[2].isdigit() and len(match[2]) == 4:
                        if match[1].lower() in ['june', 'jun', '06']:
                            return f"{match[2]}-06-{match[0].zfill(2)}"
            else:
                # Single year match
                if match.isdigit() and len(match) == 4:
                    return f"{match}-06-30"
    
    # Look for explicit date patterns
    date_match = re.search(r'30[\./]06[\./](\d{4})', text)
    if date_match:
        return f"{date_match.group(1)}-06-30"
    
    date_match = re.search(r'(\d{4})[\./\-]06[\./\-]30', text)
    if date_match:
        return f"{date_match.group(1)}-06-30"
    
    return None


def is_toc_page(text):
    """Detect if a page is likely a Table of Contents."""
    text_upper = text.upper()
    
    # CRITICAL: If page contains actual data keywords, it's NOT a TOC
    # This prevents false positives on data pages with many decimal points
    data_keywords = ['CET1', 'TIER 1 CAPITAL', 'TOTAL CAPITAL', 'RWA', 'LEVERAGE RATIO', 'NSFR', 'LCR']
    if any(kw in text_upper for kw in data_keywords):
        return False
    
    # Common TOC indicators
    toc_indicators = ['TABLE OF CONTENTS', 'INDEX OF TABLES', 'INDEX OF REGULATORY']
    if any(ind in text_upper for ind in toc_indicators) and text_upper.count('.') > 50:
        return True
    
    # Check for many template codes followed by dots and numbers
    # e.g. "EU KM1 ................. 20"
    patterns = [r'EU\s*[A-Z0-9-]+\s*\.{5,}\s*\d+', r'Template\s*\d+.*\.{5,}\s*\d+']
    matches = []
    for p in patterns:
        matches.extend(re.findall(p, text, re.IGNORECASE))
    
    if len(matches) > 5:
        return True
        
    return False



def parse_index_of_tables(pdf):
    """
    Scans the first 15 pages for an Index of Tables or Table of Contents.
    Returns a dictionary mapping Template Code (e.g., KM1) to Page Number (1-indexed).
    """
    table_map = {}
    
    # Expanded list of all known EU regulatory template codes
    known_templates = [
        # Key Metrics
        'KM1', 'KM2',
        # Own Funds
        'CC1', 'CC2',
        # Overview
        'OV1',
        # Leverage
        'LR1', 'LR2', 'LR3',
        # Liquidity
        'LIQ1', 'LIQ2',
        # Credit Risk
        'CR1', 'CR2', 'CR3', 'CR4', 'CR5', 'CR6', 'CR7', 'CR8',
        'CRE', 'CQ1', 'CQ2', 'CQ3', 'CQ4', 'CQ5', 'CQ6', 'CQ7', 'CQ8',
        # Counterparty Credit Risk
        'CCR1', 'CCR2', 'CCR3', 'CCR4', 'CCR5', 'CCR6', 'CCR7', 'CCR8',
        # Securitization
        'SEC1', 'SEC2', 'SEC3', 'SEC4', 'SEC5',
        # Market Risk
        'MR1', 'MR2', 'MR2-A', 'MR2-B', 'MR3', 'MR4',
        # Operational Risk
        'OR1', 'OR2', 'OR3',
        # Interest Rate Risk
        'IRRBB1', 'IRRBB2',
        # Remuneration
        'REM1', 'REM2', 'REM3', 'REM4', 'REM5',
        # Asset Encumbrance
        'AE1', 'AE2', 'AE3',
        # NPE
        'NPE1', 'NPE2', 'NPE3',
    ]
    
    # Also look for descriptive names
    alias_map = {
        'KEY METRICS TEMPLATE': 'KM1',
        'COMPOSITION OF REGULATORY OWN FUNDS': 'CC1',
        'RECONCILIATION OF REGULATORY OWN FUNDS': 'CC2',
        'OVERVIEW OF RISK WEIGHTED': 'OV1',
        'LEVERAGE RATIO COMMON DISCLOSURE': 'LR1',
        'LIQUIDITY COVERAGE RATIO': 'LIQ1',
        'NET STABLE FUNDING RATIO': 'LIQ2',
        'INTEREST RATE RISKS': 'IRRBB1',
    }

    print("Analyzing Index of Tables...")
    for i in range(min(15, len(pdf.pages))):
        text = pdf.pages[i].extract_text() or ""
        lines = text.split('\n')
        for line in lines:
            line_clean = line.strip()
            if not line_clean: continue
            
            line_upper = line_clean.upper()
            
            # Generic pattern match for EU templates: "EU XXX1" followed by dots and page number
            # e.g., "EU KM1 – Key metrics template ........ 17"
            eu_match = re.search(r'EU\s+([A-Z0-9\-]+)', line_upper)
            if eu_match:
                code = eu_match.group(1).replace('-', '')
                # Validate: must be at least 2 chars and contain a letter
                if len(code) >= 2 and re.search(r'[A-Z]', code):
                    # Look for page number (last number on the line)
                    pnum_match = re.search(r'(\d+)\s*$', line_clean)
                    if pnum_match:
                        pnum = int(pnum_match.group(1))
                        if 1 <= pnum <= len(pdf.pages):
                            if code not in table_map:
                                table_map[code] = pnum

            
            # 1. Match by Explicit Code in known list
            for code in known_templates:
                if code in line_upper:
                    # Look for page number at end
                    match = re.search(r'(\d+)\s*$', line_clean)
                    if match:
                        pnum = int(match.group(1))
                        if 1 <= pnum <= len(pdf.pages):
                            if code not in table_map:
                                table_map[code] = pnum
            
            # 2. Match by Alias / Description
            for alias, target in alias_map.items():
                if alias in line_upper:
                    match = re.search(r'(\d+)\s*$', line_clean)
                    if match:
                        pnum = int(match.group(1))
                        if 1 <= pnum <= len(pdf.pages):
                            if target not in table_map:
                                table_map[target] = pnum

    if table_map:
        print(f"Found {len(table_map)} tables in index: {', '.join(sorted(table_map.keys()))}")
    else:
        print("No index of tables found.")
    return table_map


def find_templates_on_page(page_text):
    """Find all Pillar III template codes on a page."""
    patterns = [
        r'EU\s*(KM1|KM2|CC1|CC2|OV1|LR1|LR2|LR3|LIQ1|LIQ2|IRRBB1|CR1|CR2|CR3|CR4|CR5)',
        r'Table\s+\d+[:\s]+.*?(KM1|KM2|CC1|CC2|OV1|LR1|LR2|LR3|LIQ1|LIQ2|IRRBB)',
    ]
    
    results = []
    for pattern in patterns:
        matches = re.findall(pattern, page_text.upper())
        results.extend(matches)
    
    return list(set(results))


def get_table_title(page_text, template_code):
    """Extract the full table title from page text."""
    patterns = [
        rf'(Table\s+\d+[:\s]+EU\s*{template_code}[^\n]*)',
        rf'(EU\s*{template_code}\s*[-–:]\s*[^\n]*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:100]
    
    return f"EU {template_code}"


def parse_table_rows(table, template_code, multiplier=1.0):
    """Parse rows from a table using template definitions."""
    
    row_defs = TEMPLATE_ROWS.get(template_code, {})
    results = []
    
    for row in table:
        if not row or len(row) < 1:
            continue
            
        # Pre-process row: join cells that are very short (likely split words)
        clean_row = []
        for cell in row:
            val = str(cell).strip() if cell is not None else ""
            if clean_row and len(val) <= 2 and not re.match(r'^\d', val):
                # Join with previous cell if this is a tiny fragment (and not a small number)
                clean_row[-1] = (str(clean_row[-1]) if clean_row[-1] else "") + val
            else:
                clean_row.append(cell)
        row = clean_row

        # Initial extraction
        row_id = str(row[0]).strip() if row[0] is not None else ''
        row_label = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ''
        value = None
        
        # Handle Alpha Bank format: values embedded in second column
        # e.g. ['1', 'Common Equity Tier 1 (CET1) Capital 4.921 5.027 4.921']
        if row_id and row_label:
            # Check if label contains embedded values (numbers at the end)
            # Match: "Label text 1,234 5,678 9,012" or "Label 16,08%"
            embedded_match = re.search(r'^(.*?)\s+(\d[\d\.,]*%?)(?:\s+[\d\.,]+%?)*\s*$', row_label)
            if embedded_match:
                clean_label = embedded_match.group(1).strip()
                first_value = embedded_match.group(2)
                value = clean_number(first_value)
                row_label = clean_label
        
        # Handle case where row_id is embedded in row_label
        if not row_id and row_label:
            # Check for ID at start of label: "1 Common Equity Tier 1" or "EU 7d Additional..."
            id_match = re.match(r'^(\d+[a-z]?|EU\s*\d+[a-z]?|EU-\d+[a-z]?)\s+(.*)', row_label, re.I)
            if id_match:
                row_id = id_match.group(1).replace(' ', '')
                row_label = id_match.group(2)
        
        # Handle case where description and values are in the first cell only
        # e.g. ['CET1 4,921 5,027', None, None]
        if row_id and not row_label and not any(row[2:] if len(row) > 2 else []):
            # Look for number patterns at the end of the first cell
            match = re.search(r'^(.*?)\s+([\d\.,]+%?)(?:\s+[\d\.,]+%?)*$', row_id)
            if match:
                row_label = match.group(1).strip()
                value_str = match.group(2)
                value = clean_number(value_str)
                # Try to find row_id in the label
                id_match = re.match(r'^(\d+[a-z]?|EU\s*[\d\-]+[a-z]?)\s+(.*)', row_label)
                if id_match:
                    row_id = id_match.group(1)
                    row_label = id_match.group(2)
                else:
                    row_id = ''
            else:
                continue
        
        # Standard row processing - find value in other columns if not already found
        if value is None:
            if row_id.lower() in ['', 'none', 'ref', 'row']:
                row_id = ''
            
            # Find first numeric value
            for cell in row[2:]:
                val = clean_number(cell)
                if val is not None:
                    value = val
                    break
        
        if value is None:
            continue

            
        # Apply multiplier if absolute amount
        # Robust ratio detection
        is_ratio = (
            "%" in row_label or 
            "ratio" in row_label.lower() or 
            "percentage" in row_label.lower() or
            (template_code == 'KM1' and row_id in ['5', '6', '7', '13', '14', '15']) or
            (template_code == 'LIQ1' and row_id == '23')
        )
        
        if template_code == 'IRRBB1':
            is_ratio = False
            
        if template_code == 'KM1':
            km1_amount_rows = ['1', '2', '3', '4', '4a', '13', '15', '17', '19']
            km1_ratio_rows = ['5', '5b', '6', '6b', '7', '7b', '8', '9', '10', '11', '12', '14', '14a', '14b', '14c', '14d', '14e', '16', '18', '20', '21', '23']
            rid_clean = row_id.strip().lower()
            if rid_clean in km1_ratio_rows:
                is_ratio = True
            elif rid_clean in km1_amount_rows:
                is_ratio = False
                
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
        elif abs(value) > 1.0 and "%" not in row_label:
            # Normalize ratio if reported like 15.5
            if abs(value) > 1.0 and abs(value) < 100:
                value /= 100.0

        # Match to row definition
        eba_item_id = None
        matched_label = row_label[:80]
        
        # QUALITY CHECK:
        # If no row_id and label is very long or looks like text, skip it (likely a note or header)
        if not row_id and len(row_label) > 100:
            continue
            
        # If row_id is just whitespace or non-id characters
        if row_id and not re.match(r'^[A-Z0-9\.\-]*$', row_id, re.I):
             if row_id not in row_defs:
                # Probably not a valid ID column, treat as label fragment
                row_label = f"{row_id} {row_label}".strip()
                row_id = ""

        if row_id in row_defs:
            matched_label, eba_item_id = row_defs[row_id]
        else:
            # Fallback label matching
            for def_id, (def_label, def_eba) in row_defs.items():
                if def_label.lower() in row_label.lower():
                    eba_item_id = def_eba
                    matched_label = def_label
                    row_id = def_id # Adopt the ID if label matches
                    break
        
        results.append({
            'row_id': row_id,
            'row_label': matched_label,
            'raw_label': row_label[:100],
            'value': value,
            'eba_item_id': eba_item_id,
            'is_new': eba_item_id is None,
            'dimension_name': 'EVE' if template_code == 'IRRBB1' else 'Default'
        })
    
    # DEDUPLICATION: For rows with the same ID, keep the first one with a meaningful value
    seen_ids = {}
    deduped = []
    for r in results:
        row_id = r['row_id']
        if not row_id:
            # No ID, always keep
            deduped.append(r)
        elif row_id not in seen_ids:
            # First time seeing this ID
            seen_ids[row_id] = len(deduped)
            deduped.append(r)
        elif r['value'] and abs(r['value']) > abs(results[seen_ids[row_id]].get('value', 0) if seen_ids[row_id] < len(results) else 0):
            # This occurrence has a larger value, replace
            pass  # Actually, keep the first one - it's usually correct
    
    return deduped


    return deduped


def parse_text_rows(text, template_code, multiplier=1.0):
    """
    Fallback parser that scans raw text for known template rows.
    Useful for banks like Eurobank where table extraction fails but text is readable.
    """
    results = []
    if template_code not in TEMPLATE_ROWS:
        return results
        
    row_defs = TEMPLATE_ROWS[template_code]
    
    # Pre-compile regexes for each row
    patterns = []
    for row_id, (def_label, eba_id) in row_defs.items():
        # Clean label for regex (escape special chars)
        clean_lbl = re.escape(def_label.replace('(', '').replace(')', '').replace('-', ' ').strip())
        # Truncate if too long to allow for variation
        if len(clean_lbl) > 20: 
            clean_lbl = clean_lbl[:20]
            
        # Pattern: RowID + Label + Value
        # e.g. "1 Common Equity Tier 1 ... 7,932"
        # Or just Label + Value if ID is missing
        # Allow for EU- ID prefix variation
        id_part = re.escape(row_id).replace('-', r'\s*-?\s*')
        
        # Regex variants to try
        # Updated to capture negative numbers: (123) or -123
        number_pattern = r'((?:-|\()?\d[\d,.]+%?\)?)(?:\s+|$)'
        
        variants = [
            # ID + Label + Value
            r'(?:^|\n)\s*' + id_part + r'\s+.*?' + clean_lbl + r'.*?' + number_pattern,
            # Just Label + Value (if ID is lost)
            r'(?:^|\n)\s*.*?' + clean_lbl + r'.*?' + number_pattern
        ]
        
        patterns.append((row_id, def_label, eba_id, variants))
        
    # Scan text
    # Try to find values
    for row_id, def_label, eba_id, variants in patterns:
        for pattern in variants:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                val_str = match.group(1)
                value = clean_number(val_str)
                
                if value is not None:
                    # Apply multiplier heuristic
                    is_ratio = (
                        "%" in val_str or 
                        "ratio" in def_label.lower() or 
                        "percentage" in def_label.lower() or
                        (template_code == 'KM1' and row_id in ['5', '6', '7', '13', '14', '15']) or
                        (template_code == 'LIQ1' and row_id == '23')
                    )
                    
                    if template_code == 'IRRBB1':
                        is_ratio = False
                        
                    if template_code == 'KM1':
                        km1_amount_rows = ['1', '2', '3', '4', '4a', '13', '15', '17', '19']
                        km1_ratio_rows = ['5', '5b', '6', '6b', '7', '7b', '8', '9', '10', '11', '12', '14', '14a', '14b', '14c', '14d', '14e', '16', '18', '20', '21', '23']
                        rid_clean = row_id.strip().lower()
                        if rid_clean in km1_ratio_rows:
                            is_ratio = True
                        elif rid_clean in km1_amount_rows:
                            is_ratio = False
                            
                    if template_code == 'KM2':
                        km2_amount_rows = ['1', 'EU-1a', '2', '4', '7']
                        km2_ratio_rows = ['3', '5', '6', '8']
                        rid_clean = row_id.strip().lower()
                        if rid_clean in km2_ratio_rows:
                            is_ratio = True
                        elif rid_clean in km2_amount_rows:
                            is_ratio = False
                        
                    # Exception: Leverage Ratio Exposure contains 'ratio' but is an amount
                    if 'exposure' in def_label.lower():
                        is_ratio = False
                        
                    if not is_ratio:
                        value *= multiplier
                    elif abs(value) > 1.0 and "%" not in val_str:
                        if abs(value) > 1.0 and abs(value) < 100:
                            value /= 100.0
                        
                    results.append({
                        'row_id': row_id,
                        'row_label': def_label,
                        'raw_label': match.group(0)[:50],
                        'value': value,
                        'eba_item_id': eba_id,
                        'is_new': eba_id is None,
                        'dimension_name': 'EVE' if template_code == 'IRRBB1' else 'Default'
                    })
                    break # Stop after first match for this row
    
    return results


def parse_pdf(pdf_path):
    """Parse a Pillar III PDF with auto-detection of bank and period."""
    
    filename = os.path.basename(pdf_path)
    print(f"\n{'='*70}")
    print(f"Processing: {filename}")
    print(f"{'='*70}")
    
    all_data = []
    detected_bank = None
    detected_lei = None
    detected_period = None
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        
        # Extract text from first few pages for detection
        first_pages_text = ""
        for page in pdf.pages[:30]:
            text = page.extract_text() or ""
            first_pages_text += text + "\n"
        
        # Detect bank
        detected_bank, detected_lei = detect_bank(first_pages_text, filename)
        if detected_bank:
            print(f"Detected Bank: {detected_bank}")
            print(f"LEI: {detected_lei}")
        else:
            print("WARNING: Could not detect bank name!")
            detected_lei = "UNKNOWN"
        
        # Detect period
        detected_period = detect_period(first_pages_text)
        if detected_period:
            print(f"Detected Period: {detected_period}")
        else:
            print("WARNING: Could not detect period!")
            year_match = re.search(r'(\d{4})', filename)
            if year_match:
                detected_period = f"{year_match.group(1)}-06-30"
                print(f"Using period from filename: {detected_period}")
            else:
                detected_period = "2025-06-30"
                print(f"Using default period: {detected_period}")
        
        # Detect units/multiplier
        multiplier = 1.0
        # Search for specific unit strings
        unit_text = first_pages_text.upper()
        if re.search(r'(?:AMOUNTS\s+IN|IN|€)\s*(?:EURO|EUR)?\s*(?:MILLION|MIO)', unit_text):
            multiplier = 1000000.0
            print("Detected units: Millions")
        elif re.search(r'(?:AMOUNTS\s+IN|IN|€)\s*(?:EURO|EUR)?\s*(?:’000|000|THOUSAND)', unit_text):
            multiplier = 1000.0
            print("Detected units: Thousands")
        elif '€M' in unit_text or 'EUR M' in unit_text or '€ MIO' in unit_text:
            multiplier = 1000000.0
            print("Detected units: Millions (from short notation)")

        # Parse all pages for templates
        templates_found = set()
        
        # Get Table Locations from Index
        table_locations = parse_index_of_tables(pdf)
        
        # Build inverted map: Page -> Templates
        # We allow +/- 2 pages because logical page numbers often differ from physical ones
        page_to_templates = {}
        for code, pnum in table_locations.items():
            for offset in range(-2, 3):
                target_p = pnum + offset
                if 1 <= target_p <= len(pdf.pages):
                    if target_p not in page_to_templates: page_to_templates[target_p] = set()
                    page_to_templates[target_p].add(code)

        # 1. Map physical to logical pages
        physical_to_logical = {}
        for i, p in enumerate(pdf.pages, start=1):
            p_text = p.extract_text() or ""
            lines = p_text.split('\n')
            if not lines: continue
            
            p_num_found = None
            # Check footer (last 3 lines)
            for l in lines[-3:]:
                # Look for standalone number or "Page X"
                match = re.search(r'^\s*(\d+)\s*$', l) or re.search(r'Page\s+(\d+)', l, re.I)
                if match:
                    p_num_found = int(match.group(1))
                    break
            if not p_num_found:
                 # Check header (first 3 lines)
                 for l in lines[:3]:
                    match = re.search(r'^\s*(\d+)\s*$', l) or re.search(r'Page\s+(\d+)', l, re.I)
                    if match:
                        p_num_found = int(match.group(1))
                        break
            if p_num_found:
                physical_to_logical[i] = p_num_found

        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            logical_num = physical_to_logical.get(page_num, page_num)
            
            if is_toc_page(page_text):
                continue
            
            # --- STRICT INDEX LOGIC ---
            # If a template is in the index, we ONLY parse it on its index pages.
            # If it's NOT in the index, we use text detection.
            
            final_templates = set()
            
            # 1. Process templates from index
            for code, target_logical in table_locations.items():
                if abs(logical_num - target_logical) <= 1:
                    # Double check keywords on the page
                    t_up = code.upper()
                    p_up = page_text.upper()
                    if t_up in p_up:
                        final_templates.add(code)
                    elif code == 'KM1' and ('METRICS' in p_up or 'KM1' in p_up):
                        final_templates.add(code)
                    elif code == 'KM2' and ('METRICS' in p_up or 'KM2' in p_up or 'KM –' in p_up):
                        final_templates.add(code)
                    elif code == 'CC1' and ('OWN FUNDS' in p_up or 'CC1' in p_up):
                        final_templates.add(code)
                    elif code == 'OV1' and ('OVERVIEW' in p_up or 'OV1' in p_up):
                        final_templates.add(code)
                    elif code == 'LIQ1' and ('LIQUIDITY' in p_up or 'LIQ1' in p_up):
                        final_templates.add(code)
                    elif code == 'CC2' and ('RECONCILIATION' in p_up or 'CC2' in p_up):
                        final_templates.add(code)
            
            # 2. Add templates detected by text ONLY if they aren't in the index at all
            detected_on_page = find_templates_on_page(page_text)
            for code in detected_on_page:
                if code not in table_locations:
                    final_templates.add(code)
            
            if final_templates:
                print(f"  Page {page_num} (logical {logical_num}): Templates to try: {list(final_templates)}")
                tables = page.extract_tables()
                
                # Combine tables if they look split
                combined_rows = []
                for t in tables:
                    if t:
                        combined_rows.extend(t)
                
                for code in final_templates:
                    rows = parse_table_rows(combined_rows, code, multiplier)
                    
                    # Count valid mapped items
                    mapped_items = sum(1 for r in rows if r['eba_item_id'])
                    
                    # FALLBACK: Check text parser if table results are underwhelming
                    # KM1 should have 10+ items. CC1 20+. 
                    # If we have few, text parser might do better (especially for Eurobank)
                    if code in ['KM1', 'CC1', 'OV1', 'KM2', 'LR1', 'LR2', 'LR3']:
                         print(f"    - Table extraction found {mapped_items} mapped items for {code}. Checking text fallback...")
                         text_rows = parse_text_rows(page_text, code, multiplier)
                         text_mapped = sum(1 for r in text_rows if r['eba_item_id'])
                         
                         if text_mapped > mapped_items:
                             print(f"      -> Text fallback BETTER! Found {text_mapped} items vs {mapped_items}. Using text data.")
                             rows = text_rows

                    if rows:
                        print(f"    - Extracted {len(rows)} items for template {code} from page {page_num}")
                        
                        for r in rows:
                            item = {
                                'bank_name': detected_bank or "Unknown Bank",
                                'lei': detected_lei,
                                'period': detected_period,
                                'template': code,
                                'template_code': code, 
                                'row_id': r['row_id'],
                                'row_label': r['row_label'],
                                'raw_label': r['raw_label'],
                                'value': r['value'],  # Matches save_results expectation
                                'eba_item_id': r['eba_item_id'],
                                'is_new': r['is_new'] # Matches save_results expectation
                            }
                            all_data.append(item)

        
        print(f"Templates found: {', '.join(sorted(templates_found))}")
        print(f"Total items extracted: {len(all_data)}")
    
    return pd.DataFrame(all_data), detected_lei, detected_period, detected_bank


def setup_database(db_path):
    """Create database tables if they don't exist."""
    
    conn = sqlite3.connect(db_path)
    
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
            bank_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lei, period, template_code, row_id, row_label)
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pillar3_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lei TEXT NOT NULL,
            period TEXT NOT NULL,
            filename TEXT,
            bank_name TEXT,
            parse_date TEXT DEFAULT CURRENT_TIMESTAMP,
            total_items INTEGER,
            new_items INTEGER,
            UNIQUE(lei, period)
        )
    """)
    
    conn.commit()
    conn.close()


def save_results(df, db_path, filename, bank_name):
    """Save parsed data to database."""
    
    if df.empty:
        return 0
    
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
        try:
            conn.execute("""
                INSERT OR REPLACE INTO facts_pillar3 
                (lei, period, template_code, table_title, row_id, row_label, raw_label, 
                 amount, eba_item_id, is_new_metric, source_page, bank_name, dimension_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (row['lei'], row['period'], row['template'], row.get('table_title', ''),
                  row['row_id'], row['row_label'], row.get('raw_label', ''),
                  row['value'], row['eba_item_id'], row['is_new'], row.get('page', 0),
                  row.get('bank_name', ''), row.get('dimension_name', 'Default')))
        except Exception as e:
            print(f"Error saving row: {e}")
    
    # Record report
    lei = df['lei'].iloc[0]
    period = df['period'].iloc[0]
    new_count = int(df['is_new'].sum())
    
    conn.execute("""
        INSERT OR REPLACE INTO pillar3_reports 
        (lei, period, filename, bank_name, total_items, new_items)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (lei, period, filename, bank_name, len(df), new_count))
    
    conn.commit()
    conn.close()
    
    return len(df)


def main():
    parser = argparse.ArgumentParser(description='Batch parse Pillar III PDFs')
    parser.add_argument('--dir', help='Directory containing PDFs')
    parser.add_argument('--pdf', help='Single PDF file to parse')
    parser.add_argument('--db', default=str(DB_PATH), help='Database path')
    parser.add_argument('--dry-run', action='store_true', help='Parse but do not save')
    
    args = parser.parse_args()
    
    # Get list of PDFs to process
    pdfs = []
    if args.pdf:
        pdfs = [args.pdf]
    elif args.dir:
        pdfs = [os.path.join(args.dir, f) for f in os.listdir(args.dir) 
                if f.lower().endswith('.pdf')]
    else:
        print("ERROR: Specify --dir or --pdf")
        return 1
    
    if not pdfs:
        print("No PDF files found!")
        return 1
    
    print(f"\nFound {len(pdfs)} PDF(s) to process")
    
    # Setup database
    if not args.dry_run:
        setup_database(args.db)
    
    # Process each PDF
    total_saved = 0
    results_summary = []
    
    for pdf_path in pdfs:
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            continue
        
        try:
            df, lei, period, bank_name = parse_pdf(pdf_path)
            
            if not df.empty:
                # Print summary by template
                print("\nBy template:")
                for tmpl in df['template'].unique():
                    t_df = df[df['template'] == tmpl]
                    mapped = t_df['eba_item_id'].notna().sum()
                    print(f"  {tmpl}: {len(t_df)} items ({mapped} mapped to EBA)")
                
                if not args.dry_run:
                    saved = save_results(df, args.db, os.path.basename(pdf_path), bank_name)
                    total_saved += saved
                    print(f"\nSaved {saved} records")
                
                results_summary.append({
                    'file': os.path.basename(pdf_path),
                    'bank': bank_name,
                    'lei': lei,
                    'period': period,
                    'items': len(df),
                    'mapped': df['eba_item_id'].notna().sum()
                })
        
        except Exception as e:
            print(f"ERROR processing {pdf_path}: {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    print(f"\n{'='*70}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"{'Bank':<35} {'Period':<12} {'Items':>8} {'Mapped':>8}")
    print("-"*70)
    for r in results_summary:
        print(f"{r['bank'] or 'Unknown':<35} {r['period']:<12} {r['items']:>8} {r['mapped']:>8}")
    print(f"\nTotal items saved: {total_saved}")
    
    return 0


if __name__ == '__main__':
    exit(main())
