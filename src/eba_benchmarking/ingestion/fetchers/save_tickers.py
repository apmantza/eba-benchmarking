import pandas as pd
import sqlite3
import os
from eba_benchmarking.config import DB_NAME, ROOT_DIR

def main():
    conn = sqlite3.connect(DB_NAME)

    # Load your verified CSV
    csv_path = os.path.join(ROOT_DIR, 'suggested_tickers.csv')
    try:
        df_verified = pd.read_csv(csv_path)
        
        # Update Database
        data = df_verified[['suggested_ticker', 'lei']].values.tolist()
        conn.executemany("UPDATE institutions SET ticker = ? WHERE lei = ?", data)
        conn.commit()
        
        print(f"Success! Updated {len(data)} tickers in the database.")
        
    except FileNotFoundError:
        print(f"Could not find '{csv_path}'. Did you run Part 2?")

    conn.close()

if __name__ == "__main__":
    main()