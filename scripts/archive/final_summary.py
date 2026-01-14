import sqlite3

conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()

print("=" * 80)
print("PILLAR III DATA EXTRACTION SUMMARY")
print("=" * 80)

# Summary by bank with unique item counts
print("\n=== DATA EXTRACTION BY BANK ===\n")
cur.execute("""
    SELECT bank_name, 
           COUNT(*) as total_records,
           SUM(CASE WHEN eba_item_id IS NOT NULL THEN 1 ELSE 0 END) as records_with_eba,
           COUNT(DISTINCT template_code || '.' || row_id) as unique_p3_items,
           COUNT(DISTINCT CASE WHEN eba_item_id IS NOT NULL THEN template_code || '.' || row_id END) as mapped_p3_items,
           COUNT(DISTINCT period) as periods
    FROM facts_pillar3
    GROUP BY bank_name
    ORDER BY total_records DESC
""")
print(f"{'Bank':<22} | {'Records':>8} | {'Periods':>7} | {'P3 Items':>8} | {'Mapped':>6}")
print("-" * 65)
for r in cur.fetchall():
    print(f"{r[0]:<22} | {r[1]:>8} | {r[5]:>7} | {r[3]:>8} | {r[4]:>6}")

# Summary of mapping coverage
print("\n\n=== MAPPING DICTIONARY COVERAGE ===\n")
cur.execute("SELECT COUNT(*) FROM pillar3_dictionary")
dict_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM pillar3_dictionary WHERE eba_item_id IS NOT NULL")
dict_mapped = cur.fetchone()[0]
print(f"Total P3 items in dictionary: {dict_count}")
print(f"Items with EBA mapping: {dict_mapped}")
if dict_count > 0:
    print(f"Coverage: {dict_mapped/dict_count*100:.1f}%")
else:
    print("Coverage: N/A (Dictionary empty)")

print("\n\n=== P3 ITEM MAPPINGS BY TEMPLATE ===\n")
cur.execute("""
    SELECT template_code, 
           COUNT(*) as items,
           COUNT(CASE WHEN eba_item_id IS NOT NULL THEN 1 END) as mapped
    FROM pillar3_dictionary
    GROUP BY template_code
    ORDER BY items DESC
""")
print(f"{'Template':<10} | {'Items':>6} | {'Mapped':>6}")
print("-" * 30)
for r in cur.fetchall():
    print(f"{r[0]:<10} | {r[1]:>6} | {r[2]:>6}")

# Key metrics comparison with EBA
print("\n\n=== KEY METRICS BY BANK (Latest Period) ===\n")
banks = ['NBG', 'Alpha Bank', 'Eurobank', 'Piraeus', 'Bank of Cyprus']
for bank in banks:
    print(f"\n[{bank}]")
    cur.execute("""
        SELECT template_code || '.' || row_id as p3_id, 
               row_label, 
               period, 
               amount,
               eba_item_id
        FROM facts_pillar3 
        WHERE bank_name = ? AND eba_item_id IS NOT NULL 
              AND row_id IN ('1', '2', '3', '4', '4a', '13')
              AND template_code = 'KM1'
        GROUP BY template_code, row_id
        HAVING period = MAX(period)
        ORDER BY CAST(row_id AS INTEGER)
    """, (bank,))
    rows = cur.fetchall()
    if rows:
        for r in rows:
            amt = r[3] / 1_000_000_000 if abs(r[3]) > 1_000_000 else r[3]
            unit = 'B' if abs(r[3]) > 1_000_000 else ''
            print(f"  {r[0]:10} | {r[1][:25]:25} | {amt:>10,.2f}{unit}")
    else:
        print("  No KM1 data available")

conn.close()
