import sqlite3
import pandas as pd
import numpy as np

DB_PATH = 'eba_data.db'
PERIOD = '2025-06-30'

# Re-use LEI Map
LEI_MAP = {
    'NBG': {'p3': '5UMCZOEYKCVFAW8ZLO05', 'tr': '5UMCZOEYKCVFAW8ZLO05'},
    'Eurobank': {'p3': 'JEUVK5RWVJEN8W0C9M24', 'tr': 'JEUVK5RWVJEN8W0C9M24'}
}

def apply_fuzzy_mappings():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    print("Finding and Applying Fuzzy Mappings...")
    
    updates = []
    
    # 1. Get All Unmapped Items for our target period, FOCUSING ON NBG
    # NBG LEI: 5UMCZOEYKCVFAW8ZLO05
    print("Focusing Fuzzy Logic on NBG Data (Most Expansive)...")
    p3_query = """
        SELECT f.template_code, f.row_id, f.row_label, f.amount, f.lei
        FROM facts_pillar3 f
        JOIN pillar3_dictionary d ON f.template_code = d.template_code AND f.row_id = d.row_id
        WHERE d.eba_item_id IS NULL AND f.period = ? AND f.amount != 0 AND f.lei = '5UMCZOEYKCVFAW8ZLO05'
    """
    p3_df = pd.read_sql(p3_query, conn, params=(PERIOD,))
    
    if p3_df.empty:
        print("No unmapped items found to process.")
        conn.close()
        return

    # 2. Get TR Data
    tr_query_all = f"""
        SELECT lei, item_id, amount FROM facts_oth WHERE period = '{PERIOD}'
        UNION ALL
        SELECT lei, item_id, amount FROM facts_cre WHERE period = '{PERIOD}'
    """
    tr_df_all = pd.read_sql(tr_query_all, conn)
    
    # 3. Match
    for _, row in p3_df.iterrows():
        lei = row['lei']
        # Find TR LEI
        tr_lei = None
        for k, v in LEI_MAP.items():
            if v['p3'] == lei: tr_lei = v['tr']
            
        if not tr_lei: continue
        
        tr_subset = tr_df_all[tr_df_all['lei'] == tr_lei]
        p3_val = row['amount']
        
        # Scaling check (Millions vs Raw)
        scales = [1, 1e6]
        
        best_match = None
        min_diff = 100
        
        for _, tr_row in tr_subset.iterrows():
            tr_val = tr_row['amount']
            if tr_val == 0: continue
            
            for s in scales:
                scaled_tr_val = tr_val * s
                diff = abs(p3_val - scaled_tr_val)
                pct = (diff / abs(scaled_tr_val)) * 100
                
                if pct < 0.5: # Strict 0.5% tolerance
                    if pct < min_diff:
                        min_diff = pct
                        best_match = tr_row['item_id']
        
        if best_match:
            # Check if this mapping is consistent (same label?)
            # We trust the amount match for now.
            # Avoid overwriting if we already queued this item
            if not any(u[0] == row['template_code'] and u[1] == row['row_id'] for u in updates):
                print(f"  Match: {row['template_code']}.{row['row_id']} ({row['row_label'][:20]}...) -> EBA {best_match} (Diff {min_diff:.2f}%)")
                updates.append((row['template_code'], row['row_id'], best_match))

    print(f"\nApplying {len(updates)} new mappings to the Database...")
    
    # Update pillar3_dictionary
    for tv, rid, eid in updates:
        cur.execute("UPDATE pillar3_dictionary SET eba_item_id = ? WHERE template_code = ? AND row_id = ?", (eid, tv, rid))
        
        # Update facts_pillar3 for consistency
        cur.execute("UPDATE facts_pillar3 SET eba_item_id = ? WHERE template_code = ? AND row_id = ?", (eid, tv, rid))

    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    apply_fuzzy_mappings()
