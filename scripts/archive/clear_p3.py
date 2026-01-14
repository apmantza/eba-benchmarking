import sqlite3
conn = sqlite3.connect('eba_data.db')
conn.execute("DELETE FROM facts_pillar3 WHERE bank_name IN ('Piraeus', 'Bank of Cyprus')")
conn.commit()
print("Cleared Piraeus and Bank of Cyprus from facts_pillar3")
conn.close()
