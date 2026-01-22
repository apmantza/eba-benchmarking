import pandas as pd
import os

def main():
    print("--- Refining Bank Metadata CSV ---")
    
    # 1. Load current DB banks (The 132 banks)
    current_banks_path = 'current_db_banks.csv'
    if not os.path.exists(current_banks_path):
        print(f"Error: {current_banks_path} not found.")
        return
    
    df_current = pd.read_csv(current_banks_path)
    print(f"Loaded {len(df_current)} banks from database.")

    # 2. Load original metadata (The 79 banks provided by user)
    # We'll use the version I haven't overwritten or hopefully the one I can still read
    original_csv_path = 'europe_bank_tickers.csv' # Assuming this is currently the 79-row version
    if not os.path.exists(original_csv_path):
         print(f"Error: {original_csv_path} not found.")
         return
    
    df_old = pd.read_csv(original_csv_path)
    print(f"Loaded {len(df_old)} metadata records.")

    # 3. Preparation
    # Ensure current list has the target columns
    metadata_cols = ['yfinance ticker', 'bond ticker', 'trading', 'bank type', 'Majority owner']
    for col in metadata_cols:
        df_current[col] = ""

    # 4. Matching Logic
    matches_found = 0
    for idx, row in df_current.iterrows():
        db_name = str(row['name']).lower().strip()
        db_comm_name = str(row['commercial_name']).lower().strip() if pd.notna(row['commercial_name']) else ""
        
        # Try to find a match in old metadata
        match = None
        
        # Exact match on name
        exact_match = df_old[df_old['NAME'].str.lower().str.strip() == db_name]
        if not exact_match.empty:
            match = exact_match.iloc[0]
        else:
            # Fuzzy match: is old name in db name or vice versa?
            for _, old_row in df_old.iterrows():
                old_name = str(old_row['NAME']).lower().strip()
                if old_name in db_name or db_name in old_name or (db_comm_name and old_name in db_comm_name):
                    match = old_row
                    break
        
        if match is not None:
            for col in metadata_cols:
                val = match.get(col)
                df_current.at[idx, col] = val if pd.notna(val) else ""
            matches_found += 1

    print(f"Matched {matches_found} banks with metadata.")

    # 5. Save Final CSV
    # Reorder columns to match user's preferred format but include LEI
    final_cols = ['lei', 'name', 'commercial_name'] + metadata_cols
    df_current = df_current[final_cols]
    
    # Rename 'name' to 'NAME' to stay close to original header if desired, or keep as is
    # Let's keep these descriptive headers
    
    output_path = 'europe_bank_tickers.csv'
    df_current.to_csv(output_path, index=False)
    print(f"Final CSV saved to {output_path} with {len(df_current)} rows.")

if __name__ == "__main__":
    main()
