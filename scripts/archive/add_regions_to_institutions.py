import sqlite3
import os

DB_NAME = 'eba_data.db'

# Region Mapping
REGION_MAP = {
    # CEE
    'BG': 'CEE', 'CZ': 'CEE', 'EE': 'CEE', 'HR': 'CEE', 'HU': 'CEE', 
    'LT': 'CEE', 'LV': 'CEE', 'PL': 'CEE', 'RO': 'CEE', 'SI': 'CEE', 'SK': 'CEE',
    
    # Northern Europe
    'DK': 'Northern Europe', 'FI': 'Northern Europe', 'IS': 'Northern Europe',
    'NO': 'Northern Europe', 'SE': 'Northern Europe', 
    
    # Southern Europe
    'CY': 'Southern Europe', 'ES': 'Southern Europe', 'GR': 'Southern Europe', 
    'IT': 'Southern Europe', 'MT': 'Southern Europe', 'PT': 'Southern Europe',
    
    # Western Europe
    'AT': 'Western Europe', 'BE': 'Western Europe', 'DE': 'Western Europe', 
    'FR': 'Western Europe', 'IE': 'Western Europe', 'LI': 'Western Europe', 
    'LU': 'Western Europe', 'NL': 'Western Europe',
    'GB': 'Western Europe', 'UK': 'Western Europe'
}

def update_db():
    if not os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Add Column
    try:
        cursor.execute("ALTER TABLE institutions ADD COLUMN region TEXT")
        print("Column 'region' added to 'institutions'.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("Column 'region' already exists.")
        else:
            print(f"Error checking/adding column: {e}")
            
    # 2. Update Rows
    # We execute update for each country found in map
    for iso, region in REGION_MAP.items():
        cursor.execute("UPDATE institutions SET region = ? WHERE country_iso = ?", (region, iso))
            
    conn.commit()
    
    # Verify
    cursor.execute("SELECT country_iso, region, COUNT(*) FROM institutions GROUP BY country_iso")
    results = cursor.fetchall()
    
    print("\nRegion assignment status:")
    for iso, reg, cnt in results:
        print(f"{iso}: {reg} ({cnt} banks)")
        
    conn.close()

if __name__ == "__main__":
    update_db()
