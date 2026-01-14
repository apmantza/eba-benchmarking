import sqlite3
import pandas as pd

def check_results():
    conn = sqlite3.connect('eba_data.db')
    banks = ['Alpha Bank', 'Eurobank', 'NBG']
    rids = ['1', '5', '7', '11a', '14', '14a', '17', '18', '20']
    
    print(f"{'Bank':<15} | {'RID':<5} | {'Value':<12} | {'Label'}")
    print("-" * 60)
    for bank in banks:
        for rid in rids:
            # Get latest period (2025-06-30)
            df = pd.read_sql_query("SELECT amount, row_label FROM facts_pillar3 WHERE bank_name=? AND row_id=? AND template_code='KM1' AND period='2025-06-30'", conn, params=(bank, rid))
            if df.empty:
                print(f"{bank:<15} | {rid:<5} | {'MISSING':<12} | -")
            else:
                for _, row in df.iterrows():
                    print(f"{bank:<15} | {rid:<5} | {row['amount']:<12.4f} | {row['row_label']}")
    conn.close()

if __name__ == "__main__":
    check_results()
