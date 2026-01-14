import sqlite3

def check_bank(bank_name):
    conn = sqlite3.connect('eba_data.db')
    cur = conn.cursor()
    query = """
    SELECT row_id, amount, row_label 
    FROM facts_pillar3 
    WHERE template_code = 'KM1' 
    AND period = '2025-06-30'
    AND bank_name = ?
    AND row_id IN ('1', '5', '7', '11a', '14', '14a', '17', '18', '20')
    ORDER BY row_id
    """
    cur.execute(query, (bank_name,))
    rows = cur.fetchall()
    print(f"--- {bank_name} ---")
    for rid, val, lbl in rows:
        print(f"{rid:<4} | {val:<10.4f} | {lbl[:40]}")
    conn.close()

if __name__ == "__main__":
    for b in ['Alpha Bank', 'Eurobank', 'NBG']:
        check_bank(b)
        print()
