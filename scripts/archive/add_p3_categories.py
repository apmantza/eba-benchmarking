import sqlite3

def add_categories():
    conn = sqlite3.connect('eba_data.db')
    cur = conn.cursor()
    
    print("Adding category column to pillar3_dictionary...")
    
    # 0. Populate dictionary from extracted facts if empty
    # We use facts_pillar3 to find all unique (template, row_id) pairs
    cur.execute("SELECT count(*) FROM pillar3_dictionary")
    if cur.fetchone()[0] == 0:
        print("Populating pillar3_dictionary from facts_pillar3...")
        cur.execute("""
            INSERT OR IGNORE INTO pillar3_dictionary (template_code, row_id, p3_label, eba_item_id)
            SELECT DISTINCT template_code, row_id, row_label, eba_item_id
            FROM facts_pillar3
        """)
        print(f"Inserted {cur.rowcount} items.")

    # 1. Add Column (Wrap in try/except in case exists)
    try:
        cur.execute("ALTER TABLE pillar3_dictionary ADD COLUMN category TEXT")
        print("Column 'category' added.")
    except sqlite3.OperationalError as e:
        print(f"Column already exists or error: {e}")
        
    # 2. Update Categories from EBA Dictionary
    print("Updating categories...")
    # SQLite supports UPDATE FROM in newer versions, else use subquery
    sql = """
        UPDATE pillar3_dictionary
        SET category = (
            SELECT category 
            FROM dictionary 
            WHERE dictionary.item_id = pillar3_dictionary.eba_item_id
        )
        WHERE eba_item_id IS NOT NULL
    """
    cur.execute(sql)
    rows = cur.rowcount
    print(f"Updated {rows} rows with categories.")
    
    # 4. KM1 Granular Categorization
    print("Applying KM1 sub-categories...")
    def get_km1_cat(rid):
        import re
        m = re.search(r'(\d+)', str(rid))
        if not m: return "Capital"
        num = int(m.group(1))
        if num < 13: return "Capital"
        if num < 15: return "Leverage"
        return "Liquidity"

    cur.execute("SELECT row_id FROM pillar3_dictionary WHERE template_code = 'KM1'")
    for (rid,) in cur.fetchall():
        cat = get_km1_cat(rid)
        cur.execute("UPDATE pillar3_dictionary SET category = ? WHERE template_code = 'KM1' AND row_id = ?", (cat, rid))

    # 5. Fill missing categories for other templates
    updates = [
        ("Capital", "CC1"),
        ("Capital", "CC2"),
        ("Liquidity", "LIQ1"),
        ("Liquidity", "LIQ2"),
        ("Credit Risk", "CR1"),
        ("Credit Risk", "CR3"),
        ("Market Risk", "MR1"),
        ("Leverage", "LR1"),
        ("Leverage", "LR2"),
        ("Leverage", "LR3"),
        ("Market Risk", "IRRBB1"),
    ]
    
    for cat, tpl in updates:
        cur.execute("UPDATE pillar3_dictionary SET category = ? WHERE template_code = ? AND category IS NULL", (cat, tpl))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_categories()
