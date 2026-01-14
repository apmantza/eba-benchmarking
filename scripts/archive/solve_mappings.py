import sqlite3
import pandas as pd
import numpy as np

DB_PATH = 'eba_data.db'

# Map P3 LEIs to EBA LEIs
# Alpha, Eurobank, NBG, Piraeus
LEI_MAP = {
    'NLPK02SGC0U1AABDLL56': '213800DBQIB6VBNU5C64', # Alpha
    'JEUVK5RWVJEN8W0C9M24': 'JEUVK5RWVJEN8W0C9M24', # Eurobank
    '5UMCZOEYKCVFAW8ZLO05': '5UMCZOEYKCVFAW8ZLO05', # NBG
    '213800OYHR4PPVA77574': 'M6AD1Y1KW32H8THQ6F76', # Piraeus
    '635400L14KNHJ3DMBX37': '635400L14KNHZXPUZM19', # Cyprus
}

TARGETS = [
    ('LIQ1', '21'),
    ('LIQ1', '22'),
    ('LIQ1', '23'),
    ('LIQ2', '27'),
    ('CC2', '2'),
    ('CC2', '3'),
    ('LIQ1', 'EU-19a'),
    ('LIQ1', '1')
]

# EBA is in Millions, P3 in Absolute. Factor = 1,000,000
UNIT_FACTOR = 1_000_000

def find_matches():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Get dictionary labels
    dict_df = pd.read_sql("SELECT item_id, label FROM dictionary", conn)
    dict_map = dict_df.set_index('item_id')['label'].to_dict()
    
    # 2. Get All EBA Data for our banks
    print("Loading EBA Data...")
    eba_leis = list(LEI_MAP.values())
    placeholders = ','.join(['?']*len(eba_leis))
    query = f"""
        SELECT lei, item_id, amount 
        FROM facts_oth 
        WHERE period='2025-06-30' AND lei IN ({placeholders})
        UNION ALL
        SELECT lei, item_id, amount 
        FROM facts_cre 
        WHERE period='2025-06-30' AND lei IN ({placeholders})
        UNION ALL
        SELECT lei, item_id, amount 
        FROM facts_mrk 
        WHERE period='2025-06-30' AND lei IN ({placeholders})
    """
    eba_df = pd.read_sql(query, conn, params=eba_leis * 3)
    
    # Ensure item_id is integer
    eba_df['item_id'] = pd.to_numeric(eba_df['item_id'], errors='coerce')
    dict_df['item_id'] = pd.to_numeric(dict_df['item_id'], errors='coerce')
    dict_map = dict_df.set_index('item_id')['label'].to_dict()
    
    # Organize EBA: Item -> {LEI -> Value}
    eba_items = {}
    for _, row in eba_df.iterrows():
        iid = row['item_id']
        if pd.isna(iid): continue # Skip invalid IDs
        iid = int(iid)
        if iid not in eba_items:
            eba_items[iid] = {}
        eba_items[iid][row['lei']] = row['amount']
        
    print(f"Loaded {len(eba_items)} unique EBA items.")

    # 3. Get P3 Data for Targets
    print("Loading Pillar 3 Data...")
    p3_df = pd.read_sql(f"SELECT * FROM facts_pillar3 WHERE period='2025-06-30'", conn)
    
    with open('mapping_solutions.txt', 'w', encoding='utf-8') as f:
        for tpl, rid in TARGETS:
            subset = p3_df[(p3_df['template_code'] == tpl) & (p3_df['row_id'] == rid)]
            if subset.empty:
                f.write(f"\n{tpl} Row {rid}: No P3 Data.\n")
                continue
            
            p3_values = {} # EBA_LEI -> P3_Value_Millions
            labels = set()
            
            for _, row in subset.iterrows():
                if row['lei'] in LEI_MAP:
                    eba_lei = LEI_MAP[row['lei']]
                    val_mil = row['amount'] / UNIT_FACTOR
                    p3_values[eba_lei] = val_mil
                    labels.add(row['row_label'])
            
            f.write(f"\n------------------------------------------------\n")
            f.write(f"Target: {tpl} Row {rid} ({', '.join(labels)})\n")
            f.write(f"P3 Values (M): { {k[-4:]: round(v, 2) for k,v in p3_values.items()} }\n")
            
            # Find Best EBA Match
            best_candidates = []
            
            # defined keywords for semantic filtering
            keywords = []
            if 'LIQ' in tpl:
                keywords = ['Liquidity', 'LCR', 'NSFR', 'HQLA', 'Cash', 'Outflow', 'Inflow', 'Funding', 'Store']
            elif 'CC2' in tpl:
                keywords = ['Asset', 'Liabilit', 'Equity', 'Capital', 'Balance']
            
            p3_vals_clean = {k:v for k,v in p3_values.items() if abs(v) > 0.01}
            if not p3_vals_clean:
                f.write("  No non-zero P3 values to match.\n")
                continue
                
            for eba_id, eba_vals in eba_items.items():
                label = dict_map.get(eba_id, "Unknown")
                
                # 1. Semantic Filter
                if keywords:
                    if not any(k.lower() in label.lower() for k in keywords):
                        continue
                
                # 2. Numeric Match
                # Check for common non-zero banks
                common_keys = [k for k in p3_vals_clean.keys() if k in eba_vals]
                # Filter out NaN EBA values from common keys
                common_leis = []
                for k in common_keys:
                    val = eba_vals[k]
                    if val is not None and not (isinstance(val, float) and np.isnan(val)):
                        common_leis.append(k)

                if not common_leis: # Need at least 1 common valid value
                     continue
                
                # We need to test different scaling factors because EBA data might be in different units than we think
                factors = [1.0, 100.0, 0.01, 1000.0] 
                
                matched_factor = None
                min_avg_diff = float('inf')
                valid_count = 0
                
                for factor in factors:
                    current_valid_count = 0
                    current_total_diff = 0
                    is_valid_factor = True
                    
                    for lei in common_leis:
                        p3 = p3_vals_clean[lei]
                        eba = eba_vals[lei]
                        
                        # Check for strict zero
                        if abs(eba) < 0.0001: 
                            is_valid_factor = False 
                            break
                        
                        val_eba_adj = eba * factor
                        
                        diff = abs(p3 - val_eba_adj)
                        avg = (abs(p3) + abs(val_eba_adj)) / 2
                        
                        # Tolerance: 5% relative or 2.0 absolute
                        if diff > 2.0 and diff / avg > 0.05:
                            is_valid_factor = False
                            break
                            
                        current_total_diff += diff
                        current_valid_count += 1
                    
                    if is_valid_factor and current_valid_count > 0:
                         matched_factor = factor
                         valid_count = current_valid_count
                         min_avg_diff = current_total_diff / current_valid_count
                         break # Found a working factor
                
                if matched_factor is not None:
                     best_candidates.append((eba_id, label, min_avg_diff, valid_count, matched_factor))

            best_candidates.sort(key=lambda x: (x[2], -x[3]))
            
            if best_candidates:
                f.write(f"Matches Found (Top 5):\n")
                for cid, lbl, diff, count, fact in best_candidates[:5]:
                    f.write(f"  [ID: {cid}] Diff: {diff:.4f} (Banks: {count}, Factor: {fact}) Label: {lbl}\n")
                    # Show value comparison
                    example_lei = common_leis[0] if common_leis else list(p3_vals_clean.keys())[0]
                    if example_lei in eba_items[cid]:
                        p3_v = p3_vals_clean[example_lei]
                        eba_v = eba_items[cid][example_lei]
                        f.write(f"     Ex: P3={p3_v:.2f}, EBA={eba_v:.2f} -> Match if EBA*{fact}\n")
            else:
                f.write("  No valid match found.\n")

    conn.close()
    print("Done. See mapping_solutions.txt")

if __name__ == "__main__":
    find_matches()
