import sqlite3
import pandas as pd
import numpy as np

DB_PATH = 'eba_data.db'

# Map P3 LEIs to EBA LEIs
LEI_MAP = {
    'NLPK02SGC0U1AABDLL56': '213800DBQIB6VBNU5C64', # Alpha
    '635400L14KNHJ3DMBX37': '635400L14KNHZXPUZM19', # Cyprus
    'JEUVK5RWVJEN8W0C9M24': 'JEUVK5RWVJEN8W0C9M24', # Eurobank (Match)
    '5UMCZOEYKCVFAW8ZLO05': '5UMCZOEYKCVFAW8ZLO05', # NBG (Match)
    '213800OYHR4PPVA77574': 'M6AD1Y1KW32H8THQ6F76', # Piraeus
}

# Conversion: P3 (absolute) / EBA (millions) = 1,000,000
UNIT_FACTOR = 1_000_000

def run_validation():
    conn = sqlite3.connect(DB_PATH)
    
    print("Loading Dictionary...")
    dict_df = pd.read_sql("SELECT item_id, label, template FROM dictionary", conn)
    dict_map = dict_df.set_index('item_id')['label'].to_dict()
    
    print("Loading EBA Data (2025-06-30)...")
    eba_data = {} # (lei, item_id) -> amount
    
    for table in ['facts_oth', 'facts_cre', 'facts_mrk', 'facts_sov']:
        try:
            df = pd.read_sql(f"SELECT lei, item_id, amount FROM {table} WHERE period='2025-06-30'", conn)
            for _, row in df.iterrows():
                eba_data[(row['lei'], row['item_id'])] = row['amount']
        except Exception as e:
            print(f"Error loading {table}: {e}")
            
    # Also create reverse lookup per LEI: value -> [item_ids]
    eba_reverse = {} # lei -> {amount: [item_ids]}
    for (lei, item_id), amt in eba_data.items():
        if lei not in eba_reverse:
            eba_reverse[lei] = {}
        
        # Round amount to e.g. 2 decimal places in Millions logic for loose matching
        val = round(amt, 2)
        if val not in eba_reverse[lei]:
            eba_reverse[lei][val] = []
        eba_reverse[lei][val].append(item_id)
        
    print(f"Loaded {len(eba_data)} EBA data points.")
    
    print("Loading Pillar 3 Data (2025-06-30)...")
    p3_df = pd.read_sql("""
        SELECT * FROM facts_pillar3 
        WHERE period='2025-06-30'
    """, conn)
    
    print(f"Loaded {len(p3_df)} Pillar 3 data points.")
    
    matches_found = []
    
    validations = {
        'valid': 0,
        'invalid': 0,
        'missing_eba': 0
    }
    
    print("\n--- Validation & Search ---")
    
    for _, row in p3_df.iterrows():
        p3_lei = row['lei']
        eba_lei = LEI_MAP.get(p3_lei, p3_lei)
        
        mapped_id = row['eba_item_id']
        p3_val = row['amount']
        
        # Determine normalized P3 value in Millions
        p3_val_mil = p3_val / UNIT_FACTOR
        
        # 1. Validate Existing Mapping
        if mapped_id and mapped_id.strip() and mapped_id != 'None':
            eba_val = eba_data.get((eba_lei, mapped_id))
            if eba_val is not None:
                diff = abs(p3_val_mil - eba_val)
                pct_diff = diff / abs(eba_val) if eba_val != 0 else diff
                
                if pct_diff < 0.01: # 1% tolerance
                    validations['valid'] += 1
                else:
                    validations['invalid'] += 1
            else:
                validations['missing_eba'] += 1
        
        # 2. Search for Mapping (if not mapped or validation failed)
        # Search tolerance: 0.5% or absolute difference < 0.1M (100k)
        if eba_lei in eba_reverse:
            candidates = []
            
            # Simple linear search in reverse map nearby values ??
            # Or just precise match on rounded?
            # Let's iterate all values for this bank (usually < few thousands)
            for val, items in eba_reverse[eba_lei].items():
                if abs(val - p3_val_mil) < max(0.5, abs(p3_val_mil) * 0.005): # 0.5M diff or 0.5%
                    for item_id in items:
                        candidates.append((item_id, val))
            
            if candidates:
                # If mapped_id is already one of the candidates, ignore (already valid)
                candidate_ids = [c[0] for c in candidates]
                if mapped_id in candidate_ids:
                    continue
                
                # Check labels and Template compatibility
                for cid, cval in candidates:
                    label = dict_map.get(cid, "Unknown")
                    eba_tpl = dict_df[dict_df['item_id'] == cid]['template'].iloc[0] if cid in dict_df.index else ""
                    
                    # Fuzzy template match
                    match_tpl = False
                    if not eba_tpl:
                        match_tpl = True # If unknown, allow
                    elif row['template_code'] in str(eba_tpl) or str(eba_tpl) in row['template_code']:
                        match_tpl = True
                    elif 'KM1' in row['template_code'] and 'Solvency' in str(eba_tpl): # Example loose mapping
                        match_tpl = True
                    
                    if match_tpl:
                        matches_found.append({
                            'Bank': row['bank_name'],
                            'Template': row['template_code'],
                            'Row': row['row_id'],
                            'P3 Label': row['row_label'],
                            'P3 Value (M)': round(p3_val_mil, 2),
                            'EBA ID': cid,
                            'EBA Label': label,
                            'EBA Templ': eba_tpl,
                            'EBA Value': cval,
                            'Current Map': mapped_id
                        })

    report_lines = []
    report_lines.append("-" * 60)
    report_lines.append(f"Validations: {validations}")
    report_lines.append("-" * 60)
    
    report_lines.append(f"\nPotential New Mappings Found: {len(matches_found)}")
    
    unique_suggestions = {}
    
    for m in matches_found:
        key = (m['Template'], m['Row'])
        if key not in unique_suggestions:
            unique_suggestions[key] = []
        unique_suggestions[key].append(m)
        
    report_lines.append("\n--- Suggested Mappings ---")
    
    for (tpl, rid), matches in unique_suggestions.items():
        # Filter for good label matches
        good_matches = []
        for match in matches:
             p3_words = set(str(match['P3 Label']).lower().split())
             eba_words = set(str(match['EBA Label']).lower().split())
             common = p3_words.intersection(eba_words)
             meaningful = [w for w in common if len(w) > 3]
             
             if len(meaningful) >= 1 or (len(common) > 0 and len(match['P3 Label']) < 10):
                 good_matches.append(match)
        
        if good_matches:
            # Group by EBA ID to see consensus
            id_counts = {}
            for m in good_matches:
                cid = m['EBA ID']
                id_counts[cid] = id_counts.get(cid, 0) + 1
            
            # Pick most frequent
            best_id = max(id_counts, key=id_counts.get)
            best_match = next(m for m in good_matches if m['EBA ID'] == best_id)
            
            report_lines.append(f"{tpl} Row {rid}: '{best_match['P3 Label']}' == '{best_match['EBA Label']}' (ID: {best_match['EBA ID']}) [Tpl: {best_match['EBA Templ']}]")
            report_lines.append(f"   Value Match: {best_match['P3 Value (M)']} vs {best_match['EBA Value']} (Count: {id_counts[best_id]})")

    with open('mappings_report.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
        
    print("Report saved to mappings_report.txt")
    
    conn.close()

if __name__ == "__main__":
    run_validation()
