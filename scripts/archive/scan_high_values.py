import sqlite3
import pandas as pd

DB_PATH = 'eba_data.db'

LEI_MAP = {
    'NLPK02SGC0U1AABDLL56': '213800DBQIB6VBNU5C64', # Alpha
    'JEUVK5RWVJEN8W0C9M24': 'JEUVK5RWVJEN8W0C9M24', # Eurobank
    '5UMCZOEYKCVFAW8ZLO05': '5UMCZOEYKCVFAW8ZLO05', # NBG
    '213800OYHR4PPVA77574': 'M6AD1Y1KW32H8THQ6F76', # Piraeus
    '635400L14KNHJ3DMBX37': '635400L14KNHZXPUZM19', # Cyprus
}

def scan_high_values():
    conn = sqlite3.connect(DB_PATH)
    
    eba_leis = list(LEI_MAP.values())
    placeholders = ','.join(['?']*len(eba_leis))
    
    query = f"""
        SELECT lei, item_id, amount, 'oth' as source FROM facts_oth WHERE period='2025-06-30' AND lei IN ({placeholders}) AND amount > 5000
        UNION ALL
        SELECT lei, item_id, amount, 'cre' as source FROM facts_cre WHERE period='2025-06-30' AND lei IN ({placeholders}) AND amount > 5000
        UNION ALL
        SELECT lei, item_id, amount, 'mrk' as source FROM facts_mrk WHERE period='2025-06-30' AND lei IN ({placeholders}) AND amount > 5000
    """
    
    df = pd.read_sql(query, conn, params=eba_leis * 3)
    
    # Get labels
    dict_df = pd.read_sql("SELECT item_id, label FROM dictionary", conn)
    dict_map = dict_df.set_index('item_id')['label'].to_dict()
    
    # Group by item
    items = df.groupby('item_id')['amount'].agg(['count', 'mean', 'max']).reset_index()
    items['label'] = items['item_id'].map(dict_map)
    
    # Sort by mean value descending
    items = items.sort_values('mean', ascending=False)
    
    with open('high_values.txt', 'w', encoding='utf-8') as f:
        f.write(f"Found {len(items)} items with values > 5000 M for Greek banks.\n")
        f.write("-" * 80 + "\n")
        for _, row in items.head(50).iterrows():
            label = row['label'] if row['label'] else "Unknown"
            if len(label) > 100: # allow longer labels in file
                 label = label[:97] + "..."
            f.write(f"ID: {row['item_id']} | Mean: {row['mean']:,.0f} | Max: {row['max']:,.0f} | Label: {label}\n")
        f.write("-" * 80 + "\n")
    
    print("Done. See high_values.txt")
    
    conn.close()

if __name__ == "__main__":
    scan_high_values()
