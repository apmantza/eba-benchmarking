import pandas as pd
import sqlite3
from eba_benchmarking.config import DB_NAME

def main():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("--- 2. Classifying Banks by Size (Total Assets) ---")

    # Ensure institutions table has the size columns
    print("  - Ensuring institutions table has size columns...")
    for col, col_type in [('total_assets', 'REAL'), ('size_category', 'TEXT'), ('business_model', 'TEXT')]:
        try:
            cursor.execute(f"ALTER TABLE institutions ADD COLUMN {col} {col_type}")
            print(f"    Added column: {col}")
        except:
            pass  # Column already exists
    conn.commit()

    # Query for the LATEST Total Assets per bank
    # Item ID 2521010 = Total Assets
    sql = """
    WITH LatestAssets AS (
        SELECT
            lei,
            amount as total_assets,
            period,
            ROW_NUMBER() OVER (PARTITION BY lei ORDER BY period DESC) as rn
        FROM facts_oth
        WHERE item_id = '2521010'
    )
    SELECT lei, total_assets
    FROM LatestAssets
    WHERE rn = 1
    """

    try:
        df_assets = pd.read_sql(sql, conn)

        if df_assets.empty:
            print("⚠️ No asset data found in facts_oth (Item 2521010).")
            return

        # Classification Logic
        def classify_size(assets):
            # amount is in EUR millions in EBA files.
            # 50bn = 50,000 Million
            # 200bn = 200,000 Million
            # 500bn = 500,000 Million

            val = float(assets)

            if val < 50000:
                return 'Small (<50bn)'
            elif val < 200000:
                return 'Medium (50-200bn)'
            elif val < 500000:
                return 'Large (200-500bn)'
            else:
                return 'Huge (>500bn)'

        df_assets['size_category'] = df_assets['total_assets'].apply(classify_size)

        # Update institutions table directly
        print("  - Updating institutions table with size data...")
        data = df_assets[['total_assets', 'size_category', 'lei']].values.tolist()
        cursor.executemany("""
            UPDATE institutions
            SET total_assets = ?, size_category = ?
            WHERE lei = ?
        """, data)

        conn.commit()
        print(f"  > Successfully classified {len(df_assets)} banks by size in institutions.")

        print("\n--- Size Distribution ---")
        print(df_assets['size_category'].value_counts())

    except Exception as e:
        print(f"❌ Error classifying size: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
