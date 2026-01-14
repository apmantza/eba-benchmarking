import sqlite3

DB_PATH = 'eba_data.db'

def patch_eurobank_irrbb1():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Values from User Screenshot (2025-06-30)
    # Eurobank IRRBB1 EVE Current Period
    # Unit: Millions
    corrections_eve = [
        ('1', 'Parallel up', -200.0),
        ('2', 'Parallel down', 90.0),
        ('3', 'Steepener', 132.0),
        ('4', 'Flattener', -345.0),
        ('5', 'Short rates up', -394.0),
        ('6', 'Short rates down', 164.0)
    ]
    
    corrections_nii = [
        ('EU-1', 'Parallel up', 77.0),
        ('EU-2', 'Parallel down', -266.0)
    ]
    
    lei = 'JEUVK5RWVJEN8W0C9M24' # Eurobank
    period = '2025-06-30'
    template = 'IRRBB1'
    source = 'Manual Patch (Screenshot)'
    
    print("Applying manual patch for Eurobank IRRBB1...")
    
    count = 0
    # Process EVE
    for row_id, label, val_mio in corrections_eve:
        val_absolute = val_mio * 1_000_000
        try:
            cur.execute("""
                INSERT OR REPLACE INTO facts_pillar3 
                (lei, period, template_code, table_title, row_id, row_label, raw_label, 
                 amount, is_new_metric, source_page, bank_name, dimension_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lei, period, template, 'EU IRRBB1', row_id, label, 'Manual Patch',
                val_absolute, 0, 45, 'Eurobank', 'EVE'
            ))
            count += 1
        except Exception as e:
            print(f"Error updating EVE row {row_id}: {e}")
            
    # Process NII
    for row_id, label, val_mio in corrections_nii:
        val_absolute = val_mio * 1_000_000
        try:
            cur.execute("""
                INSERT OR REPLACE INTO facts_pillar3 
                (lei, period, template_code, table_title, row_id, row_label, raw_label, 
                 amount, is_new_metric, source_page, bank_name, dimension_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lei, period, template, 'EU IRRBB1', row_id, label, 'Manual Patch',
                val_absolute, 0, 45, 'Eurobank', 'NII'
            ))
            count += 1
        except Exception as e:
            print(f"Error updating NII row {row_id}: {e}")
            
    # Process KM1 - removed manual patch, using automated blueprint_pipeline instead
    conn.commit()
    print(f"Patched {count} rows successfully.")
    conn.close()

if __name__ == "__main__":
    patch_eurobank_irrbb1()
