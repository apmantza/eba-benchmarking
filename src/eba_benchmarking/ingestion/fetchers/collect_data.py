import pandas as pd
import yfinance as yf
import sqlite3
import datetime
import os
from eba_benchmarking.config import ROOT_DIR, DB_NAME

# 1. SETUP DATABASE
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Updated Schema: Added 'lei' column
cursor.execute('''
    CREATE TABLE IF NOT EXISTS market_data (
        lei TEXT,
        bank_name TEXT,
        ticker TEXT,
        collection_date TEXT,
        market_cap REAL,
        stock_price REAL,
        currency TEXT,
        date TEXT,
        category TEXT,
        metric TEXT,
        value REAL,
        region TEXT,
        PRIMARY KEY (lei, collection_date)
    )
''')
conn.commit()

def get_market_data():
    print("--- Starting Data Collection ---")
    
    # Load mapping file
    banks_csv_path = os.path.join(ROOT_DIR, 'banks.csv')
    try:
        # distinct=True helps if you accidentally have duplicates in your CSV
        banks_df = pd.read_csv(banks_csv_path)
    except FileNotFoundError:
        print(f"Error: '{banks_csv_path}' not found.")
        return

    for index, row in banks_df.iterrows():
        bank_name = row['name']
        lei_code = row['lei']  # CAPTURE LEI
        ticker_symbol = row['ticker']
        
        print(f"Fetching: {bank_name} ({ticker_symbol}) -> LEI: {lei_code}")
        
        try:
            stock = yf.Ticker(ticker_symbol)
            price = stock.fast_info['last_price']
            mkt_cap = stock.fast_info['market_cap']
            
            data_entry = (
                lei_code,      # STORE LEI
                bank_name,
                ticker_symbol,
                str(datetime.date.today()),
                mkt_cap,
                price,
                row['currency']
            )
            
            cursor.execute('''
                INSERT INTO market_data (lei, bank_name, ticker, collection_date, market_cap, stock_price, currency)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', data_entry)
            
        except Exception as e:
            print(f"   -> Error: {e}")

    conn.commit()
    conn.close()
    print("--- Collection Complete ---")

if __name__ == "__main__":
    get_market_data()