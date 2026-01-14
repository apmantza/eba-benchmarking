import sqlite3

conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()

print("=" * 80)
print("PILLAR III EXTRACTION - GAP ANALYSIS")
print("=" * 80)

# Get dictionary items
cur.execute("""
    SELECT p3_item_id, template_code, p3_label, eba_item_id
    FROM pillar3_dictionary 
    WHERE eba_item_id IS NOT NULL
    ORDER BY template_code, row_id
""")
dict_items = cur.fetchall()

# For each bank, show which key items are missing
banks = ['NBG', 'Alpha Bank', 'Eurobank', 'Piraeus', 'Bank of Cyprus']

# Focus on the most critical items (KM1 rows 1-7, 13-14)
critical_items = [
    'KM1.1', 'KM1.2', 'KM1.3', 'KM1.4', 'KM1.4a',
    'KM1.5', 'KM1.6', 'KM1.7', 'KM1.13', 'KM1.14',
    'CC1.29', 'CC1.44', 'CC1.58'
]

print("\n=== CRITICAL KM1/CC1 COVERAGE ===\n")
print(f"{'Item':<12} | " + " | ".join([f"{b[:10]:>10}" for b in banks]))
print("-" * 75)

for item in critical_items:
    parts = item.split('.')
    template = parts[0]
    row_id = parts[1] if len(parts) > 1 else ''
    
    row_data = [item]
    for bank in banks:
        cur.execute("""
            SELECT amount FROM facts_pillar3 
            WHERE bank_name = ? AND template_code = ? AND row_id = ?
            ORDER BY period DESC LIMIT 1
        """, (bank, template, row_id))
        result = cur.fetchone()
        if result and result[0]:
            # Format as billions if large
            amt = result[0]
            if abs(amt) > 1_000_000_000:
                row_data.append(f"{amt/1e9:.1f}B")
            elif abs(amt) < 2:
                row_data.append(f"{amt*100:.1f}%")
            else:
                row_data.append(f"{amt/1e6:.0f}M")
        else:
            row_data.append("✗")
    
    print(f"{row_data[0]:<12} | " + " | ".join([f"{d:>10}" for d in row_data[1:]]))

# Summary
print("\n\n=== EXTRACTION STATUS ===\n")
for bank in banks:
    cur.execute("""
        SELECT COUNT(DISTINCT template_code || '.' || row_id) 
        FROM facts_pillar3 
        WHERE bank_name = ? AND eba_item_id IS NOT NULL
    """, (bank,))
    mapped = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COUNT(DISTINCT template_code) 
        FROM facts_pillar3 
        WHERE bank_name = ?
    """, (bank,))
    templates = cur.fetchone()[0]
    
    status = "✓ Good" if mapped > 30 else "⚠ Partial" if mapped > 10 else "✗ Poor"
    print(f"{bank:<20}: {mapped:>3} mapped items from {templates:>2} templates - {status}")

print("\n\n=== RECOMMENDED FIXES ===")
print("""
1. EUROBANK: PDF table extraction is fragmented. KM1/CC1 pages not detected.
   - Add explicit page targeting using index: KM1 is on page 20
   - Consider OCR-based extraction or Excel fallback

2. PIRAEUS: Has Excel data but CC1 template not in PDF/Excel
   - Check if CC1 is in a different location in their reports
   
3. ALPHA BANK: Missing many CC1 rows (7-27)
   - The values are being extracted but row_ids not matching

4. ALL BANKS: Ensure row_id normalization (remove spaces, handle EU- prefix)
""")

conn.close()
