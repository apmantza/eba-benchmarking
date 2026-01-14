import sqlite3
import pandas as pd

def check_missing_summary():
    conn = sqlite3.connect('eba_data.db')
    rids = ['11a', '14', '14a', '16', '16a', '17', '18']
    banks = ['Alpha Bank', 'Eurobank', 'NBG']
    
    print(f"{'Bank':<15} | {'RID':<5} | {'Value':<12} | {'Label':<40}")
    print("-" * 80)
    
    for bank in banks:
        for rid in rids:
            query = """
            SELECT amount, row_label FROM facts_pillar3 
            WHERE bank_name = ? AND template_code = 'KM1' AND row_id = ?
            """
            cur = conn.cursor()
            cur.execute(query, (bank, rid))
            rows = cur.fetchall()
            if not rows:
                print(f"{bank:<15} | {rid:<5} | {'MISSING':<12}")
            for amount, label in rows:
                print(f"{bank:<15} | {rid:<5} | {amount:<12.4f} | {label}")
    
    conn.close()

if __name__ == "__main__":
    check_missing_summary()
