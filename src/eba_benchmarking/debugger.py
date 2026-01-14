import pandas as pd
import sqlite3
from eba_benchmarking.config import DB_NAME

def main():
    conn = sqlite3.connect(DB_NAME)

    print("--- DIAGNOSTIC REPORT ---")

    # 1. Check if the table is empty
    try:
        row_count = pd.read_sql("SELECT Count(*) FROM facts_cre", conn).iloc[0,0]
        print(f"Total Rows in facts_cre: {row_count}")

        if row_count > 0:
            # 2. Find the correct Item IDs (What data do we actually have?)
            print("\nTop 5 Items by Total Amount (What are the big numbers?):")
            sql_items = """
            SELECT f.item_id, d.label, SUM(f.amount) as total_value
            FROM facts_cre f
            LEFT JOIN dictionary d ON f.item_id = d.item_id
            GROUP BY f.item_id, d.label
            ORDER BY total_value DESC
            LIMIT 5
            """
            print(pd.read_sql(sql_items, conn))

            # 3. Find the correct Exposure Codes (Are they 300, 400, or something else?)
            print("\nTop 5 Exposures by Total Amount:")
            sql_exp = """
            SELECT exposure, SUM(amount) as total_value
            FROM facts_cre
            WHERE amount > 0
            GROUP BY exposure
            ORDER BY total_value DESC
            LIMIT 5
            """
            print(pd.read_sql(sql_exp, conn))

            # 4. Check Period
            print("\nAvailable Periods:")
            print(pd.read_sql("SELECT DISTINCT period FROM facts_cre", conn))

        else:
            print("CRITICAL: The table 'facts_cre' is empty. The parser failed to insert data.")
    except Exception as e:
        print(f"Error checking database: {e}")

    conn.close()

if __name__ == "__main__":
    main()