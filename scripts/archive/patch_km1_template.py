import sqlite3

def patch_km1_template():
    conn = sqlite3.connect('eba_data.db')
    cur = conn.cursor()
    
    # Missing or corrected rows for KM1
    rows = [
        ('11a', 'Overall capital requirements (%)', True),
        ('14a', 'Additional own funds requirements to address the risk of excessive leverage (%)', True),
        ('14b', 'of which: to be made up of CET1 capital (percentage points)', True),
        ('14c', 'Total SREP leverage ratio requirements (%)', True),
        ('14d', 'Leverage ratio buffer and overall leverage ratio requirement (%)', True),
        ('14e', 'Overall leverage ratio requirement (%)', True),
        ('EU 16a', 'Cash outflows - Total weighted value', False),
        ('EU 16b', 'Cash inflows - Total weighted value', False),
        ('16', 'Total net cash outflows (adjusted value)', False),
        ('17', 'Total net cash outflows (adjusted value)', False), 
        ('18', 'Liquidity coverage ratio (%)', True),
        ('19', 'Total available stable funding', False),
        ('20', 'Total required stable funding', False),
        ('21', 'NSFR ratio (%)', True),
    ]
    
    for rid, label, is_ratio in rows:
        cur.execute("""
            INSERT OR REPLACE INTO pillar3_templates (template_code, row_id, row_label, is_ratio)
            VALUES ('KM1', ?, ?, ?)
        """, (rid, label, is_ratio))
        
    conn.commit()
    conn.close()
    print("KM1 template patched.")

if __name__ == "__main__":
    patch_km1_template()
