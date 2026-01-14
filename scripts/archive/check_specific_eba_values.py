import sqlite3
import pandas as pd

DB_PATH = 'eba_data.db'

# Alpha, Eurobank, NBG, Piraeus, Cyprus
LEI_MAP = {
    'NLPK02SGC0U1AABDLL56': '213800DBQIB6VBNU5C64', # Alpha
    'JEUVK5RWVJEN8W0C9M24': 'JEUVK5RWVJEN8W0C9M24', # Eurobank
    '5UMCZOEYKCVFAW8ZLO05': '5UMCZOEYKCVFAW8ZLO05', # NBG
    '213800OYHR4PPVA77574': 'M6AD1Y1KW32H8THQ6F76', # Piraeus
    '635400L14KNHJ3DMBX37': '635400L14KNHZXPUZM19', # Cyprus
}

ITEMS_TO_CHECK = [
    2521216, # Total Equity
    2521214, # Total Liabilities
    2521001, # Cash
    2520602, # Debt Securities
    2520101, # Own Funds
    2520143, # CET1 
]

def check_values():
    conn = sqlite3.connect(DB_PATH)
    
    eba_leis = list(LEI_MAP.values())
    placeholders = ','.join(['?']*len(eba_leis))
    
    tables = ['facts_oth', 'facts_cre', 'facts_mrk']
    
    with open('eba_missing_debug.txt', 'w', encoding='utf-8') as f:
        for table in tables:
            f.write(f"Scanning {table}...\n")
            query = f"SELECT lei, item_id, amount FROM {table} WHERE period='2025-06-30' AND lei IN ({placeholders})"
            df = pd.read_sql(query, conn, params=eba_leis)
            
            f.write(f"  Loaded {len(df)} rows.\n")
            f.write(f"  Types: {df.dtypes}\n")
            
            for iid in ITEMS_TO_CHECK:
                subset = df[df['item_id'] == iid]
                if not subset.empty:
                    f.write(f"  FOUND {iid} in {table}:\n")
                    for _, row in subset.iterrows():
                        # Identify bank
                        bank = "Unknown"
                        for k,v in LEI_MAP.items():
                            if v == row['lei']:
                                bank = v[-4:] # Suffix
                        f.write(f"    Bank {bank}: {row['amount']:,.2f}\n")
                else:
                    # f.write(f"  Item {iid} NOT found in {table}.\n")
                    pass
        f.write("Done.\n")
    
    conn.close()
    print("Done. See eba_missing_debug.txt")

if __name__ == "__main__":
    check_values()
