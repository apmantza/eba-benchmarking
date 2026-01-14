import pdfplumber
import re
import sys
import os
import pandas as pd
from operator import itemgetter

# Add scripts to path
from eba_benchmarking.ingestion.parsers.pdf_enhanced import reconstruct_page_text
from eba_benchmarking.ingestion.parsers.common import clean_number
from eba_benchmarking.config import DB_NAME
import sqlite3

class BlueprintPipeline:
    def __init__(self, pdf_path, logger=None):
        self.pdf_path = pdf_path
        self.doc = pdfplumber.open(pdf_path)
        self.logger = logger or print
        self.index = {} # Template -> Page Number
        
        # Detection
        fname = os.path.basename(pdf_path)
        self.period = re.search(r'\d{4}-\d{2}-\d{2}', fname).group(0) if re.search(r'\d{4}-\d{2}-\d{2}', fname) else '2025-06-30'
        self.bank_name = 'Unknown'
        if 'NBG' in fname: self.bank_name = 'NBG'
        elif 'Alpha' in fname: self.bank_name = 'Alpha Bank'
        elif 'Eurobank' in fname: self.bank_name = 'Eurobank'
        elif 'Piraeus' in fname: self.bank_name = 'Piraeus'
        
        self.lei = {
            'NBG': '5UMCZOEYKCVFAW8ZLO05', 
            'Alpha Bank': 'NLPK02SGC0U1AABDLL56', 
            'Eurobank': 'JEUVK5RWVJEN8W0C9M24',
            'Piraeus': '213800OYHR4PPVA77574'
        }.get(self.bank_name, 'UNKNOWN')

    def run(self, save=False):
        self.logger(f"Processing: {os.path.basename(self.pdf_path)} ({self.bank_name})")
        self.scan_index()
        all_results = []
        
        # Targets for this blueprint
        targets = ['KM1', 'KM2', 'OV1', 'LR2', 'LIQ1', 'IRRBB1', 'CC1', 'CC2']
        
        for code in targets:
            if code in self.index:
                items = self.parse_template(code)
                all_results.extend(items)
                if save:
                    self.save_to_db(items)
            else:
                self.logger(f"  [MISSING] {code} not found in index")
                
        return all_results

    def save_to_db(self, items):
        if not items: return
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        count = 0
        for item in items:
            try:
                cur.execute("""
                    INSERT OR REPLACE INTO facts_pillar3 
                    (lei, period, template_code, table_title, row_id, row_label, raw_label, 
                     amount, is_new_metric, source_page, bank_name, dimension_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.lei, self.period, item['template_code'], item['template_code'], 
                    item['row_id'], item['row_label'], 'Blueprint Parser',
                    item['amount'], 0, item['source_page'], self.bank_name, item.get('dimension', 'Default')
                ))
                count += 1
            except Exception as e:
                self.logger(f"      [DB ERROR] {e}")
        conn.commit()
        conn.close()
        self.logger(f"    Saved {count} items to DB")

    def scan_index(self):
        self.logger("Scanning Index...")
        for i in range(min(10, len(self.doc.pages))):
            page = self.doc.pages[i]
            text = reconstruct_page_text(page)
            # Find lines like "KM1 Key Metrics ... 27"
            # Pattern: (TemplateCode) (Description) (Page Number at end)
            lines = text.split('\n')
            for line in lines:
                line_clean = line.strip()
                # Find lines like "KM1 Key Metrics ... 27" or "Table 2: EU KM1 ... 23"
                # More robust pattern: code ... page number
                match = re.search(r'\b(KM1|KM2|OV1|LR1|LR2|LIQ1|CC1|CC2|CR1|CR3|CCR1|IRRBB1|CCR8)\b', line_clean)
                if match:
                    code = match.group(1)
                    # Find last number on the line
                    all_nums = re.findall(r'\d+', line_clean)
                    if all_nums:
                        page_num = int(all_nums[-1])
                        if 1 < page_num < 500: # Sanity check
                            if code not in self.index:
                                self.index[code] = page_num
                                self.logger(f"  Found {code} -> Page {page_num}")

    def parse_template(self, code):
        page_num = self.index[code]
        # Many reports have an offset (e.g. index says 27, PDF index is 28)
        # We search a small range around the target
        target_page = None
        for offset in [0, 1, 2, -1]:
            idx = page_num + offset - 1
            if 0 <= idx < len(self.doc.pages):
                p = self.doc.pages[idx]
                t = p.extract_text() or ""
                if code in t:
                    target_page = p
                    break
        
        if not target_page:
            self.logger(f"  [ERROR] Could not find {code} near page {page_num}")
            return []

        self.logger(f"  Parsing {code} on page {target_page.page_number}...")
        text = reconstruct_page_text(target_page)
        lines = text.split('\n')
        
        # 1. Structural Analysis: Standardize on Millions
        report_multiplier = 1.0 
        header_area = "\n".join(lines[:30]).lower()
        if "millions" in header_area or "mio" in header_area or "€ million" in header_area or "eur m" in header_area:
            report_multiplier = 1.0  # Already in millions
        elif "thousands" in header_area or "’000" in header_area or "€ thousand" in header_area:
            report_multiplier = 0.001 # Thousands to Millions
        else:
            # Default to units? Or check if numbers are huge.
            # Let's check common metric lines. If CET1 is > 1M, it's likely units.
            report_multiplier = 1.0 # Default for most P3 PDFs is millions
            
        self.logger(f"    Report scale: {'Millions' if report_multiplier == 1 else 'Thousands'}")
        
        # 2. Targeted Row Extraction
        extracted = []
        
        # Pass 0: Table Extraction (Reliable for clean tables like NBG/Alpha)
        table_rows_found = {} # rid -> (val, page_num)
        for offset in [0, 1, 2, -1]:
            idx = target_page.page_number + offset - 1
            if 0 <= idx < len(self.doc.pages):
                p = self.doc.pages[idx]
                tables = p.extract_tables()
                if tables:
                    for table in tables:
                        if not table: continue
                        for row in table:
                            if not row or len(row) < 2: continue
                            # Clean up row cells
                            row = [str(c).strip() if c else "" for c in row]
                            # Try to find RID in first 2 columns
                            rid_found = None
                            val_found = None
                            
                            row_joined = " ".join([str(c) for c in row if c])
                            
                            for i_col in [0, 1, 2]: # Scan first 3 cols for ID
                                if i_col >= len(row): break
                                cell = str(row[i_col]).strip()
                                if not cell: continue
                                # ID Matching Logic
                                # Handle '1Own' case (Eurobank) where spacing is missing:
                                km2_boundary = r'(?=\b|[A-Z])' if code == 'KM2' else r'\b'
                                m_rid = re.match(r'^(\bEU\s+)?(\d+[a-z]?)' + km2_boundary, cell, re.I)
                                if m_rid:
                                    rid_found = m_rid.group(2)
                                    if m_rid.group(1): rid_found = "EU " + rid_found
                                    
                                    # Find value in remaining columns
                                    for v_cell in row[i_col+1:]:
                                        v_parts = str(v_cell).split()
                                        for v_part in v_parts:
                                            v = clean_number(v_part)
                                            if v is not None:
                                                if abs(v) < 50 and "." not in str(v_part) and "%" not in str(v_part):
                                                    continue
                                                val_found = v
                                                break
                                        if val_found is not None: break
                                    if rid_found and val_found is not None:
                                        break
                            
                            # KM1 specific label-to-id mapping to fix shifted IDs (liquidity/leverage section)
                            if code == 'KM1':
                                km1_fix_map = {
                                    r'liquidity\s*coverage\s*ratio': '17',
                                    r'available\s*stable\s*funding': '18',
                                    r'required\s*stable\s*funding': '19',
                                    r'nsfr\s*ratio': '20',
                                    r'net\s*cash\s*outflow': '16',
                                    r'overall\s*capital\s*requirements?\s*\(%\)': '11a',
                                    r'cash\s*outflows[ -]*total\s*weighted': 'EU 16a',
                                    r'cash\s*inflows[ -]*total\s*weighted': 'EU 16b',
                                    r'total\s*risk\s*weighted\s*exposure': '4',
                                    r'leverage\s*ratio\s*\(%\)': '14',
                                    r'additional\s*own\s*funds\s*requirements\s*.*leverage': '14a',
                                    r'to\s*be\s*made\s*up\s*of\s*cet1\s*capital': '14b',
                                    r'srep\s*leverage\s*ratio\s*requirements': '14c',
                                    r'leverage\s*ratio\s*buffer': '14d',
                                    r'overall\s*leverage\s*ratio\s*requirement': '14e',
                                }
                                for pattern, canonical_rid in km1_fix_map.items():
                                    if re.search(pattern, row_joined, re.I):
                                        if val_found is None:
                                            # Seek number in row
                                            for v_cell in row[1:]:
                                                v_parts = str(v_cell).split()
                                                for v_part in v_parts:
                                                    v = clean_number(v_part)
                                                    if v is not None and not (v < 50 and "." not in str(v_part) and "%" not in str(v_part)):
                                                        val_found = v
                                                        break
                                                if val_found is not None: break
                                        if val_found is not None:
                                            rid_found = canonical_rid
                                            break

                            if rid_found and val_found is not None:
                                if rid_found not in table_rows_found:
                                    table_rows_found[rid_found] = (val_found, p.page_number)

        self.logger(f"    Table extraction found {len(table_rows_found)} candidates")

        
        # Pass 0.1: Expand Text Search Window
        all_lines_with_meta = []
        for offset in [0, 1, 2, -1]:
            idx = target_page.page_number + offset - 1
            if 0 <= idx < len(self.doc.pages):
                p = self.doc.pages[idx]
                p_text = reconstruct_page_text(p)
                all_lines_with_meta.extend([(l, p.page_number) for l in p_text.split('\n')])

        # 2. Targeted Row Extraction
        extracted = []
        km2_debug = False
        if code == 'KM2':
             self.logger(f"DEBUG KM2 Rows: {list(self.get_template_rows(code).keys())}")
             km2_debug = True
             
        irrbb1_max_cols = 0

        for rid, (label, is_ratio_tmpl) in self.get_template_rows(code).items():
            # Pass 0.2: Use Table Results First (Skip for IRRBB1 to use text multi-column logic)
            if rid in table_rows_found and code != 'IRRBB1':
                val, p_num = table_rows_found[rid]
                extracted.append({
                    'template_code': code,
                    'row_id': rid,
                    'row_label': label,
                    'amount': val if is_ratio_tmpl else val * report_multiplier,
                    'source_page': p_num
                })
                self.logger(f"      Matched {rid} from Table (Pass 0)")
                continue

            # Pass 1: Text-based matching (Fallback)
            # Build a fuzzy regex for the label
            # ... (rest of old code builds label_regex)

            # Build a fuzzy regex for the label
            # 1. Allow optional spaces between every character if needed (extreme, but safe)
            # 2. Allow optional "weighted" in TREA
            # 3. Allow hyphen/space variations
            
            # Specific overrides for NBG/Eurobank weirdness
            clean_l = label.lower()
            if "common equity tier 1 ratio" in clean_l:
                clean_l = r"(common\s*equity\s*tier[ -]?1\s*ratio|cet\s*1\s*ratio)"
            elif "tier 1 capital ratio" in clean_l:
                clean_l = r"(tier[ -]?1\s*capital\s*ratio|tier\s*1\s*ratio)"
            elif "total capital ratio" in clean_l:
                clean_l = r"(total\s*capital\s*ratio)"
            elif "common equity tier 1" in clean_l and "ratio" not in clean_l:
                clean_l = r"(common\s*equity\s*tier[ -]?1|cet\s*1)"
            elif "tier 1 capital" in clean_l and "ratio" not in clean_l:
                clean_l = r"tier[ -]?1\s*capital"
            elif "total risk exposure" in clean_l:
                clean_l = r"total\s*risk\s*([ -]?weighted\s*)?exposure\s*amount"
            else:
                # Ultra-fuzzy character matching: allow optional spaces/dots between EVERY character
                # This handles cases like "CommonEquityTier1" or "C o m m o n E q u i t y"
                clean_label_chars = "".join(label.split())
                parts = [re.escape(c) for c in clean_label_chars]
                clean_l = r"[\s.]*".join(parts)
            
            # Final regex flags/adjustments
            label_regex = clean_l
            if "risk" in label.lower() and "exposure" in label.lower():
                label_regex = label_regex.replace(r"r[\s.]*i[\s.]*s[\s.]*k[\s.]*e[\s.]*x[\s.]*p[\s.]*o[\s.]*s[\s.]*u[\s.]*r[\s.]*e", 
                                                  r"risk[\s.]*([ -]?weighted[\s.]*)?exposure")
            
            # Make "1" optional in some common labels to handle Eurobank/Alpha omissions
            if "tier 1" in label.lower() or "cet 1" in label.lower():
                label_regex = label_regex.replace("1", "[1I]?")
            else:
                label_regex = label_regex.replace("1", "[1I]")
                
            label_regex = label_regex.replace("capital", r"capital\s*") # allow stuff after capital
            
            best_line = None
            best_source_page = target_page.page_number
            
            # Pass 1: Text-based matching (Fallback)
            # Find the best line by ID or Label
            for line_idx, (line, p_num) in enumerate(all_lines_with_meta):
                line_strip = line.strip()
                
                # KM1 Label-based ID Correction (even in text)
                clean_line = line.lower()
                if code == 'KM1':
                    # KM1 fix_map: Only for rows where banks consistently shift IDs (liquidity section)
                    km1_fix_map = {
                        r'liquidity\s*coverage\s*ratio': '17',
                        r'available\s*stable\s*funding': '18',
                        r'required\s*stable\s*funding': '19',
                        r'nsfr\s*ratio': '20',
                        r'net\s*cash\s*outflow': '16',
                        r'overall\s*capital\s*requirements?\s*\(%\)': '11a',
                        r'cash\s*outflows[ -]*total\s*weighted': 'EU 16a',
                        r'cash\s*inflows[ -]*total\s*weighted': 'EU 16b',
                        r'leverage\s*ratio\s*\(%\)': '14',
                        r'total\s*risk\s*weighted\s*exposure': '4',
                    }
                    for pattern, canonical_rid in km1_fix_map.items():
                        if re.search(pattern, clean_line):
                            if canonical_rid == rid:
                                # Must have extractable numbers (not just header lines)
                                line_numbers = re.findall(r'(?:-?\d[\d,.]*%?|\(\d[\d,.]*\))', line)
                                has_value_numbers = any('%' in n or float(re.sub(r'[^\d.]', '', n.replace(',', ''))) >= 50 for n in line_numbers if n.replace('.', '').replace(',', '').replace('%', '').replace('-', '').isdigit() or '%' in n)
                                if has_value_numbers:
                                    self.logger(f"      Matched {rid} by Label fix-map on line {line_idx}")
                                    best_line = line
                                    best_source_page = p_num
                                    break
                    if best_line: break

                # Standard ID matching
                # KM2 Eurobank fix: Allow '1Own' (missing space), but keep strict for KM1
                boundary = r'(?=\b|[A-Z])' if code == 'KM2' else r'\b'
                # KM2 Eurobank fix: Allow ID anywhere in line (due to header merge)
                anchor = r'(?:^|\s)' if code == 'KM2' else r'^'
                
                id_pattern = rf'{anchor}(\bEU[\s-]*|EU[\s\w]*\b)?{re.escape(rid)}{boundary}'
                # Skip lines that look like footers
                # Skip lines that look like footers (but careful of merged data)
                if re.search(r'Pillar\s*III|Disclosures|Consolidated', line, re.I):
                    continue
                    
                
                matched_id = False
                if re.search(id_pattern, line_strip, re.I):
                    matched_id = True
                    # Extra check for numeric IDs to avoid matching section numbers like "2.1.4"
                    if rid.isdigit():
                        # Check if the character after the ID match is a dot
                        # Use split/regex to be precise
                        after_match = re.sub(id_pattern, '', line_strip, count=1, flags=re.I)
                        if after_match and after_match.strip().startswith('.'):
                            matched_id = False
                
                if matched_id:
                    has_numbers = len(re.findall(r'-?\d[0-9,.]*', line)) > 0
                    label_match = re.search(label_regex, line, re.I)
                    
                    if label_match or (code == 'KM1' and has_numbers):
                        self.logger(f"      Matched {label} (RID {rid}) on line {line_idx} (ID priority)")
                        best_line = line
                        best_source_page = p_num
                        break

            
            # Pass 2: Fallback to fuzzy label match anywhere
            if not best_line:
                for line_idx, (line, p_num) in enumerate(all_lines_with_meta):
                    if re.search(label_regex, line, re.I):
                        # Strict Ratio check
                        is_tmpl_ratio = '%' in label or 'ratio' in label.lower()
                        has_ratio_indicator = '%' in line or 'ratio' in line.lower()
                        
                        if is_tmpl_ratio and not has_ratio_indicator:
                            continue
                        
                        self.logger(f"      Matched {label} (RID {rid}) on line {line_idx} (Fuzzy fallback)")
                        best_line = line
                        best_source_page = p_num
                        break
            
            if best_line:
                # Extract numeric value
                m = re.search(label_regex, best_line, re.I)
                data_part = best_line[m.end():] if m else best_line
                
                # Filter out small integers that look like row IDs
                numbers = re.findall(r'(?:-?\d[\d,.]*%?|\(\d[\d,.]*\))', data_part)
                
                # Vertical Table Check: If no numbers on this line, check next few lines
                if not numbers:
                    self.logger(f"      No numbers on match line, checking next lines...")
                    # Find which index this best_line was in all_lines_with_meta
                    for i_meta, (l_check, p_check) in enumerate(all_lines_with_meta):
                        if l_check == best_line and p_check == best_source_page:
                            # Look at next 5 lines on the same page
                            for offset in range(1, 6):
                                if i_meta + offset < len(all_lines_with_meta):
                                    next_l, next_p = all_lines_with_meta[i_meta + offset]
                                    if next_p == best_source_page:
                                        next_nums = re.findall(r'(?:-?\d[\d,.]*%?|\(\d[\d,.]*\))', next_l)
                                        if next_nums:
                                            numbers = next_nums
                                            self.logger(f"      Found numbers on line {i_meta + offset} (+{offset})")
                                            break
                            break
                
                valid_num = None
                for n_str in numbers:
                    val = clean_number(n_str)
                    if val is not None:
                        # Simple ratio check for pre-filtering
                        looks_like_ratio = "%" in n_str or val < 1.0
                        
                        # Ignore numbers that look like row IDs (usually < 50 if we expect millions)
                        if val < 50 and not looks_like_ratio:
                             continue
                        valid_num = val
                        val_str = n_str
                        break
                
                if valid_num is not None:
                    # Ratio detection
                    is_ratio = is_ratio_tmpl
                    if not is_ratio:
                        if "%" in val_str or ("ratio" in label.lower() and "exposure" not in label.lower() and "measure" not in label.lower()):
                            is_ratio = True
                    
                    # Apply report multiplier
                    # Sanity check for Unit/Scale:
                    # If raw number is very large (e.g. > 1 Million), it is indistinguishable from "Millions" logic (implies Trillions).
                    # Logic:
                    # - If > 1 Billion raw: Assume Absolute (Multiplier 1.0)
                    # - If > 1 Million raw and Scale is Millions: Assume Thousands (Multiplier 1000.0) - Fixes Piraeus
                    effective_multiplier = report_multiplier
                    if not is_ratio:
                        # Magnitude-based Scale Correction to normalize to "Millions" (Standard DB Unit)
                        
                        # Threshold based on template typical values
                        # IRRBB1 EVE usually < 10B. If > 10k detected, it's likely Thousands (not Millions).
                        # KM1 Capital usually > 1B. If > 1M detected, likely Thousands.
                        threshold = 50000 if code == 'IRRBB1' else 1000000
                        
                        # 1. If raw number > 1 Billion (and not IRRBB1 since 1B EVE rare): It's Absolute.
                        if abs(valid_num) >= 1000000000:
                             effective_multiplier = 0.000001
                        # 2. If raw number > Threshold:
                        #    It represents "Thousands". Convert to Millions (0.001).
                        elif abs(valid_num) > threshold:
                             effective_multiplier = 0.001

                    final_val = valid_num if is_ratio else valid_num * effective_multiplier
                        
                    # Normalize ratios (0.18 instead of 18) - use higher threshold to protect NSFR/LCR (usually 1.0-2.5)
                    if is_ratio and abs(final_val) >= 3.0 and abs(final_val) < 100:
                        final_val /= 100.0
                    
                    # IRRBB1 Multi-column Handling
                    if code == 'IRRBB1' and len(numbers) >= 2:
                        # Filter out Row ID if accidentally captured as a number (e.g. Eurobank "3 Steepener 3...")
                        try:
                            # Check first item. If matches Row ID, pop it.
                            # Use loose matching (3.0 == 3)
                            first_val = clean_number(numbers[0])
                            if first_val is not None:
                                # Row IDs for IRRBB1 are '1','2','3','4','5','6'.
                                if rid.isdigit() and abs(first_val - float(rid)) < 0.01:
                                    # It's likely the ID. Skip it.
                                    numbers = numbers[1:]
                        except:
                            pass
                            
                        if len(numbers) < 2: 
                             # If we filtered and now have < 2, falling back to standard extraction might be safer or just skip
                             pass

                        num_count = len(numbers)
                        if num_count > irrbb1_max_cols:
                            irrbb1_max_cols = num_count
                            
                        # EBA Template EU IRRBB1 has 4 columns:
                        # a: EVE Current, b: EVE Previous, c: NII Current, d: NII Previous
                        
                        idx_eve = 0
                        idx_nii = 1 # Default assumption (2-col layout)
                        
                        # Layout Detection Logic
                        if irrbb1_max_cols >= 4:
                            # 4-Column Layout detected (e.g. from Row 1)
                            if num_count >= 3:
                                idx_nii = 2 # (c) NII Current is Index 2
                            else:
                                idx_nii = None
                        elif num_count >= 3:
                            # Fallback if this is the first row but has 3+ numbers
                            idx_nii = 2
                        
                        # FORCE SKIP NII for Rows 3-6 (Steepener, Flattener, Short rates)
                        # User confirmed: "NII dimension only has Parallel up and Parallel down tests"
                        if rid in ['3', '4', '5', '6']:
                            idx_nii = None

                        eve_val = clean_number(numbers[idx_eve])
                        nii_val = clean_number(numbers[idx_nii]) if idx_nii is not None else None
                        
                        threshold_irrbb1 = 50000
                        
                        if eve_val is not None:
                            mult_eve = report_multiplier
                            if abs(eve_val) >= 1000000000: mult_eve = 0.000001
                            elif abs(eve_val) > threshold_irrbb1: mult_eve = 0.001
                            
                            extracted.append({
                                'template_code': code,
                                'row_id': rid,
                                'row_label': label,
                                'amount': eve_val * mult_eve,
                                'source_page': best_source_page,
                                'dimension': 'EVE'
                            })
                            
                        if nii_val is not None:
                            mult_nii = report_multiplier
                            if abs(nii_val) >= 1000000000: mult_nii = 0.000001
                            elif abs(nii_val) > threshold_irrbb1: mult_nii = 0.001
                            
                            extracted.append({
                                'template_code': code,
                                'row_id': rid,
                                'row_label': label,
                                'amount': nii_val * mult_nii,
                                'source_page': best_source_page,
                                'dimension': 'NII'
                            })
                        continue # Skip normal extraction
                        
                    extracted.append({
                        'template_code': code,
                        'row_id': rid,
                        'row_label': label,
                        'amount': final_val,
                        'source_page': best_source_page
                    })
        
        self.logger(f"    Extracted {len(extracted)} items for {code}")
        return extracted

    def get_template_rows(self, code):
        """Load row definitions from DB or fallback to hardcoded."""
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT row_id, row_label, is_ratio FROM pillar3_templates WHERE template_code = ?", (code,))
            rows = cur.fetchall()
            conn.close()
            
            if rows:
                return {r[0]: (r[1], r[2]) for r in rows}
        except Exception as e:
            self.logger(f"  [DB ERROR] Failed to load templates: {e}")

        # Fallback to hardcoded for critical templates if DB fails/empty
        KM1_ROWS = {
            '1': ('Common Equity Tier 1', '2520102'),
            '2': ('Tier 1 capital', '2520133'),
            '3': ('Total capital', '2520101'),
            '4': ('Total risk exposure amount', '2520138'),
            '5': ('Common Equity Tier 1 ratio', '2520146'),
            '6': ('Tier 1 ratio', '2520147'),
            '7': ('Total capital ratio', '2520148'),
            '8': ('Capital conservation buffer', None),
            '9': ('Institution specific countercyclical capital buffer', None),
            '11': ('Combined buffer requirement', None),
            '13': ('Leverage ratio total exposure measure', '2520903'),
            '14': ('Leverage ratio', '2520905'),
        }
        # ... rest of the hardcoded fallback
        MAP = {
            'KM1': KM1_ROWS,
        }
        return MAP.get(code, {})

if __name__ == "__main__":
    p = BlueprintPipeline('data/raw/Pillar3reports/2025-06-30_NBG.pdf')
    results = p.run()
    df = pd.DataFrame(results)
    print("\nExtraction Results (Snapshot):")
    if not df.empty:
        print(df.head(20).to_string())
