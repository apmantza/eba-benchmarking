import sqlite3
import pandas as pd

DB_PATH = 'eba_data.db'

def search_cc2():
    conn = sqlite3.connect(DB_PATH)
    
    # Search for keywords
    keywords = ['Intangible', 'Deferred', 'Equity', 'Liabilit']
    conditions = " OR ".join([f"label LIKE '%{k}%'" for k in keywords])
    
    query = f"SELECT * FROM dictionary WHERE {conditions}"
    df = pd.read_sql(query, conn)
    
    # Ensure item_id is numeric
    df['item_id'] = pd.to_numeric(df['item_id'], errors='coerce')
    
    print(f"Found {len(df)} candidate items in dictionary.")
    
    # Now check which of these actually have data in facts tables for Greek banks
    lei_map = {
        'NLPK02SGC0U1AABDLL56': '213800DBQIB6VBNU5C64', # Alpha
        'JEUVK5RWVJEN8W0C9M24': 'JEUVK5RWVJEN8W0C9M24', # Eurobank
        '5UMCZOEYKCVFAW8ZLO05': '5UMCZOEYKCVFAW8ZLO05', # NBG
        '213800OYHR4PPVA77574': 'M6AD1Y1KW32H8THQ6F76', # Piraeus
    }
    eba_leis = list(lei_map.values())
    placeholders = ','.join(['?']*len(eba_leis))
    
    # Get values for these candidates
    candidates = tuple(df['item_id'].dropna().unique().tolist())
    if not candidates:
        print("No candidates found.")
        return

    placeholders_ids = ','.join(['?']*len(candidates))
    
    data_query = f"""
        SELECT lei, item_id, amount, 'oth' as src FROM facts_oth WHERE period='2025-06-30' AND lei IN ({placeholders}) AND item_id IN ({placeholders_ids})
        UNION ALL
        SELECT lei, item_id, amount, 'cre' as src FROM facts_cre WHERE period='2025-06-30' AND lei IN ({placeholders}) AND item_id IN ({placeholders_ids})
    """
    
    # Params: LEIs + IDs + LEIs + IDs
    params = eba_leis + list(candidates) + eba_leis + list(candidates)
    
    try:
        data_df = pd.read_sql(data_query, conn, params=params)
    except Exception as e:
        print(f"Query failed: {e}")
        return

    # Merge labels
    data_df['item_id'] = pd.to_numeric(data_df['item_id'])
    merged = pd.merge(data_df, df, on='item_id', how='left')
    
    # Summarize by item
    summary = merged.groupby(['item_id', 'label'])['amount'].mean().reset_index().sort_values('amount', ascending=False)
    
    with open('cc2_candidates.txt', 'w', encoding='utf-8') as f:
        f.write("\nTop 50 Candidates by Mean Value:\n")
        f.write("-" * 80 + "\n")
        for _, row in summary.head(50).iterrows():
            f.write(f"ID: {row['item_id']} | Mean: {row['amount']:,.2f} | Label: {row['label']}\n")
            
            # Show specific bank values for debugging CC2 alignment
            subset = merged[merged['item_id'] == row['item_id']]
            for _, sub_row in subset.iterrows():
                 f.write(f"   > Bank {sub_row['lei'][-4:]}: {sub_row['amount']}\n")
            f.write("-" * 20 + "\n")
        
    conn.close()
    print("Done. See cc2_candidates.txt")

if __name__ == "__main__":
    search_cc2()
