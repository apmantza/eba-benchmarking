import sqlite3
from eba_benchmarking.config import DB_NAME

def main():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("--- Checking Database Schema ---")
    try:
        # Try to select the column to see if it exists
        cursor.execute("SELECT region FROM market_data LIMIT 1")
        print("✅ Column 'region' already exists.")
    except sqlite3.OperationalError:
        print("⚠️ Column 'region' missing. Adding it now...")
        try:
            # Alter table is the safest way to add a column without deleting data
            cursor.execute("ALTER TABLE market_data ADD COLUMN region TEXT")
            print("✅ Success: Added 'region' column.")
        except Exception as e:
            print(f"❌ Error adding column: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()