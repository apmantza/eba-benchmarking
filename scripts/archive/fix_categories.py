import sqlite3

DB_PATH = 'eba_data.db'

def fix_categories():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Rule 1: All LIQ templates should be Liquidity
    print("Fixing LIQ templates...")
    cur.execute("UPDATE pillar3_dictionary SET category = 'Liquidity' WHERE template_code IN ('LIQ1', 'LIQ2')")
    print(f"  Updated matches for LIQ* -> Liquidity")
    
    # Rule 2: Ensure Market Risk is only MR templates (optional specific request check)
    # The user said "NSFR is not market risk", which we just fixed by forcing LIQ2 -> Liquidity.
    
    conn.commit()
    conn.close()
    print("Categories updated.")

if __name__ == "__main__":
    fix_categories()
