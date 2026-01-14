"""
Yahoo Finance data integration module.
Fetches stock data for banks with tickers and stores in database.
"""
import pandas as pd
import sqlite3
import yfinance as yf
import os
from datetime import datetime, timedelta
from ..config import DB_NAME

# Conditional streamlit import for caching
try:
    import streamlit as st
    cache_decorator = st.cache_data(ttl=3600)
except:
    # Fallback when running as script (no streamlit)
    def cache_decorator(func):
        return func

@cache_decorator
def get_market_data(lei_list=None):
    """
    Fetches market data for banks with tickers.
    If lei_list is provided, filters to those banks only.
    Returns DataFrame with latest market data.
    """
    if not os.path.exists(DB_NAME):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_NAME)
    
    # Build query
    query = """
        SELECT m.*, i.commercial_name as name, i.country_iso
        FROM market_data m
        JOIN institutions i ON m.lei = i.lei
    """
    if lei_list:
        leis_str = "'" + "','".join([str(l) for l in lei_list]) + "'"
        query += f" WHERE m.lei IN ({leis_str})"
    
    try:
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except:
        conn.close()
        return pd.DataFrame()

def fetch_yahoo_data(ticker):
    """
    Fetches comprehensive data from Yahoo Finance for a single ticker.
    Returns dict with all available metrics.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data for returns calculation
        hist = stock.history(period="1y")
        
        data = {
            # Identification
            'ticker': ticker,
            'fetch_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # Price Data
            'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'previous_close': info.get('previousClose') or info.get('regularMarketPreviousClose'),
            'open_price': info.get('open') or info.get('regularMarketOpen'),
            'day_high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
            'day_low': info.get('dayLow') or info.get('regularMarketDayLow'),
            'week_52_high': info.get('fiftyTwoWeekHigh'),
            'week_52_low': info.get('fiftyTwoWeekLow'),
            'volume': info.get('volume') or info.get('regularMarketVolume'),
            'avg_volume': info.get('averageVolume'),
            'avg_volume_10d': info.get('averageVolume10days'),
            
            # Valuation Metrics
            'market_cap': info.get('marketCap'),
            'enterprise_value': info.get('enterpriseValue'),
            'pe_trailing': info.get('trailingPE'),
            'pe_forward': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
            'enterprise_to_revenue': info.get('enterpriseToRevenue'),
            'enterprise_to_ebitda': info.get('enterpriseToEbitda'),
            
            # Financial Metrics
            'revenue': info.get('totalRevenue'),
            'net_income': info.get('netIncomeToCommon'),
            'ebitda': info.get('ebitda'),
            'eps_trailing': info.get('trailingEps'),
            'eps_forward': info.get('forwardEps'),
            'book_value': info.get('bookValue'),
            'total_cash': info.get('totalCash'),
            'total_debt': info.get('totalDebt'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'return_on_equity': info.get('returnOnEquity'),
            'return_on_assets': info.get('returnOnAssets'),
            'profit_margin': info.get('profitMargins'),
            'operating_margin': info.get('operatingMargins'),
            
            # Dividend Data
            'dividend_rate': info.get('dividendRate'),
            'dividend_yield': info.get('dividendYield'),
            'payout_ratio': info.get('payoutRatio'),
            'ex_dividend_date': info.get('exDividendDate'),
            'last_dividend_value': info.get('lastDividendValue'),
            
            # Analyst Data
            'target_mean': info.get('targetMeanPrice'),
            'target_high': info.get('targetHighPrice'),
            'target_low': info.get('targetLowPrice'),
            'target_median': info.get('targetMedianPrice'),
            'recommendation': info.get('recommendationKey'),
            'recommendation_mean': info.get('recommendationMean'),
            'num_analysts': info.get('numberOfAnalystOpinions'),
            
            # Risk Metrics
            'beta': info.get('beta'),
            
            # Returns (calculated from history)
            'ytd_return': None,
            'return_1y': None,
        }
        
        # Calculate returns from historical data
        if not hist.empty and len(hist) > 1:
            current = hist['Close'].iloc[-1]
            
            # YTD return
            year_start = datetime(datetime.now().year, 1, 1)
            ytd_data = hist[hist.index >= year_start.strftime('%Y-%m-%d')]
            if not ytd_data.empty:
                data['ytd_return'] = (current - ytd_data['Close'].iloc[0]) / ytd_data['Close'].iloc[0]
            # 1Y return
            data['return_1y'] = (current - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
            
            # Robust Dividend Yield Calculation
            # Sometimes Yahoo info returns bad dividend yield (e.g. 450% for NBG).
            # We calculate manually from div history if possible.
            try:
                # Get last 1 year dividends
                # Get last 1 year dividends
                one_year_ago = datetime.now() - timedelta(days=365)
                divs = stock.dividends
                
                if not divs.empty:
                    # Handle timezone-aware index
                    if divs.index.tz is not None:
                        divs = divs.tz_convert(None)
                        
                    recent_divs = divs[divs.index > one_year_ago]
                    ttm_div = recent_divs.sum()
                    
                    if current > 0:
                        calculated_yield = ttm_div / current
                        
                        # Sanity check: If Yahoo's yield is > 50% and calculated is < 20%, use calculated
                        yahoo_yield = data.get('dividend_yield', 0) or 0
                        if (yahoo_yield > 0.50 and calculated_yield < 0.20) or data.get('dividend_yield') is None:
                            data['dividend_yield'] = calculated_yield
                            data['dividend_rate'] = ttm_div
            except Exception as e:
                print(f"Error calculating dividend yield for {ticker}: {e}")
        
        return data
        
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def refresh_market_data():
    """
    Refreshes market data for all banks with tickers.
    Creates or updates the market_data table.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            lei TEXT PRIMARY KEY,
            ticker TEXT,
            fetch_date TEXT,
            
            -- Price Data
            current_price REAL,
            previous_close REAL,
            open_price REAL,
            day_high REAL,
            day_low REAL,
            week_52_high REAL,
            week_52_low REAL,
            volume INTEGER,
            avg_volume INTEGER,
            avg_volume_10d INTEGER,
            
            -- Valuation
            market_cap REAL,
            enterprise_value REAL,
            pe_trailing REAL,
            pe_forward REAL,
            peg_ratio REAL,
            price_to_book REAL,
            price_to_sales REAL,
            enterprise_to_revenue REAL,
            enterprise_to_ebitda REAL,
            
            -- Financials
            revenue REAL,
            net_income REAL,
            ebitda REAL,
            eps_trailing REAL,
            eps_forward REAL,
            book_value REAL,
            total_cash REAL,
            total_debt REAL,
            debt_to_equity REAL,
            current_ratio REAL,
            return_on_equity REAL,
            return_on_assets REAL,
            profit_margin REAL,
            operating_margin REAL,
            
            -- Dividends
            dividend_rate REAL,
            dividend_yield REAL,
            payout_ratio REAL,
            ex_dividend_date TEXT,
            last_dividend_value REAL,
            
            -- Analyst
            target_mean REAL,
            target_high REAL,
            target_low REAL,
            target_median REAL,
            recommendation TEXT,
            recommendation_mean REAL,
            num_analysts INTEGER,
            
            -- Risk
            beta REAL,
            ytd_return REAL,
            return_1y REAL
        )
    """)
    
    # Get banks with tickers
    cur.execute("SELECT lei, ticker, commercial_name FROM institutions WHERE ticker IS NOT NULL")
    banks = cur.fetchall()
    
    print(f"Fetching data for {len(banks)} banks...")
    
    for lei, ticker, name in banks:
        print(f"  {ticker:12} | {name[:30]}...", end=" ")
        
        data = fetch_yahoo_data(ticker)
        
        if data:
            # Prepare insert/update
            columns = ['lei'] + list(data.keys())
            values = [lei] + list(data.values())
            placeholders = ','.join(['?' for _ in values])
            
            cur.execute(f"""
                INSERT OR REPLACE INTO market_data ({','.join(columns)})
                VALUES ({placeholders})
            """, values)
            print("✓")
        else:
            print("✗")
    
    conn.commit()
    conn.close()
    print("\nDone!")

# =============================================================================
# HISTORICAL DATA FUNCTIONS
# =============================================================================

@cache_decorator
def get_market_history(lei_list=None, period="5y"):
    """
    Fetches historical market data for banks with tickers.
    Returns DataFrame with monthly price data for trend analysis.
    """
    if not os.path.exists(DB_NAME):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_NAME)
    
    query = """
        SELECT h.*, i.commercial_name as name, i.country_iso
        FROM market_history h
        JOIN institutions i ON h.lei = i.lei
    """
    if lei_list:
        leis_str = "'" + "','".join([str(l) for l in lei_list]) + "'"
        query += f" WHERE h.lei IN ({leis_str})"
    query += " ORDER BY h.date"
    
    try:
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except:
        conn.close()
        return pd.DataFrame()

def fetch_price_history(ticker, period="5y"):
    """
    Fetches historical price data from Yahoo Finance.
    Returns DataFrame with monthly data.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return pd.DataFrame()
        
        # Resample to monthly (end of month)
        monthly = hist['Close'].resample('ME').last().reset_index()
        monthly.columns = ['date', 'close']
        monthly['date'] = monthly['date'].dt.strftime('%Y-%m-%d')
        
        # Get dividends
        divs = stock.dividends
        if not divs.empty:
            # Sum dividends per month
            div_monthly = divs.resample('ME').sum().reset_index()
            div_monthly.columns = ['date', 'dividend']
            div_monthly['date'] = div_monthly['date'].dt.strftime('%Y-%m-%d')
            monthly = monthly.merge(div_monthly, on='date', how='left')
            monthly['dividend'] = monthly['dividend'].fillna(0)
        else:
            monthly['dividend'] = 0
        
        # Calculate trailing 12-month dividend
        monthly['dividend_ttm'] = monthly['dividend'].rolling(12, min_periods=1).sum()
        
        # Calculate dividend yield
        monthly['dividend_yield'] = monthly['dividend_ttm'] / monthly['close']
        
        # Get shares outstanding for market cap calculation
        info = stock.info
        shares = info.get('sharesOutstanding', 0)
        monthly['market_cap'] = monthly['close'] * shares if shares else None
        
        monthly['ticker'] = ticker
        
        return monthly
        
    except Exception as e:
        print(f"Error fetching history for {ticker}: {e}")
        return pd.DataFrame()

def refresh_market_history():
    """
    Refreshes historical market data for all banks with tickers.
    Creates or updates the market_history table.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS market_history (
            lei TEXT,
            ticker TEXT,
            date TEXT,
            close REAL,
            dividend REAL,
            dividend_ttm REAL,
            dividend_yield REAL,
            market_cap REAL,
            PRIMARY KEY (lei, date)
        )
    """)
    
    # Get banks with tickers
    cur.execute("SELECT lei, ticker, commercial_name FROM institutions WHERE ticker IS NOT NULL")
    banks = cur.fetchall()
    
    print(f"Fetching historical data for {len(banks)} banks...")
    
    for lei, ticker, name in banks:
        print(f"  {ticker:12} | {name[:30]}...", end=" ")
        
        df_hist = fetch_price_history(ticker, period="5y")
        
        if not df_hist.empty:
            df_hist['lei'] = lei
            
            # Clear existing data for this LEI
            cur.execute("DELETE FROM market_history WHERE lei = ?", (lei,))
            
            # Insert new data
            for _, row in df_hist.iterrows():
                cur.execute("""
                    INSERT OR REPLACE INTO market_history 
                    (lei, ticker, date, close, dividend, dividend_ttm, dividend_yield, market_cap)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (lei, ticker, row['date'], row['close'], row['dividend'], 
                      row['dividend_ttm'], row['dividend_yield'], row.get('market_cap')))
            
            print(f"✓ ({len(df_hist)} months)")
        else:
            print("✗")
    
    conn.commit()
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--history':
        refresh_market_history()
    else:
        refresh_market_data()

