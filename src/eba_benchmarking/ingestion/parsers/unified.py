"""
Pillar 3 Unified Parser
========================
Unified parser for Pillar 3 reports from PDFs and Excel files.
This module can be called from the main pipeline or run standalone.

Features:
- PDF parsing with fallback chain (standard -> geometric -> line parsing)
- Excel parsing with sheet detection
- Bank and period normalization
- Source file and page number tracking
- Automatic CSV export after parsing
- Report-type aware thresholds (H1/FY vs Q1/Q3)
"""

import os
import sys
import re
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add scripts to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import PDF parsing functions from enhanced parser
from eba_benchmarking.ingestion.parsers.pdf_enhanced import (
    parse_pdf_file, 
    ParserLogger, 
    save_results as save_pdf_results,
    export_csv,
    generate_report
)
from eba_benchmarking.ingestion.parsers.common import TEMPLATE_ROWS, clean_number
from eba_benchmarking.config import DB_NAME

# Configuration
DB_PATH = Path(DB_NAME)
RAW_DATA_DIR = Path('data/raw/Pillar3reports')
REPORT_DIR = Path('data/output')

# Bank identification for Excel files
BANK_CONFIG_EXCEL = {
    'Piraeus': {
        'filename_patterns': ['Pillar III_EN_', 'piraeus'],
        'lei': '213800OYHR4PPVA77574',
    },
    'Bank of Cyprus': {
        'filename_patterns': ['interim-pillar-3', 'cyprus', 'boc'],
        'lei': '635400L14KNHJ3DMBX37',
    },
    'NBG': {
        'filename_patterns': ['nbg', 'national'],
        'lei': '5UMCZOEYKCVFAW8ZLO05',
    },
}

# Track files for renaming
FILES_TO_RENAME = []


def normalize_filename(bank_name, period, original_path):
    """
    Generate normalized filename in format: [period]_[bank_name].[ext]
    Example: 2025-09-30_Alpha_Bank.pdf
    """
    ext = Path(original_path).suffix
    
    # Sanitize bank name (replace spaces with underscores)
    safe_bank_name = bank_name.replace(' ', '_').replace('/', '_')
    
    # Create normalized name
    normalized_name = f"{period}_{safe_bank_name}{ext}"
    
    return normalized_name


def rename_processed_files(logger):
    """Rename all processed files to normalized format."""
    if not FILES_TO_RENAME:
        return
    
    print("\n" + "=" * 70)
    print("RENAMING FILES TO NORMALIZED FORMAT")
    print("=" * 70)
    
    renamed_count = 0
    
    for original_path, bank_name, period in FILES_TO_RENAME:
        try:
            original_path = Path(original_path)
            if not original_path.exists():
                continue
            
            normalized_name = normalize_filename(bank_name, period, str(original_path))
            new_path = original_path.parent / normalized_name
            
            # Skip if already normalized
            if original_path.name == normalized_name:
                logger.info(f"Already normalized: {original_path.name}")
                continue
            
            # Skip if target exists
            if new_path.exists():
                logger.warn(f"Cannot rename, target exists: {normalized_name}")
                continue
            
            # Rename
            import shutil
            shutil.move(str(original_path), str(new_path))
            logger.success(f"Renamed: {original_path.name} -> {normalized_name}")
            renamed_count += 1
            
        except Exception as e:
            logger.error(f"Failed to rename {original_path}: {e}")
    
    print(f"\nRenamed {renamed_count} files")
    
    # Clear the list
    FILES_TO_RENAME.clear()


def detect_bank_from_excel(filepath):
    """Detect bank from Excel filename."""
    filename = os.path.basename(filepath).lower()
    
    for bank_name, config in BANK_CONFIG_EXCEL.items():
        for pattern in config['filename_patterns']:
            if pattern.lower() in filename:
                return bank_name, config['lei']
    
    return "Unknown", None


def detect_period_from_excel(filepath, df_text=""):
    """Detect reporting period from Excel filename or content."""
    filename = os.path.basename(filepath).lower()
    combined = filename + " " + df_text.lower()
    
    patterns = [
        (r'092025|09[-_./]2025|sep.*2025|september.*2025', '2025-09-30'),
        (r'062025|06[-_./]2025|jun.*2025|june.*2025', '2025-06-30'),
        (r'032025|03[-_./]2025|mar.*2025|march.*2025', '2025-03-31'),
        (r'122025|12[-_./]2025|dec.*2025|december.*2025', '2025-12-31'),
        (r'092024|09[-_./]2024|sep.*2024', '2024-09-30'),
        (r'062024|06[-_./]2024|jun.*2024', '2024-06-30'),
    ]
    
    for pattern, period in patterns:
        if re.search(pattern, combined):
            return period
    
    return '2025-06-30'  # Default


def parse_excel_report(filepath, logger):
    """Parse a single Excel Pillar 3 report."""
    filename = os.path.basename(filepath)
    logger.info(f"Processing Excel: {filename}")
    
    bank_name, lei = detect_bank_from_excel(filepath)
    if bank_name == "Unknown":
        logger.warn(f"Unknown bank for Excel: {filename}")
        return []
    
    logger.info(f"  Bank: {bank_name}, LEI: {lei}")
    
    try:
        xl = pd.ExcelFile(filepath)
    except Exception as e:
        logger.error(f"Error opening Excel: {e}")
        return []
    
    all_data = []
    
    try:  # Wrap parsing in try-finally to ensure file is closed
        # Template detection patterns
        template_patterns = {
            'KM1': ['km1', 'key metrics', 'key-metrics'],
            'CC1': ['cc1'],
            'CC2': ['cc2'],
            'OV1': ['ov1'],
            'LR1': ['lr1'],
            'LR2': ['lr2'],
            'LR3': ['lr3'],
            'LIQ1': ['liq1', 'lcr'],
            'LIQ2': ['liq2', 'nsfr'],
            'CR1': ['cr1'],
            'CCR1': ['ccr1'],
            'KM2': ['km2'],
            'IRRBB1': ['irrbb1', 'irrbb'],
        }
        
        for sheet_name in xl.sheet_names:
            sheet_lower = sheet_name.lower()
            
            # Detect template
            template_code = None
            for code, patterns in template_patterns.items():
                if any(p in sheet_lower for p in patterns):
                    template_code = code
                    break
            
            if not template_code:
                continue
            
            # Skip commentary sheets
            if 'comment' in sheet_lower or 'notes' in sheet_lower:
                continue
            
            logger.info(f"  Parsing {template_code} from sheet '{sheet_name}'")
            
            try:
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
            except Exception as e:
                logger.error(f"  Error reading sheet {sheet_name}: {e}")
                continue
            
            # Detect units from sheet content
            unit_text = ""
            for i in range(min(20, len(df))):
                unit_text += " ".join(str(x) for x in df.iloc[i].values if pd.notna(x)) + " "
            
            unit_text_upper = unit_text.upper()
            if re.search(r'(?:AMOUNTS?\s+IN|IN|€)\s*(?:EURO|EUR)?\s*(?:MILLION|MIO|MN)', unit_text_upper) or '€M' in unit_text_upper:
                multiplier = 1_000_000.0
            elif re.search(r"(?:000'S|000S|THOUSAND)", unit_text_upper) or '€000' in unit_text_upper:
                multiplier = 1_000.0
            else:
                multiplier = 1_000_000.0  # Default to millions
            
            # Detect date columns
            date_cols = {}
            for i in range(min(15, len(df))):
                for j, val in enumerate(df.iloc[i].values):
                    if pd.isna(val):
                        continue
                    val_str = str(val).upper()
                    
                    year_match = re.search(r'(202\d)', val_str)
                    if year_match:
                        year = year_match.group(1)
                        if 'SEP' in val_str or '09' in val_str:
                            date_cols[j] = f"{year}-09-30"
                        elif 'JUN' in val_str or '06' in val_str:
                            date_cols[j] = f"{year}-06-30"
                        elif 'MAR' in val_str or '03' in val_str:
                            date_cols[j] = f"{year}-03-31"
                        elif 'DEC' in val_str or '12' in val_str:
                            date_cols[j] = f"{year}-12-31"
            
            if not date_cols:
                # Use filename-based period detection
                period = detect_period_from_excel(filepath, unit_text)
                for j in range(len(df.columns)):
                    date_cols[j] = period
            
            # Get template row definitions
            row_defs = TEMPLATE_ROWS.get(template_code, {})
            
            # Parse rows
            for i, row in df.iterrows():
                row_id = None
                row_label = None
                
                for j, val in enumerate(row.values[:3]):
                    if pd.notna(val):
                        val_str = str(val).strip()
                        if row_id is None:
                            row_id = re.sub(r'^EU[-\s]+', '', val_str, flags=re.IGNORECASE)
                        elif row_label is None:
                            row_label = val_str
                            break
                
                if not row_id:
                    continue
                
                mapping = row_defs.get(row_id) or row_defs.get(row_id.split('-')[-1].strip())
                
                for col_idx, period in date_cols.items():
                    if col_idx >= len(row.values):
                        continue
                    
                    val_raw = row.values[col_idx]
                    amount = clean_number(val_raw)
                    
                    if amount is not None:
                        label_lower = (row_label or "").lower()
                        is_ratio = abs(amount) < 2.0 or '%' in label_lower or 'ratio' in label_lower
                        
                        if not is_ratio:
                            amount *= multiplier
                        elif abs(amount) > 1.0:
                            amount /= 100.0
                        
                        all_data.append({
                            'bank_name': bank_name,
                            'lei': lei,
                            'period': period,
                            'template': template_code,
                            'row_id': row_id,
                            'row_label': (mapping[0] if mapping else row_label) or row_id,
                            'raw_label': row_label or row_id,
                            'value': amount,
                            'eba_item_id': mapping[1] if mapping else None,
                            'is_new': 0 if (mapping and mapping[1]) else 1,
                            'source_page': None,
                            'source_file': filename,
                            'dimension_name': 'EVE' if template_code == 'IRRBB1' else 'Default'
                        })
    finally:
        xl.close()
    
    logger.info(f"  Extracted {len(all_data)} items from Excel")
    
    if all_data:
        period = all_data[0].get('period', '2025-06-30')
        FILES_TO_RENAME.append((filepath, bank_name, period))
    
    return all_data


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


def run_pillar3_parser():
    """Main entry point - parse all Pillar 3 reports (PDFs and Excels)."""
    print("=" * 70)
    print("PILLAR 3 UNIFIED PARSER")
    print("Parsing PDFs and Excel files")
    print("=" * 70)
    
    logger = ParserLogger()
    
    # Find all files
    pdf_files = []
    excel_files = []
    
    if RAW_DATA_DIR.exists():
        for f in os.listdir(RAW_DATA_DIR):
            filepath = RAW_DATA_DIR / f
            if f.endswith('.pdf'):
                pdf_files.append(str(filepath))
            elif f.endswith('.xlsx') or f.endswith('.xls'):
                excel_files.append(str(filepath))
    
    print(f"\nFound {len(pdf_files)} PDF files and {len(excel_files)} Excel files")
    
    all_results = []
    
    # Process PDFs
    if pdf_files:
        print("\n" + "=" * 50)
        print("PROCESSING PDF FILES")
        print("=" * 50)
        
        for pdf_path in sorted(pdf_files):
            print("\n" + "-" * 40)
            try:
                results = parse_pdf_file(pdf_path, logger)
                all_results.extend(results)
                
                # Track PDF for renaming if we got data
                if results:
                    bank_name = results[0].get('bank_name', 'Unknown')
                    period = results[0].get('period', '2025-06-30')
                    FILES_TO_RENAME.append((pdf_path, bank_name, period))
                    
            except Exception as e:
                logger.error(f"Failed to parse PDF {pdf_path}: {e}")
    
    # Process Excel files
    if excel_files:
        print("\n" + "=" * 50)
        print("PROCESSING EXCEL FILES")
        print("=" * 50)
        
        for excel_path in sorted(excel_files):
            print("\n" + "-" * 40)
            try:
                results = parse_excel_report(excel_path, logger)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Failed to parse Excel {excel_path}: {e}")
    
    # Save to database
    print("\n" + "=" * 70)
    print("SAVING RESULTS TO DATABASE")
    print("=" * 70)
    
    saved_count = save_results(all_results, logger)
    print(f"Saved {saved_count} records to database")
    
    # Rename files to normalized format
    rename_processed_files(logger)
    
    # Export CSV
    export_csv(logger)
    
    # Generate report
    generate_report(logger, saved_count)
    
    return saved_count


def main():
    """Standalone entry point."""
    run_pillar3_parser()


if __name__ == "__main__":
    main()
