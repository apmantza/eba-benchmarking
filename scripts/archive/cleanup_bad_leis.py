import sqlite3

DB_PATH = 'eba_data.db'
BAD_LEIS = [
    '549300B37Y9Z6Y5Z9Z9Z',
    '5299008V0A0A0A0A0A0',
    'M9S06G2A6O0A0A0A0A0'
]

def cleanup():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    for lei in BAD_LEIS:
        print(f"Cleaning up LEI: {lei}")
        cur.execute("DELETE FROM facts_pillar3 WHERE lei = ?", (lei,))
        print(f"  Deleted {cur.rowcount} rows.")
        
    conn.commit()
    conn.close()
    print("Cleanup complete.")

if __name__ == "__main__":
    cleanup()
