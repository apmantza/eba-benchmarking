"""
Alpha Vantage data integration module.
Fetches stock data for banks with tickers and stores in database.
"""
import pandas as pd
import sqlite3
import requests
import os
import time
from datetime import datetime, timedelta
from ..config import DB_NAME

# The user's API key
AV_API_KEY = 'BPT2C0JHFSAJM7ZB'
BASE_URL = 'https://www.alphavantage.co/query'

# Mapping of secondary tickers if the primary Athens ticker isn't supported by AV
# Alpha Vantage has better coverage for OTC/US-listed symbols for some foreign stocks.
AV_TICKER_MAP = {
    '213800DBQIB6VBNU5C64': 'ALBKF', # Alpha Bank
    '549300H09Y076Y9RWE09': 'NBGCY', # National Bank of Greece
    '5493006N8A8R39A1C362': 'EGFEY', # Eurobank
    '549300V6Y4E67727X120': 'PIRBF', # Piraeus Bank
}

def fetch_av_quote(symbol):
    """Fetches global quote from Alpha Vantage."""
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol,
        'apikey': AV_API_KEY
    }
    try:
        r = requests.get(BASE_URL, params=params)
        data = r.json()
        if 'Global Quote' in data and data['Global Quote']:
            q = data['Global Quote']
            return {
                'price': float(q.get('05. price', 0)),
                'volume': int(q.get('06. volume', 0)),
                'prev_close': float(q.get('08. previous close', 0)),
                'date': q.get('07. latest trading day')
            }
        elif 'Information' in data:
            print(f"Rate limit hit or info: {data['Information']}")
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {e}")
    return None

def fetch_price_history_av(symbol, period="5y"):
    """
    Fetches historical price data from Alpha Vantage.
    Returns DataFrame with monthly data.
    """
    params = {
        'function': 'TIME_SERIES_MONTHLY_ADJUSTED',
        'symbol': symbol,
        'apikey': AV_API_KEY
    }
    try:
        r = requests.get(BASE_URL, params=params)
        data = r.json()
        
        # Key for monthly series: 'Monthly Adjusted Time Series'
        series_key = 'Monthly Adjusted Time Series'
        if series_key not in data:
            if 'Error Message' in data:
                print(f"AV Error: {data['Error Message']}")
            elif 'Information' in data:
                print(f"AV Info: {data['Information']}")
            return pd.DataFrame()
            
        series = data[series_key]
        df = pd.DataFrame.from_dict(series, orient='index')
        
        # Alpha Vantage returns columns with numbers, e.g., '5. adjusted close'
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # We want the adjusted close and dividend
        df_clean = pd.DataFrame({
            'date': df.index.strftime('%Y-%m-%d'),
            'close': df['5. adjusted close'].astype(float),
            'dividend': df['7. dividend amount'].astype(float)
        })
        
        # Calculate trailing 12-month dividend
        df_clean['dividend_ttm'] = df_clean['dividend'].rolling(12, min_periods=1).sum()
        
        # Calculate dividend yield
        df_clean['dividend_yield'] = df_clean.apply(
            lambda x: x['dividend_ttm'] / x['close'] if x['close'] > 0 else 0, axis=1
        )
        
        return df_clean
        
    except Exception as e:
        print(f"Error fetching history for {symbol} from AV: {e}")
        return pd.DataFrame()

def refresh_market_data_av():
    """Refreshes latest market data using Alpha Vantage."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT lei, ticker, commercial_name FROM institutions
        WHERE ticker IS NOT NULL AND trading_status = 'Public'
    """)
    banks = cur.fetchall()
    
    print(f"Fetching Alpha Vantage data for {len(banks)} banks...")
    
    for lei, ticker, name in banks:
        av_symbol = AV_TICKER_MAP.get(lei, ticker)
        print(f"  {av_symbol:12} | {name[:30]}...", end=" ")
        
        quote = fetch_av_quote(av_symbol)
        
        if quote:
            data = {
                'current_price': quote['price'],
                'previous_close': quote['prev_close'],
                'volume': quote['volume'],
                'fetch_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Prepare update
            cols = list(data.keys())
            vals = list(data.values())
            
            cur.execute(f"""
                UPDATE market_data 
                SET {', '.join([f"{c} = ?" for c in cols])}
                WHERE lei = ?
            """, vals + [lei])
            print("OK")
        else:
            print("FAILED")
            
        # Respect rate limits (5 per min)
        time.sleep(12)
            
    conn.commit()
    conn.close()

def refresh_market_history_av():
    """Refreshes historical data using Alpha Vantage."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT lei, ticker, commercial_name FROM institutions
        WHERE ticker IS NOT NULL AND trading_status = 'Public'
    """)
    banks = cur.fetchall()
    
    print(f"Fetching Alpha Vantage history for {len(banks)} banks...")
    
    for lei, ticker, name in banks:
        av_symbol = AV_TICKER_MAP.get(lei, ticker)
        print(f"  {av_symbol:12} | {name[:30]}...", end=" ")
        
        df_hist = fetch_price_history_av(av_symbol)
        
        if not df_hist.empty:
            cur.execute("DELETE FROM market_history WHERE lei = ?", (lei,))
            
            for _, row in df_hist.iterrows():
                cur.execute("""
                    INSERT OR REPLACE INTO market_history 
                    (lei, ticker, date, close, dividend, dividend_ttm, dividend_yield)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (lei, row.get('ticker', ticker), row['date'], row['close'], row['dividend'], 
                      row['dividend_ttm'], row['dividend_yield']))
            
            print(f"OK ({len(df_hist)} months)")
        else:
            print("FAILED")
            
        time.sleep(15) # Slightly longer delay for history calls
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--history':
        refresh_market_history_av()
    else:
        refresh_market_data_av()
