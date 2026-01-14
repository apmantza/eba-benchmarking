import sqlite3
import pandas as pd
import numpy as np

DB_PATH = 'eba_data.db'
PERIOD = '2025-06-30'

# Mapping P3 LEI -> TR LEI
LEI_MAP = {
    'NBG': {
        'p3': '5UMCZOEYKCVFAW8ZLO05', 
        'tr': '5UMCZOEYKCVFAW8ZLO05'
    },
    'Alpha': {
        'p3': 'KLQDKFP5ACPO4FAJ9Y58', 
        'tr': '213800DBQIB6VBNU5C64'
    },
    'Eurobank': {
        'p3': 'JEUVK5RWVJEN8W0C9M24', 
        'tr': 'JEUVK5RWVJEN8W0C9M24'
    },
    'Piraeus': {
        'p3': '213800OYHR1MPQ5VJL60', 
        'tr': 'M6AD1Y1KW32H8THQ6F76' # Financial Holdings
    }
}

def check_fuzzy_match(p3_val, tr_df):
    """Finds TR items that match p3_val within 1%."""
    if p3_val == 0: return []
    
    matches = []
    for _, row in tr_df.iterrows():
        tr_val = row['amount']
        if tr_val == 0: continue
        
        # Scaling factors: 1 (Millions vs Millions), 1e6 (Raw vs Millions), 1e3 (Thousands vs Millions)
        scales = [1, 1e6, 1e3, 0.001]
        
        for s in scales:
            scaled_tr = tr_val * s
            diff = abs(p3_val - scaled_tr)
            pct = (diff / abs(scaled_tr)) * 100
            
            if pct < 1.0: # 1% tolerance
                matches.append((row['item_id'], scaled_tr, pct))
    return matches

def validate():
    conn = sqlite3.connect(DB_PATH)
    
    print(f"Validation for Period: {PERIOD}")
    
    for bank_name, leis in LEI_MAP.items():
        p3_lei = leis['p3']
        tr_lei = leis['tr']
        
        print(f"\n--- {bank_name} ---")
        
        # Get Pillar 3 Data
        p3_query = f"""
            SELECT row_id, row_label, eba_item_id, amount
            FROM facts_pillar3
            WHERE lei = '{p3_lei}' AND period = '{PERIOD}'
        """
        p3_df = pd.read_sql(p3_query, conn)
        
        if p3_df.empty:
            print(f"No Pillar 3 data found.")
            continue
            
        # Get TR Data (Combine facts_oth and facts_cre)
        tr_query = f"""
            SELECT item_id, amount FROM facts_oth WHERE lei = '{tr_lei}' AND period = '{PERIOD}'
            UNION ALL
            SELECT item_id, amount FROM facts_cre WHERE lei = '{tr_lei}' AND period = '{PERIOD}'
        """
        tr_df = pd.read_sql(tr_query, conn)
        
        if tr_df.empty:
            print(f"No TR data found for LEI {tr_lei}")
            continue
            
        # 1. Check Existing Mappings
        print(f"Checking Mapped Items:")
        mapped_p3 = p3_df[p3_df['eba_item_id'].notnull()]
        
        for _, row in mapped_p3.iterrows():
            eba_id = row['eba_item_id']
            p3_val = row['amount']
            
            tr_match = tr_df[tr_df['item_id'] == eba_id]
            if not tr_match.empty:
                tr_val = tr_match.iloc[0]['amount']
                # Auto-scale
                tr_val_scaled = tr_val * 1e6 if p3_val > tr_val * 1000 else tr_val
                
                diff = 0
                if tr_val_scaled != 0:
                    diff = ((p3_val - tr_val_scaled) / tr_val_scaled) * 100
                elif p3_val != 0:
                     diff = 100
                
                status = "OK" if abs(diff) < 1 else "DIFF"
                print(f"  {eba_id:<8} | P3: {p3_val:15,.0f} | TR: {tr_val_scaled:15,.0f} | {diff:6.1f}% | {status}")
            else:
                pass # print(f"  {eba_id:<8} | Not found in TR")

        # 2. Fuzzy Logic for Unmapped Items
        print(f"Fuzzy Matching for Unmapped Items:")
        unmapped_p3 = p3_df
        # We define unmapped as EBA ID is None, OR EBA ID is set but we want to verify?
        # User said "fuzzy logic ... if any more items could be mapped".
        # So look at items with eba_item_id IS NULL.
        unmapped_real = p3_df[p3_df['eba_item_id'].isnull()]
        
        count_fuzzy = 0
        for _, row in unmapped_real.iterrows():
            val = row['amount']
            label = row['row_label'] or str(row['row_id'])
            
            matches = check_fuzzy_match(val, tr_df)
            if matches:
                 for mid, mval, mpct in matches:
                     print(f"  ? P3 '{label}' ({val:,.0f}) ~= TR {mid} ({mval:,.0f}) [Diff {mpct:.1f}%]")
                     count_fuzzy += 1
        
        if count_fuzzy == 0:
            print("  No fuzzy matches found.")

    conn.close()

if __name__ == "__main__":
    validate()
