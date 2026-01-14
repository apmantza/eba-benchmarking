import sqlite3

def patch_km1_template_v2():
    conn = sqlite3.connect('eba_data.db')
    cur = conn.cursor()
    
    # Standard EBA KM1 rows
    rows = [
        ('11a', 'Overall capital requirements (%)', True),
        ('EU 11a', 'Overall capital requirements (%)', True),
        ('14a', 'Additional own funds requirements to address the risk of excessive leverage (%)', True),
        ('14b', 'of which: to be made up of CET1 capital (percentage points)', True),
        ('14c', 'Total SREP leverage ratio requirements (%)', True),
        ('14d', 'Leverage ratio buffer and overall leverage ratio requirement (%)', True),
        ('14e', 'Overall leverage ratio requirement (%)', True),
        ('15', 'Total high-quality liquid assets (HQLA) (Weighted value -average)', False),
        ('EU 16a', 'Cash outflows - Total weighted value', False),
        ('EU 16b', 'Cash inflows - Total weighted value', False),
        ('16', 'Total net cash outflows (adjusted value)', False),
        ('17', 'Liquidity coverage ratio (%)', True),
        ('18', 'Total available stable funding', False),
        ('19', 'Total required stable funding', False),
        ('20', 'NSFR ratio (%)', True),
    ]
    
    # Remove the bad ones I added earlier (like 21)
    cur.execute("DELETE FROM pillar3_templates WHERE template_code='KM1' AND row_id IN ('21')")
    
    for rid, label, is_ratio in rows:
        cur.execute("""
            INSERT OR REPLACE INTO pillar3_templates (template_code, row_id, row_label, is_ratio)
            VALUES ('KM1', ?, ?, ?)
        """, (rid, label, is_ratio))
        
    conn.commit()
    conn.close()
    print("KM1 template (v2) patched.")

if __name__ == "__main__":
    patch_km1_template_v2()
