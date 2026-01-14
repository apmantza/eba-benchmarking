import sqlite3

DB_PATH = 'eba_data.db'

# Correct Mappings
LEI_MAP = {
    'NBG': '5UMCZOEYKCVFAW8ZLO05',
    'Alpha Bank': 'NLPK02SGC0U1AABDLL56',
    'Eurobank': 'JEUVK5RWVJEN8W0C9M24',
    'Piraeus': '213800OYHR4PPVA77574',
    'Bank of Cyprus': '635400L14KNHJ3DMBX37'
}

# Old/Bad LEIs to remove or remap
BAD_LEIS = [
    '5299008V0A0A0A0A0A0', # Alpha
    '549300B37Y9Z6Y5Z9Z9Z', # NBG
    'M9S06G2A6O0A0A0A0A0', # Piraeus
    '213800OYHR1MPQ5VJL60', # Piraeus Excel
    '635400L14KNHZXPUZM19', # Cyprus Excel
]

def cleanup():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("Initial Row Count:", cur.execute("SELECT COUNT(*) FROM facts_pillar3").fetchone()[0])
    
    # 1. Update bank names for consistency
    print("Updating bank names...")
    cur.execute("UPDATE facts_pillar3 SET bank_name = 'Alpha Bank' WHERE bank_name LIKE 'Alpha%'")
    cur.execute("UPDATE facts_pillar3 SET bank_name = 'Piraeus' WHERE bank_name LIKE 'Piraeus%'")
    cur.execute("UPDATE facts_pillar3 SET bank_name = 'NBG' WHERE bank_name LIKE 'National Bank%'")
    
    # 2. Remap LEIs based on bank_name if possible
    print("Remapping LEIs...")
    for name, lei in LEI_MAP.items():
        cur.execute("UPDATE facts_pillar3 SET lei = ? WHERE bank_name = ?", (lei, name))
        print(f"  Assigned {lei} to bank {name}")

    # 3. Delete any remaining bad LEIs
    print("Deleting orphan bad LEIs...")
    for lei in BAD_LEIS:
        cur.execute("DELETE FROM facts_pillar3 WHERE lei = ?", (lei,))
        print(f"  Deleted {cur.rowcount} rows for bad LEI {lei}")
        
    # 4. Remove duplicates (Skipped - handled by PK)
    # print("Removing duplicates...")
    # cur.execute("""
    #     DELETE FROM facts_pillar3 
    #     WHERE id NOT IN (
    #         SELECT MAX(id) 
    #         FROM facts_pillar3 
    #         GROUP BY bank_name, lei, period, template_code, row_id
    #     )
    # """)
    # print(f"  Deleted {cur.rowcount} duplicate rows.")

    print("Final Row Count:", cur.execute("SELECT COUNT(*) FROM facts_pillar3").fetchone()[0])
    
    conn.commit()
    
    print("Vacuuming database (this might take a while)...")
    cur.execute("VACUUM")
    
    conn.close()
    print("Cleanup complete.")

if __name__ == "__main__":
    cleanup()
