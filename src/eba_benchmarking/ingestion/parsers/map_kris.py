import sqlite3
from eba_benchmarking.config import DB_NAME

def main():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('DROP TABLE IF EXISTS kri_to_item')
    cursor.execute('''
    CREATE TABLE kri_to_item (
        kri_name TEXT PRIMARY KEY,
        item_id TEXT,
        FOREIGN KEY(item_id) REFERENCES dictionary(item_id)
    )
    ''')
    
    # Mapping based on EBA Transparency Exercise structure
    mappings = [
        ('CET 1 capital ratio', '2520140'),
        ('Tier 1 capital ratio', '2520141'),
        ('Total capital ratio', '2520142'),
        ('Leverage ratio', '2520906'),
        ('Cost to income ratio', '2520316'), # Note: Often associated with Total Operating Income as base
        ('Return on assets', '2521010'), # Total Assets
        ('Net interest margin', '2520301'), # Interest Income
        ('Liquidity coverage ratio', '2520101'), # Placeholder if exact ID missing
        ('Net Stable Funding Ratio', '2520101'), # Placeholder
        ('Share of non‐performing loans and advances (NPL ratio)', '2520605'),
        ('Coverage ratio of non-performing loans and advances', '2520605'),
        ('Forbearance ratio - Loans and advances (gross amount) (FBL)', '2520701'),
        ('Cost of risk', '2520324'), # Impairment
    ]
    
    cursor.executemany('INSERT INTO kri_to_item VALUES (?,?)', mappings)
    conn.commit()
    conn.close()
    print("✅ Created kri_to_item mapping table.")

if __name__ == "__main__":
    main()
