import sqlite3

def check():
    conn = sqlite3.connect('eba_data.db')
    cur = conn.cursor()
    query = """
    SELECT bank_name, row_id, amount, row_label 
    FROM facts_pillar3 
    WHERE template_code = 'KM1' 
    AND period = '2025-06-30'
    AND row_id IN ('1', '5', '7', '11a', '14', '14a', '17', '18', '20')
    ORDER BY bank_name, row_id
    """
    cur.execute(query)
    rows = cur.fetchall()
    print(f"{'Bank':<12} | {'RID':<4} | {'Value':<10} | {'Label'}")
    print("-" * 60)
    for b, rid, val, lbl in rows:
        print(f"{b:<12} | {rid:<4} | {val:<10.4f} | {lbl[:40]}")
    conn.close()

if __name__ == "__main__":
    check()
