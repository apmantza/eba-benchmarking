"""
Script to populate ticker column in institutions table using manual mappings.
"""
import sqlite3
import sys
sys.path.insert(0, 'data')
from ticker_mappings import TICKER_MAPPINGS

# 1. Connect to database
conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()

# 2. Ensure ticker column exists
cur.execute("PRAGMA table_info(institutions)")
columns = [row[1] for row in cur.fetchall()]
if 'ticker' not in columns:
    print("Adding ticker column...")
    cur.execute("ALTER TABLE institutions ADD COLUMN ticker TEXT")

# 3. Get all institutions
cur.execute("SELECT lei, commercial_name FROM institutions")
institutions = cur.fetchall()

# 4. Match and update
matched = 0
for lei, name in institutions:
    if not name:
        continue
    name_lower = name.lower()
    
    for pattern, ticker in TICKER_MAPPINGS.items():
        if pattern.lower() in name_lower:
            cur.execute("UPDATE institutions SET ticker = ? WHERE lei = ?", (ticker, lei))
            print(f"  Matched: {name[:40]:40} -> {ticker}")
            matched += 1
            break

conn.commit()

# 5. Verify
print(f"\n=== Summary ===")
print(f"Total institutions: {len(institutions)}")
print(f"Matched with tickers: {matched}")

print("\nInstitutions with tickers:")
cur.execute("SELECT commercial_name, ticker FROM institutions WHERE ticker IS NOT NULL ORDER BY ticker")
for name, ticker in cur.fetchall():
    print(f"  {ticker:12} | {name}")

conn.close()
print("\nDone!")
