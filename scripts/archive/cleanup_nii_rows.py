import sqlite3

def delete_spurious_nii():
    db_path = 'eba_data.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check count first
    cur.execute("SELECT COUNT(*) FROM facts_pillar3 WHERE template_code='IRRBB1' AND dimension_name='NII' AND row_id IN ('3','4','5','6')")
    count_before = cur.fetchone()[0]
    print(f"Found {count_before} spurious NII rows to delete.")
    
    # Delete
    cur.execute("DELETE FROM facts_pillar3 WHERE template_code='IRRBB1' AND dimension_name='NII' AND row_id IN ('3','4','5','6')")
    conn.commit()
    print(f"Deleted {cur.rowcount} rows.")
    conn.close()

if __name__ == "__main__":
    delete_spurious_nii()
