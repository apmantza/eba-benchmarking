import sqlite3
from eba_benchmarking.config import DB_NAME

def main():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Identify rows with many X's or LEIs that are not 20 characters of alpha-numeric
    cursor.execute("SELECT lei FROM bank_models")
    rows = cursor.fetchall()
    
    to_delete = []
    for (lei,) in rows:
        if 'XXXX' in lei or 'xxxx' in lei:
            to_delete.append(lei)
            
    if to_delete:
        print(f"Deleting dummy rows from bank_models: {to_delete}")
        cursor.executemany("DELETE FROM bank_models WHERE lei = ?", [(l,) for l in to_delete])
        conn.commit()
    else:
        print("No dummy rows found in bank_models.")
        
    conn.close()

if __name__ == "__main__":
    main()
