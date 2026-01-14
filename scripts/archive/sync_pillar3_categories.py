import sqlite3
import pandas as pd

DB_PATH = 'eba_data.db'

# Define category fallbacks based on Template prefix
TEMPLATE_CATEGORIES = {
    'KM': 'Capital',
    'CC': 'Capital',
    'LR': 'Leverage',
    'LIQ': 'Liquidity',
    'CR': 'Credit Risk',
    'CQ': 'Asset Quality',
    'CCR': 'Counterparty Credit Risk',
    'CVA': 'Counterparty Credit Risk',
    'MR': 'Market Risk',
    'OV': 'RWA',
    'SEC': 'Securitisation',
    'IRRBB': 'Interest Rate Risk',
    'CRE': 'Credit Risk',
    'ESG': 'ESG',
    'TAXONOMY': 'ESG'
}

def get_fallback_category(tpl):
    # Sort prefixes by length descending to match longest first (e.g. CCR before CC)
    for prefix, cat in sorted(TEMPLATE_CATEGORIES.items(), key=lambda x: len(x[0]), reverse=True):
        if tpl.startswith(prefix):
            return cat
    return 'Other'

def sync():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Load EBA Dictionary for official categories
    print("Loading EBA Dictionary...")
    eba_dict = pd.read_sql("SELECT item_id, category FROM dictionary", conn)
    eba_cat_map = eba_dict.set_index('item_id')['category'].to_dict()
    
    # 2. Load Distinct Items from facts_pillar3
    print("Loading Distinct Pillar 3 Items...")
    query = """
    SELECT DISTINCT template_code, row_id, row_label, eba_item_id, is_new_metric
    FROM facts_pillar3
    """
    p3_items = pd.read_sql(query, conn)
    # Deduplicate by ID
    p3_items = p3_items.drop_duplicates(subset=['template_code', 'row_id'])
    
    print(f"Found {len(p3_items)} distinct items (deduplicated).")
    
    # 3. Determine Category for each
    categories = []
    for _, row in p3_items.iterrows():
        cat = None
        eba_id = row['eba_item_id']
        
        # Try EBA map first
        if eba_id and eba_id in eba_cat_map:
            cat = eba_cat_map[eba_id]
        
        # Fallback to Template map
        if not cat:
            cat = get_fallback_category(row['template_code'])
            
        categories.append(cat)
    
    p3_items['category'] = categories
    
    # 4. Update pillar3_dictionary table
    # We'll truncate and repopulate to be clean
    print("Updating pillar3_dictionary table...")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pillar3_dictionary")
    
    for _, row in p3_items.iterrows():
        p3_id = f"{row['template_code']}_{row['row_id']}"
        cursor.execute("""
            INSERT INTO pillar3_dictionary 
            (p3_item_id, template_code, row_id, p3_label, eba_item_id, notes, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            p3_id,
            row['template_code'], 
            row['row_id'], 
            row['row_label'], 
            row['eba_item_id'], 
            '', # Notes
            row['category']
        ))
    
    conn.commit()
    print("pillar3_dictionary updated.")
    
    conn.close()
    
    # 5. Run md generation
    print("Regenerating Markdown...")
    import generate_dictionary_md
    generate_dictionary_md.generate_md()

if __name__ == "__main__":
    sync()
