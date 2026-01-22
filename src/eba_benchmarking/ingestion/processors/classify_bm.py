import pandas as pd
import sqlite3
from eba_benchmarking.config import DB_NAME

def main():
    conn = sqlite3.connect(DB_NAME)

    print("--- Running Business Model Classification ---")

    # 1. Determine the best Period (the one with the most data)
    sql_period = """
    SELECT period, count(*) as cnt
    FROM facts_cre
    WHERE item_id = '2520605'
    GROUP BY period
    ORDER BY cnt DESC
    LIMIT 1
    """
    try:
        best_period = pd.read_sql(sql_period, conn).iloc[0,0]
        print(f"Using Period: {best_period}")

        # 2. SQL Query using CONFIRMED Item ID 2520605
        sql_loans = f"""
        SELECT
            i.lei,
            i.name,

            -- CORPORATE LOANS (Codes 300-399)
            SUM(CASE WHEN f.exposure >= 300 AND f.exposure < 400 THEN f.amount ELSE 0 END) as corp_loans,

            -- RETAIL LOANS (Codes 400-499)
            SUM(CASE WHEN f.exposure >= 400 AND f.exposure < 500 THEN f.amount ELSE 0 END) as retail_loans,

            -- TOTAL (sum of the above two for the ratio calculation)
            SUM(CASE WHEN f.exposure >= 300 AND f.exposure < 500 THEN f.amount ELSE 0 END) as calc_total

        FROM facts_cre f
        JOIN institutions i ON f.lei = i.lei
        WHERE f.item_id = '2520605'  -- Gross Carrying Amount (Loans)
        AND f.period = {best_period}
        GROUP BY i.lei, i.name
        HAVING calc_total > 0
        """

        df_loans = pd.read_sql(sql_loans, conn)

        if not df_loans.empty:
            # Calculate Ratios
            df_loans['retail_share'] = df_loans['retail_loans'] / df_loans['calc_total']
            df_loans['corp_share'] = df_loans['corp_loans'] / df_loans['calc_total']

            # --- CLASSIFICATION LOGIC ---
            def classify(row):
                if row['corp_share'] > 0.60:
                    return 'Corporate Lender'
                if row['retail_share'] > 0.60:
                    return 'Retail Lender'
                return 'Universal Bank'

            df_loans['business_model'] = df_loans.apply(classify, axis=1)

            # --- SAVE DIRECTLY TO INSTITUTIONS ---
            cursor = conn.cursor()

            # Ensure column exists
            try:
                cursor.execute("ALTER TABLE institutions ADD COLUMN business_model TEXT")
            except:
                pass  # Column already exists

            # Update institutions table
            data = df_loans[['business_model', 'lei']].values.tolist()
            cursor.executemany("UPDATE institutions SET business_model = ? WHERE lei = ?", data)

            conn.commit()
            print(f"\n--- Success! {len(df_loans)} Banks Classified ---")
            print(df_loans[['name', 'retail_share', 'corp_share', 'business_model']].head(15))

            print("\n--- Business Model Distribution ---")
            print(df_loans['business_model'].value_counts())

        else:
            print("Query returned no data. Ensure 'facts_cre' is populated.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        conn.close()

if __name__ == '__main__':
    main()
