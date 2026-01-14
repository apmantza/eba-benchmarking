import sqlite3

conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()

print("=" * 60)
print("NBG TEMPLATE STRUCTURE ANALYSIS")
print("=" * 60)

# Get template structure from NBG (best parsed data)
cur.execute("""
    SELECT template_code, COUNT(DISTINCT row_id) as items 
    FROM facts_pillar3 
    WHERE bank_name = 'NBG' 
    GROUP BY template_code 
    ORDER BY items DESC
""")
results = cur.fetchall()

print("\nItems per Template:")
for r in results:
    print(f"  {r[0]}: {r[1]} items")

# Get detailed row IDs per template
print("\n" + "=" * 60)
print("DETAILED TEMPLATE REFERENCE (From NBG)")
print("=" * 60)

templates = ['KM1', 'CC1', 'OV1', 'LR1', 'LR2', 'LIQ1', 'CR1', 'CCR1']
for template in templates:
    cur.execute("""
        SELECT DISTINCT row_id, row_label 
        FROM facts_pillar3 
        WHERE bank_name = 'NBG' AND template_code = ?
        ORDER BY CAST(row_id AS INTEGER)
    """, (template,))
    rows = cur.fetchall()
    if rows:
        print(f"\n{template} ({len(rows)} items):")
        for r in rows[:10]:  # First 10 only
            label = r[1][:50] if r[1] else "No label"
            print(f"  Row {r[0]}: {label}")
        if len(rows) > 10:
            print(f"  ... and {len(rows) - 10} more")

conn.close()
