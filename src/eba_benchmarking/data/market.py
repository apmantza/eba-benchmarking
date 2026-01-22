"""
Yahoo Finance data integration module.
Fetches stock data for banks with tickers and stores in database.
"""
import pandas as pd
import sqlite3
import yfinance as yf
import os
from datetime import datetime, timedelta
from datetime import datetime, timedelta
import numpy as np
from ..config import DB_NAME

# Conditional streamlit import for caching
try:
    import streamlit as st
    cache_decorator = st.cache_data(ttl=3600)
except:
    # Fallback when running as script (no streamlit)
    def cache_decorator(func):
        return func

# Currency conversion utilities
CURRENCY_FX_PAIRS = {
    'EUR': None,  # No conversion needed
    'GBp': 'GBPEUR=X',  # British Pence (will divide by 100 first)
    'SEK': 'EURSEK=X',  # Swedish Krona
    'NOK': 'EURNOK=X',  # Norwegian Krone
    'DKK': 'EURDKK=X',  # Danish Krone
    'PLN': 'EURPLN=X',  # Polish Zloty
    'HUF': 'EURHUF=X',  # Hungarian Forint
    'CZK': 'EURCZK=X',  # Czech Koruna
    'RON': 'EURRON=X',  # Romanian Leu
    'ISK': 'EURISK=X',  # Icelandic Króna
    'CHF': 'EURCHF=X',  # Swiss Franc
    'USD': 'EURUSD=X',  # US Dollar
    'GBP': 'GBPEUR=X',  # British Pound
}

def get_fx_rate(currency):
    """
    Get current FX rate to convert from currency to EUR.
    Returns 1.0 for EUR, None if currency not supported.
    """
    if currency == 'EUR':
        return 1.0
    
    fx_pair = CURRENCY_FX_PAIRS.get(currency)
    if not fx_pair:
        print(f"Warning: Currency {currency} not supported for conversion")
        return None
    
    try:
        fx = yf.Ticker(fx_pair)
        info = fx.info
        rate = info.get('regularMarketPrice') or info.get('previousClose')
        
        if rate:
            # For EUR/XXX pairs (e.g., EURSEK=X), rate is EUR→XXX, so we need 1/rate for XXX→EUR
            # For GBP/EUR pairs, rate is GBP→EUR, so we use it directly
            if 'GBP' in fx_pair and fx_pair.startswith('GBP'):
                return rate  # GBP→EUR rate
            else:
                return 1.0 / rate  # Invert EUR→XXX to get XXX→EUR
        return None
    except Exception as e:
        print(f"Error fetching FX rate for {currency}: {e}")
        return None

def get_fx_history(currency, period='5y'):
    """
    Get historical FX rates for currency conversion.
    Returns DataFrame with dates and FX rates (to convert from currency to EUR).
    """
    if currency == 'EUR':
        return None  # No conversion needed
    
    fx_pair = CURRENCY_FX_PAIRS.get(currency)
    if not fx_pair:
        return None
    
    try:
        fx = yf.Ticker(fx_pair)
        history = fx.history(period=period)
        
        if history.empty:
            return None
        
        # Use Close price for FX rate
        fx_rates = history[['Close']].copy()
        
        # Invert rates if needed (same logic as get_fx_rate)
        if 'GBP' in fx_pair and fx_pair.startswith('GBP'):
            fx_rates['fx_to_eur'] = fx_rates['Close']  # GBP→EUR
        else:
            fx_rates['fx_to_eur'] = 1.0 / fx_rates['Close']  # Invert EUR→XXX
        
        return fx_rates[['fx_to_eur']]
    except Exception as e:
        print(f"Error fetching FX history for {currency}: {e}")
        return None

def convert_to_eur(value, currency, fx_rate=None, is_total_value=False):
    """
    Convert a value from source currency to EUR.
    For GBp (pence):
      - Per-share values (prices, EPS, DPS): divide by 100 first
      - Total values (market cap, enterprise value): already in correct magnitude, don't divide
    
    Args:
        value: The value to convert
        currency: Source currency code
        fx_rate: Optional pre-fetched FX rate
        is_total_value: True for market cap/enterprise value, False for per-share prices
    """
    if value is None or pd.isna(value):
        return None
    
    if currency == 'EUR':
        return value
    
    # Special handling for pence
    if currency == 'GBp':
        if not is_total_value:
            # Per-share values: convert pence to pounds
            value = value / 100.0
        # For total values (market cap), Yahoo already reports in pence magnitude
        # e.g., 17B pence, which we treat as 17B in base currency units
        # So we don't divide by 100 for total values
        currency = 'GBP'  # Now treat as GBP for FX conversion
    
    # Get FX rate if not provided
    if fx_rate is None:
        fx_rate = get_fx_rate(currency)
    
    if fx_rate is None:
        return None
    
    return value * fx_rate

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
        SELECT m.*, COALESCE(i.short_name, i.commercial_name) as name, i.country_iso, i.region, i.size_category
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
    except Exception as e:
        print(f"ERROR in get_market_data: {e}")
        conn.close()
        return pd.DataFrame()

@cache_decorator
def get_market_benchmarking_stats(base_country, base_region, base_size):
    """
    Calculates market data averages for 6 key peer groups:
    - Domestic Peers (incl. BoC if Base is GR)
    - Regional (Same Size)
    - Regional (All but Small)
    - Core (Same Size)
    - Core (All but Small)
    - CEE (All)
    """
    df_all = get_market_data()
    if df_all.empty:
        return pd.DataFrame()
        
    ATHEX_PEER_LEIS = ['635400L14KNHZXPUZM19'] # Bank of Cyprus
    CORE_REGIONS = ['Western Europe', 'Northern Europe']
    SMALL_SIZE = 'Small (<50bn)'
    
    groups = {
        "Domestic Avg": df_all[(df_all['country_iso'] == base_country) | (df_all['lei'].isin(ATHEX_PEER_LEIS) if base_country == 'GR' else False)],
        "Regional (Same Size)": df_all[(df_all['region'] == base_region) & (df_all['size_category'] == base_size)],
        "Regional (All but Small)": df_all[(df_all['region'] == base_region) & (df_all['size_category'] != SMALL_SIZE)],
        "Core (Same Size)": df_all[(df_all['region'].isin(CORE_REGIONS)) & (df_all['size_category'] == base_size)],
        "Core (All but Small)": df_all[(df_all['region'].isin(CORE_REGIONS)) & (df_all['size_category'] != SMALL_SIZE)],
        "CEE (All)": df_all[df_all['region'] == 'CEE']
    }
    
    stats = []
    numeric_cols = ['current_price', 'market_cap', 'pe_trailing', 'price_to_book', 'dividend_yield', 
                    'buyback_yield', 'payout_yield', 'beta', 'return_1y', 'return_3y', 'return_5y',
                    'eps_trailing', 'dps_trailing', 'payout_ratio']
    
    for label, group_df in groups.items():
        if not group_df.empty:
            avg_row = group_df[numeric_cols].mean().to_dict()
            avg_row['name'] = label
            stats.append(avg_row)
            
    return pd.DataFrame(stats)

@cache_decorator
def get_market_fy_averages(base_country, base_region, base_size):
    """
    Calculates FY strategic averages for peer groups.
    """
    df_fy_all = get_market_financial_years()
    if df_fy_all.empty:
        return pd.DataFrame()
        
    # Standardize LEI mapping
    conn = sqlite3.connect(DB_NAME)
    df_meta = pd.read_sql("SELECT lei, country_iso, region, size_category FROM institutions", conn)
    conn.close()
    
    df_fy_all = pd.merge(df_fy_all, df_meta, on='lei', how='left')
    
    ATHEX_PEER_LEIS = ['635400L14KNHZXPUZM19']
    CORE_REGIONS = ['Western Europe', 'Northern Europe']
    SMALL_SIZE = 'Small (<50bn)'
    
    group_filters = {
        "Domestic Avg": (df_fy_all['country_iso'] == base_country) | (df_fy_all['lei'].isin(ATHEX_PEER_LEIS) if base_country == 'GR' else False),
        "Regional (Same Size)": (df_fy_all['region'] == base_region) & (df_fy_all['size_category'] == base_size),
        "Regional (All but Small)": (df_fy_all['region'] == base_region) & (df_fy_all['size_category'] != SMALL_SIZE),
        "Core (Same Size)": (df_fy_all['region'].isin(CORE_REGIONS)) & (df_fy_all['size_category'] == base_size),
        "Core (All but Small)": (df_fy_all['region'].isin(CORE_REGIONS)) & (df_fy_all['size_category'] != SMALL_SIZE),
        "CEE (All)": (df_fy_all['region'] == 'CEE')
    }
    
    fy_stats = []
    fy_numeric_cols = ['dividend_yield_fy', 'buyback_yield_fy', 'total_yield_fy', 
                       'payout_ratio_fy', 'dividend_payout_ratio_fy', 'earnings_yield_fy',
                       'eps_fy', 'dps_fy']
    
    for label, mask in group_filters.items():
        group_df = df_fy_all[mask]
        if not group_df.empty:
            # Group by fy to get annual averages for each peer group
            group_avgs = group_df.groupby('fy')[fy_numeric_cols].mean().reset_index()
            group_avgs['name'] = label
            fy_stats.append(group_avgs)
            
    if not fy_stats:
        return pd.DataFrame()
        
    return pd.concat(fy_stats, ignore_index=True)

def fetch_yahoo_data(ticker, lei=None):
    """
    Fetches comprehensive data from Yahoo Finance for a single ticker.
    Optional 'lei' allows for manual data overrides where Yahoo coverage is spotty.
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch 5 years of history to allow for 1y, 3y, 5y return calculations
        hist = stock.history(period="5y") 
        info = stock.info
        
        # Manual Metadata Overrides (where Yahoo is missing shares/book value)
        # 5493001BABFV7P27OW30 = Nova Ljubljanska Banka (Ljubljana listing missing core metadata)
        if lei == '5493001BABFV7P27OW30':
            if not info.get('sharesOutstanding'): info['sharesOutstanding'] = 20_000_000
            if not info.get('bookValue'): info['bookValue'] = 111.0
            if not info.get('trailingPE'): 
                # Estimated PE using 2024 expected net income (~€500M) vs 20M shares
                # Net income ~25 per share. Price 36 -> PE ~1.4
                # But let yfinance try to use its own first.
                pass

        shares = info.get('sharesOutstanding') or 0
        
        # Currency detection and conversion
        currency = info.get('currency', 'EUR')  # Listing currency (for prices)
        financial_currency = info.get('financialCurrency', currency)  # Financial reporting currency
        
        fx_rate = get_fx_rate(currency) if currency != 'EUR' else 1.0
        fx_rate_financial = get_fx_rate(financial_currency) if financial_currency != 'EUR' else 1.0
        
        # Helper functions for conversion
        def to_eur_price(value):
            """Convert price-based values (use listing currency)"""
            return convert_to_eur(value, currency, fx_rate, is_total_value=False)
        
        def to_eur_total(value):
            """Convert total values like market cap (use listing currency, no ÷100 for GBp)"""
            return convert_to_eur(value, currency, fx_rate, is_total_value=True)
        
        def to_eur_financial(value):
            """Convert financial metrics (use financial currency)"""
            return convert_to_eur(value, financial_currency, fx_rate_financial, is_total_value=False)
        
        data = {
            # Identification
            'ticker': ticker,
            'fetch_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'currency': currency,  # Store listing currency
            'fx_rate_to_eur': fx_rate,  # Store FX rate used
            
            # Price Data (converted using listing currency)
            'current_price': to_eur_price(info.get('currentPrice') or info.get('regularMarketPrice')),
            'previous_close': to_eur_price(info.get('previousClose') or info.get('regularMarketPreviousClose')),
            'open_price': to_eur_price(info.get('open') or info.get('regularMarketOpen')),
            'day_high': to_eur_price(info.get('dayHigh') or info.get('regularMarketDayHigh')),
            'day_low': to_eur_price(info.get('dayLow') or info.get('regularMarketDayLow')),
            'week_52_high': to_eur_price(info.get('fiftyTwoWeekHigh')),
            'week_52_low': to_eur_price(info.get('fiftyTwoWeekLow')),
            'volume': info.get('volume') or info.get('regularMarketVolume'),
            'avg_volume': info.get('averageVolume'),
            'avg_volume_10d': info.get('averageVolume10days'),
            
            # Valuation Metrics (market cap uses listing currency, is total value)
            'market_cap': to_eur_total(info.get('marketCap')),
            'enterprise_value': to_eur_total(info.get('enterpriseValue')),
            'pe_trailing': info.get('trailingPE'),  # Ratio - no conversion
            'pe_forward': info.get('forwardPE'),  # Ratio - no conversion
            'peg_ratio': info.get('pegRatio'),  # Ratio - no conversion
            'price_to_book': None,  # Will recalculate after book value conversion
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
            'enterprise_to_revenue': info.get('enterpriseToRevenue'),
            'enterprise_to_ebitda': info.get('enterpriseToEbitda'),
            
            # Financial Metrics (use financial currency)
            'revenue': info.get('totalRevenue'),
            'net_income': info.get('netIncomeToCommon'),
            'ebitda': info.get('ebitda'),
            'eps_trailing': to_eur_financial(info.get('trailingEps')),
            'eps_forward': to_eur_financial(info.get('forwardEps')),
            'book_value': to_eur_financial(info.get('bookValue')),
            'total_cash': info.get('totalCash'),
            'total_debt': info.get('totalDebt'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'return_on_equity': info.get('returnOnEquity'),
            'return_on_assets': info.get('returnOnAssets'),
            'profit_margin': info.get('profitMargins'),
            'operating_margin': info.get('operatingMargins'),
            
            # Dividend Data (use financial currency)
            'dividend_yield': info.get('dividendYield'),  # Ratio - no conversion
            'dividend_rate': to_eur_financial(info.get('dividendRate')),
            'dps_trailing': to_eur_financial(info.get('trailingAnnualDividendRate')),
            'payout_ratio': info.get('payoutRatio'),  # Ratio - no conversion
            'ex_dividend_date': info.get('exDividendDate'),
            'last_dividend_value': to_eur_financial(info.get('lastDividendValue')),
            
            # Analyst Data (targets use price currency)
            'target_mean': to_eur_price(info.get('targetMeanPrice')),
            'target_high': to_eur_price(info.get('targetHighPrice')),
            'target_low': to_eur_price(info.get('targetLowPrice')),
            'target_median': to_eur_price(info.get('targetMedianPrice')),
            'recommendation': info.get('recommendationKey'),
            'recommendation_mean': info.get('recommendationMean'),
            'num_analysts': info.get('numberOfAnalystOpinions'),
            
            # Risk Metrics
            'beta': info.get('beta'),

            # Returns (calculated from history)
            'ytd_return': None,
            'return_1y': None,
            'return_3y': None, # Added 3Y return
            'return_5y': None, # Added 5Y return

            # Buyback Data (will be populated from cash flow)
            'buyback_ttm': None,
            'buyback_yield': None,
            'payout_yield': None,
            'total_payout': None,
        }
        
        # Recalculate P/B ratio using EUR-converted values
        if data['current_price'] and data['book_value'] and data['book_value'] > 0:
            data['price_to_book'] = data['current_price'] / data['book_value']

        # Fallback Market Cap calculation if Yahoo is missing the aggregate value
        if (not data.get('market_cap') or data['market_cap'] == 0) and data['current_price'] and shares > 0:
            data['market_cap'] = data['current_price'] * shares

        # Calculate 12-month average price and market cap for yield denominators
        # Calculate 12-month average price (filter last year from 5y history)
        # Ensure index is datetime and localized/unlocalized consistently
        if not hist.empty:
            last_date = hist.index[-1]
            start_1y = last_date - timedelta(days=365)
            hist_1y = hist[hist.index > start_1y]
            avg_price_1y = hist_1y['Close'].mean() if not hist_1y.empty else hist['Close'].iloc[-1]
        else:
            avg_price_1y = None
        avg_market_cap_1y = (avg_price_1y * shares) if (avg_price_1y and shares) else data.get('market_cap')
        data['avg_market_cap_1y'] = avg_market_cap_1y

        # Fetch buyback data from cash flow statement (TTM Logic)
        try:
            buyback_ttm = 0
            found_quarterly = False
            
            # 1. Try Quarterly TTM Sum (Last 4 Quarters)
            qcf = stock.quarterly_cashflow
            if qcf is not None and not qcf.empty:
                # Priority: Net Common Stock Issuance (Negative values)
                if 'Net Common Stock Issuance' in qcf.index:
                    # Get last 4 quarters
                    vals = qcf.loc['Net Common Stock Issuance'].head(4)
                    # Sum only negative values (buybacks)
                    buyback_ttm = vals[vals < 0].abs().sum()
                    if buyback_ttm > 0:
                        found_quarterly = True
                
                # Fallback: Gross Repurchase
                if not found_quarterly:
                    for key in ['Repurchase Of Capital Stock', 'Common Stock Payments']:
                        if key in qcf.index:
                            vals = qcf.loc[key].head(4)
                            buyback_ttm = vals[vals < 0].abs().sum()
                            if buyback_ttm > 0:
                                found_quarterly = True
                            break
            
            # 2. Fallback to Annual (Most Recent Year) if Quarterly missing/zero
            if not found_quarterly:
                cf = stock.cashflow
                if cf is not None and not cf.empty:
                    if 'Net Common Stock Issuance' in cf.index:
                        val = cf.loc['Net Common Stock Issuance'].iloc[0]
                        if val < 0:
                            buyback_ttm = abs(val)
                    else:
                        for key in ['Repurchase Of Capital Stock', 'Common Stock Payments']:
                            if key in cf.index:
                                val = cf.loc[key].iloc[0]
                                if val < 0:
                                    buyback_ttm = abs(val)
                                break
                                
            # Manual TTM Overrides
            MANUAL_TTM_OVERRIDES = {
                'TPEIR.AT': 0, # Exclude Q2 2025 noise (HFSF/extraordinary flows)
            }
            if ticker in MANUAL_TTM_OVERRIDES:
                buyback_ttm = MANUAL_TTM_OVERRIDES[ticker]

            data['buyback_ttm'] = buyback_ttm

        except Exception as e:
            data['buyback_ttm'] = 0
            # print(f"Error fetching buyback TTM for {ticker}: {e}")

        # Calculate buyback yield and payout yield using 12-month average market cap
        if avg_market_cap_1y and avg_market_cap_1y > 0:
            buyback = data.get('buyback_ttm') or 0
            data['buyback_yield'] = buyback / avg_market_cap_1y if buyback else 0

            # Total annual dividend = dividend rate * shares
            div_rate = data.get('dividend_rate') or 0
            annual_div = div_rate * shares if div_rate and shares else 0

            # Total payout = dividends + buybacks
            data['total_payout'] = annual_div + buyback

            # Payout yield = total payout / avg market cap
            data['payout_yield'] = data['total_payout'] / avg_market_cap_1y if data['total_payout'] else 0
        else:
            data['buyback_yield'] = 0
            data['payout_yield'] = 0

        # Calculate returns from historical data
        if not hist.empty and len(hist) > 1:
            current = hist['Close'].iloc[-1]
            
            # Helper to find closest price N days ago
            def get_price_ago(days_ago):
                try:
                    target_date = hist.index[-1] - timedelta(days=days_ago)
                    # Filter for history closest to target date (after or on)
                    subset = hist[hist.index >= target_date]
                    if not subset.empty:
                        return subset['Close'].iloc[0]
                except:
                    pass
                return None

            # YTD return
            # Ensure proper timezone handling for YTD
            try:
                current_yr = datetime.now().year
                ytd_subset = hist[hist.index.year == current_yr]
                if not ytd_subset.empty:
                    start_price = ytd_subset['Close'].iloc[0]
                    data['ytd_return'] = (current - start_price) / start_price
            except:
                pass

            # 1Y return
            price_1y = get_price_ago(365)
            if price_1y:
                data['return_1y'] = (current - price_1y) / price_1y
            
            # 3Y return
            price_3y = get_price_ago(3 * 365)
            if price_3y:
                data['return_3y'] = (current - price_3y) / price_3y

            # 5Y return
            price_5y = get_price_ago(5 * 365)
            if price_5y:
                data['return_5y'] = (current - price_5y) / price_5y
            
            # Robust Dividend Yield Calculation
            try:
                # Get last 1 year dividends
                one_year_ago = datetime.now() - timedelta(days=365)
                divs = stock.dividends
                
                if not divs.empty:
                    # Handle timezone-aware index
                    if divs.index.tz is not None:
                        divs = divs.tz_convert(None)
                        
                    recent_divs = divs[divs.index > one_year_ago]
                    ttm_div = recent_divs.sum()
                    
                    # Use 12-month average price for yield calculation
                    denominator = avg_price_1y if avg_price_1y and avg_price_1y > 0 else current
                    if denominator > 0:
                        calculated_yield = ttm_div / denominator
                        
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
            currency TEXT,
            fx_rate_to_eur REAL,
            
            -- Price Data (all in EUR)
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
            dps_trailing REAL, -- Added DPS
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
            return_1y REAL,
            return_3y REAL, -- Added 3Y return
            return_5y REAL, -- Added 5Y return

            -- Buyback/Payout
            buyback_ttm REAL,
            avg_market_cap_1y REAL,
            buyback_yield REAL,
            payout_yield REAL,
            total_payout REAL
        )
    """)
    
    # Get publicly traded banks with tickers only
    cur.execute("""
        SELECT lei, ticker, commercial_name FROM institutions
        WHERE ticker IS NOT NULL AND trading_status = 'Public'
    """)
    banks = cur.fetchall()

    print(f"Fetching data for {len(banks)} public banks...")
    
    for lei, ticker, name in banks:
        safe_name = name[:30].encode('ascii', 'replace').decode('ascii')
        print(f"  {ticker:12} | {safe_name}...", end=" ")
        
        data = fetch_yahoo_data(ticker, lei=lei)
        
        if data:
            # Prepare insert/update
            columns = ['lei'] + list(data.keys())
            values = [lei] + list(data.values())
            placeholders = ','.join(['?' for _ in values])
            
            cur.execute(f"""
                INSERT OR REPLACE INTO market_data ({','.join(columns)})
                VALUES ({placeholders})
            """, values)
            print("OK")
        else:
            print("FAIL")
    
    conn.commit()
    conn.close()
    print("\nDone!")

# Ticker overrides for historical data (to handle corporate restructuring gaps)
HISTORY_TICKER_MAP = {
    # '213800DBQIB6VBNU5C64': 'ACBC.SG', # REVERTED: Price in SG (0.84) does not match Athens (1.54/3.81)
}

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
        SELECT h.*, COALESCE(i.short_name, i.commercial_name) as name, i.country_iso
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

@cache_decorator
def get_market_financial_years(lei_list=None):
    """
    Fetches strategic market data aligned by Financial Year.
    """
    if not os.path.exists(DB_NAME):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT f.*, COALESCE(i.short_name, i.commercial_name) as name
        FROM market_financial_years f
        JOIN institutions i ON f.lei = i.lei
    """
    if lei_list:
        leis_str = "'" + "','".join([str(l) for l in lei_list]) + "'"
        query += f" WHERE f.lei IN ({leis_str})"
    query += " ORDER BY f.fy DESC"
    
    try:
        df = pd.read_sql(query, conn)
        # Calculate Strategic Metrics
        
        # 1. Payout Ratio: (Total Payout Amount) / Net Income
        # Now that dividend_amt is absolute (DPS * Shares) and buyback_amt is absolute, we can sum them directly.
        total_payout = df['dividend_amt'] + df['buyback_amt']
        df['payout_ratio_fy'] = total_payout / df['net_income']
        df['dividend_payout_ratio_fy'] = df['dividend_amt'] / df['net_income']
        
        df.loc[df['net_income'] <= 0, 'payout_ratio_fy'] = np.nan # Avoid negative earnings distortion
        df.loc[df['net_income'] <= 0, 'dividend_payout_ratio_fy'] = np.nan
        
        # 2. Earnings Yield: Net Income / Market Cap
        df['earnings_yield_fy'] = df['net_income'] / df['avg_market_cap']
        
        conn.close()
        return df
    except Exception as e:
        print(f"Error in get_market_financial_years: {e}")
        conn.close()
        return pd.DataFrame()

def attribute_date_to_fy(date_obj):
    """
    Attributions for European Banking:
    H2 (Aug-Dec) payments usually relate to the current profit year (interim).
    H1 (Jan-Jul) payments usually relate to the previous profit year (final).
    """
    month = date_obj.month
    year = date_obj.year
    if month >= 8:
        return year
    else:
        return year - 1

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
        
        # Currency detection and FX conversion for historical data
        info = stock.info
        currency = info.get('currency', 'EUR')
        financial_currency = info.get('financialCurrency', currency)
        
        # Fetch historical FX rates if needed
        fx_history_price = None
        fx_history_financial = None
        
        if currency != 'EUR':
            print(f"  Fetching FX history for {currency}...")
            fx_history_price = get_fx_history(currency, period=period)
            if fx_history_price is None:
                print(f"  Warning: Could not fetch FX history for {currency}, using current rate")
                current_fx = get_fx_rate(currency) or 1.0
                # Create a constant FX rate series
                fx_history_price = pd.DataFrame(
                    {'fx_to_eur': current_fx}, 
                    index=hist.index
                )
        
        if financial_currency != 'EUR' and financial_currency != currency:
            fx_history_financial = get_fx_history(financial_currency, period=period)
            if fx_history_financial is None:
                current_fx = get_fx_rate(financial_currency) or 1.0
                fx_history_financial = pd.DataFrame(
                    {'fx_to_eur': current_fx},
                    index=hist.index
                )
        
        # Convert historical prices to EUR
        if fx_history_price is not None:
            # Align FX rates with stock prices by date
            hist_with_fx = hist.merge(
                fx_history_price,
                left_index=True,
                right_index=True,
                how='left'
            )
            # Forward fill any missing FX rates
            hist_with_fx['fx_to_eur'] = hist_with_fx['fx_to_eur'].ffill().bfill()
            
            # Convert prices
            for col in ['Open', 'High', 'Low', 'Close']:
                if col in hist_with_fx.columns:
                    # Special handling for GBp (pence)
                    if currency == 'GBp':
                        hist_with_fx[col] = (hist_with_fx[col] / 100.0) * hist_with_fx['fx_to_eur']
                    else:
                        hist_with_fx[col] = hist_with_fx[col] * hist_with_fx['fx_to_eur']
            
            hist = hist_with_fx
        
        # Resample to monthly (end of month)
        monthly = hist['Close'].resample('ME').last().reset_index()
        monthly.columns = ['date', 'close']
        # Convert date to datetime for processing
        monthly['date_dt'] = pd.to_datetime(monthly['date'])
        
        # Get dividends and convert to EUR
        divs = stock.dividends
        if not divs.empty:
            # Historical dividends from yfinance are expressed in the listing currency (currency)
            # which matches the historical price history data.
            if currency != 'EUR' and fx_history_price is not None:
                divs_with_fx = divs.to_frame('dividend').merge(
                    fx_history_price,
                    left_index=True,
                    right_index=True,
                    how='left'
                )
                divs_with_fx['fx_to_eur'] = divs_with_fx['fx_to_eur'].ffill().bfill()
                
                # Convert dividends using listing currency rules
                if currency == 'GBp':
                    divs_with_fx['dividend_eur'] = (divs_with_fx['dividend'] / 100.0) * divs_with_fx['fx_to_eur']
                else:
                    divs_with_fx['dividend_eur'] = divs_with_fx['dividend'] * divs_with_fx['fx_to_eur']
                
                divs = divs_with_fx['dividend_eur']
            
            # Sum dividends per month
            div_monthly = divs.resample('ME').sum().reset_index()
            div_monthly.columns = ['date', 'dividend']
            monthly = monthly.merge(div_monthly, on='date', how='left')
            monthly['dividend'] = monthly['dividend'].fillna(0)
        else:
            monthly['dividend'] = 0
        
        # Calculate trailing 12-month dividend and average price
        monthly['dividend_ttm'] = monthly['dividend'].rolling(12, min_periods=1).sum()
        monthly['close_avg_12m'] = monthly['close'].rolling(12, min_periods=1).mean()
        
        # Calculate dividend yield using 12-month average price
        monthly['dividend_yield'] = monthly['dividend_ttm'] / monthly['close_avg_12m']
        
        # Get shares outstanding for market cap calculation
        shares = info.get('sharesOutstanding', 0)
        
        # Calculate 12-month rolling average market cap
        monthly['market_cap'] = monthly['close'] * shares if shares else None
        if monthly['market_cap'] is not None:
             monthly['market_cap_avg_12m'] = monthly['market_cap'].rolling(12, min_periods=1).mean()
        else:
             monthly['market_cap_avg_12m'] = None

        # Buyback and Payout Columns
        monthly['buyback_annual'] = 0.0
        monthly['buyback_yield'] = 0.0
        monthly['payout_yield'] = 0.0
        
        # Get buybacks from cash flow
        try:
            cf = stock.cashflow
            if cf is not None and not cf.empty:
                buyback_keys = ['Repurchase Of Capital Stock', 'Common Stock Payments']
                buyback_series = None
                for key in buyback_keys:
                    if key in cf.index:
                        buyback_series = cf.loc[key].dropna()
                        break
                
                if buyback_series is not None:
                    # buyback_series is indexed by date (annual)
                    # Convert to positive
                    buyback_series = abs(buyback_series)
                    
                    buyback_df = buyback_series.to_frame(name='buyback_val')
                    # Convert index to datetime and remove timezone for merge_asof
                    buyback_df.index = pd.to_datetime(buyback_df.index).tz_localize(None)
                    buyback_df = buyback_df.sort_index()
                    
                    # Ensure monthly date_dt is also timezone-naive
                    monthly['date_dt'] = monthly['date_dt'].dt.tz_localize(None)
                    monthly = monthly.sort_values('date_dt')
                    
                    # Map each month to the preceding annual buyback value
                    monthly = pd.merge_asof(
                        monthly, 
                        buyback_df, 
                        left_on='date_dt',
                        right_index=True,
                        direction='backward'
                    )
                    
                    # Fill NaN buybacks
                    monthly['buyback_annual'] = monthly['buyback_val'].fillna(0)
                    
                    # Calculate yields using rolling average market cap
                    if 'market_cap_avg_12m' in monthly.columns:
                        monthly['buyback_yield'] = monthly.apply(
                            lambda x: x['buyback_annual'] / x['market_cap_avg_12m'] if x['market_cap_avg_12m'] and x['market_cap_avg_12m'] > 0 else 0, 
                            axis=1
                        )
                        # Payout yield = buyback yield + dividend yield
                        monthly['payout_yield'] = monthly['buyback_yield'] + monthly['dividend_yield']
                    
                    monthly = monthly.drop(columns=['buyback_val'])
        except Exception as e:
            print(f"Error fetching buyback history for {ticker}: {e}")

        # ---------------------------------------------------------------------
        # FINANCIAL YEAR (FY) ATTRIBUTION ENGINE
        # ---------------------------------------------------------------------
        fy_data = []
        
        # 1. Calculate Average Prices/Cap per Calendar Year
        # We use simple calendar years for denominators
        monthly['cal_year'] = pd.to_datetime(monthly['date']).dt.year
        yr_avg = monthly.groupby('cal_year').agg({
            'close': 'mean',
            'market_cap': 'mean'
        }).rename(columns={'close': 'avg_price_yr', 'market_cap': 'avg_mcap_yr'})
        
        # 2. Attribute Dividends to FY
        # Use the ALREADY CONVERTED 'divs' series (which is now in EUR per share)
        if not divs.empty:
            div_df = divs.to_frame(name='amount').reset_index()
            
            # Rename 'Date' column if needed (yfinance sometimes changes case)
            date_col = 'Date' if 'Date' in div_df.columns else 'index'
            div_df['date_dt'] = pd.to_datetime(div_df[date_col]).dt.tz_localize(None)
            div_df['fy'] = div_df['date_dt'].apply(attribute_date_to_fy)
            fy_divs = div_df.groupby('fy')['amount'].sum().to_frame('fy_dividend')
            # Extract DPS (approx)
            fy_divs['dps_fy'] = fy_divs['fy_dividend'] # Amount is already EUR per share
        else:
            fy_divs = pd.DataFrame(columns=['fy_dividend', 'dps_fy'])
            
        # 3. Attribute Buybacks and Net Income to FY
        fy_buybacks_dict = {}
        fy_net_income_dict = {}
        locked_buyback_years = set()
        
        # Net Income from Income Statement
        try:
            inc = stock.income_stmt
            if inc is not None and not inc.empty:
                ni_key = 'Net Income' if 'Net Income' in inc.index else None
                if ni_key:
                    ni_series = inc.loc[ni_key].dropna()
                    for date, val in ni_series.items():
                        # Convert to EUR if financial_currency != EUR
                        if financial_currency != 'EUR':
                            # Try to find historical FX rate
                            fx_val = None
                            if fx_history_financial is not None:
                                try:
                                    # Find closest date in FX history
                                    date_dt = pd.to_datetime(date)
                                    rate_idx = fx_history_financial.index.get_indexer([date_dt], method='nearest')
                                    fx_val = fx_history_financial.iloc[rate_idx[0]]['fx_to_eur']
                                except:
                                    pass
                            
                            # Fallback to current rate
                            if fx_val is None:
                                fx_val = get_fx_rate(financial_currency) or 1.0
                            
                            val = val * fx_val
                            
                        fy_net_income_dict[date.year] = val
        except:
            pass
            
        def process_buybacks(cf_df, allow_locking=False):
            if cf_df is None or cf_df.empty:
                return

            def _to_eur_fin(val, date):
                if financial_currency == 'EUR':
                    return val
                fx_val = None
                if fx_history_financial is not None:
                    try:
                        date_dt = pd.to_datetime(date)
                        rate_idx = fx_history_financial.index.get_indexer([date_dt], method='nearest')
                        fx_val = fx_history_financial.iloc[rate_idx[0]]['fx_to_eur']
                    except:
                        pass
                if fx_val is None:
                    fx_val = get_fx_rate(financial_currency) or 1.0
                return val * fx_val

            # Priority 1: Net Common Stock Issuance
            if 'Net Common Stock Issuance' in cf_df.index:
                vals = cf_df.loc['Net Common Stock Issuance'].dropna()
                for date, val in vals.items():
                    target_fy = date.year - 1
                    # If this year is already locked by a previous high-priority source, skip
                    if target_fy in locked_buyback_years and not allow_locking:
                         continue
                         
                    if val < 0: # Net Buyback
                        buyback_amt = _to_eur_fin(abs(val), date)
                        # Set value
                        if allow_locking: # Annual
                             fy_buybacks_dict[target_fy] = buyback_amt
                             locked_buyback_years.add(target_fy)
                        else: # Quarterly
                             # Only add if not locked
                             if target_fy not in locked_buyback_years:
                                  fy_buybacks_dict[target_fy] = fy_buybacks_dict.get(target_fy, 0) + buyback_amt
                return # Done with this DF if Net used

            # Priority 2: Synthetic Net (Issuance + Repurchase)
            if 'Issuance Of Capital Stock' in cf_df.index:
                rep_key = next((k for k in ['Repurchase Of Capital Stock', 'Common Stock Payments'] if k in cf_df.index), None)
                if rep_key:
                    iss_vals = cf_df.loc['Issuance Of Capital Stock']
                    rep_vals = cf_df.loc[rep_key]
                    df_net = pd.DataFrame({'Issue': iss_vals, 'Repurchase': rep_vals}).fillna(0)
                    df_net['Net'] = df_net['Issue'] + df_net['Repurchase']
                    
                    for date, row in df_net.iterrows():
                        val = row['Net']
                        target_fy = date.year - 1
                        if target_fy in locked_buyback_years and not allow_locking:
                             continue
                        
                        if val < 0: # Net Buyback
                            buyback_amt = _to_eur_fin(abs(val), date)
                            if allow_locking:
                                fy_buybacks_dict[target_fy] = buyback_amt
                                locked_buyback_years.add(target_fy)
                            else:
                                if target_fy not in locked_buyback_years:
                                    fy_buybacks_dict[target_fy] = fy_buybacks_dict.get(target_fy, 0) + buyback_amt
                    return

            # Priority 3: Gross Repurchase
            bb_keys = ['Repurchase Of Capital Stock', 'Common Stock Payments']
            for key in bb_keys:
                if key in cf_df.index:
                    vals = cf_df.loc[key].dropna()
                    for date, val in vals.items():
                        target_fy = date.year - 1
                        if target_fy in locked_buyback_years and not allow_locking:
                             continue
                             
                        if val < 0:
                            buyback_amt = _to_eur_fin(abs(val), date)
                            if allow_locking: # Annual fallback
                                fy_buybacks_dict[target_fy] = buyback_amt
                                locked_buyback_years.add(target_fy)
                            else: # Quarterly
                                if target_fy not in locked_buyback_years:
                                    fy_buybacks_dict[target_fy] = fy_buybacks_dict.get(target_fy, 0) + buyback_amt
                    break

        # Process Annual FIRST to establish baseline and lock years
        try:
            process_buybacks(stock.cashflow, allow_locking=True)
        except:
            pass
            
        # Process Quarterly SECOND to fill in gaps (e.g. current year, or years where Annual misses info)
        try:
            process_buybacks(stock.quarterly_cashflow, allow_locking=False)
        except:
            pass
        
        fy_buybacks = pd.DataFrame.from_dict(fy_buybacks_dict, orient='index', columns=['fy_buyback'])
        fy_buybacks.index.name = 'fy'

        # 4. Merge for Strategic FY Table
        # Range of years
        all_fys = sorted(list(set(yr_avg.index) | set(fy_divs.index) | set(fy_buybacks.index) | set(fy_net_income_dict.keys())))
        for fy in all_fys:
            if fy < datetime.now().year - 6 or fy > datetime.now().year:
                continue
                
            mcap = yr_avg.loc[fy, 'avg_mcap_yr'] if fy in yr_avg.index else None
            price = yr_avg.loc[fy, 'avg_price_yr'] if fy in yr_avg.index else None
            
            div_amt_sum = fy_divs.loc[fy, 'fy_dividend'] if fy in fy_divs.index else 0
            dps = fy_divs.loc[fy, 'dps_fy'] if (fy in fy_divs.index and 'dps_fy' in fy_divs.columns) else 0
            bb_amt = fy_buybacks.loc[fy, 'fy_buyback'] if fy in fy_buybacks.index else 0
            # Define manual corrections for known data anomalies
            MANUAL_FY_CORRECTIONS = {
                ('TPEIR.AT', 2024): {'buyback_amt': 0},         # User confirmed SBB started late 2025; H1 outflows excluded
                ('BMPS.MI', 2024): {'dividend_amt': 1083000000} # Corrects for Shares Outstanding mismatch (1.26B real vs 3B Yahoo)
            }

            net_inc = fy_net_income_dict.get(fy, 0)
            
            # Calculate absolute dividend amount
            if shares and shares > 0:
                abs_div_amt = div_amt_sum * shares
            else:
                abs_div_amt = 0
            
            # Apply Manual Overrides
            if (ticker, fy) in MANUAL_FY_CORRECTIONS:
                corrections = MANUAL_FY_CORRECTIONS[(ticker, fy)]
                if 'buyback_amt' in corrections:
                    bb_amt = corrections['buyback_amt']
                if 'dividend_amt' in corrections:
                    abs_div_amt = corrections['dividend_amt']
                if 'net_income' in corrections:
                    net_inc = corrections['net_income']

            # EPS FY = Net Income / Shares
            eps = net_inc / shares if (net_inc and shares and shares > 0) else 0
            
            fy_data.append({
                'fy': int(fy),
                'avg_price': price,
                'avg_market_cap': mcap,
                'net_income': net_inc,
                'dividend_amt': abs_div_amt,
                'buyback_amt': bb_amt,
                'eps_fy': eps,
                'dps_fy': dps,
                'dividend_yield_fy': dps / price if (dps and price and price > 0) else 0,
                'buyback_yield_fy': bb_amt / mcap if (bb_amt and mcap and mcap > 0) else 0,
                'total_yield_fy': (dps/price if (dps and price and price > 0) else 0) + (bb_amt/mcap if (bb_amt and mcap and mcap > 0) else 0)
            })
            
        # Drop helper column and format date
        monthly['date'] = monthly['date_dt'].dt.strftime('%Y-%m-%d')
        monthly = monthly.drop(columns=['date_dt', 'cal_year'])
        monthly['ticker'] = ticker
        
        return {
            'monthly': monthly,
            'financial_years': pd.DataFrame(fy_data)
        }
        
    except Exception as e:
        print(f"Error fetching history for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return None


def refresh_market_history():
    """
    Refreshes historical market data for all banks with tickers.
    Creates or updates the market_history table.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS market_financial_years (
            lei TEXT,
            ticker TEXT,
            fy INTEGER,
            avg_price REAL,
            avg_market_cap REAL,
            net_income REAL,
            dividend_amt REAL,
            buyback_amt REAL,
            eps_fy REAL,
            dps_fy REAL,
            dividend_yield_fy REAL,
            buyback_yield_fy REAL,
            total_yield_fy REAL,
            PRIMARY KEY (lei, fy)
        )
    """)

    # Create original history table if not exists
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
            buyback_annual REAL,
            buyback_yield REAL,
            payout_yield REAL,
            PRIMARY KEY (lei, date)
        )
    """)

    
    # Get publicly traded banks with tickers only
    cur.execute("""
        SELECT lei, ticker, commercial_name FROM institutions
        WHERE ticker IS NOT NULL AND trading_status = 'Public'
    """)
    banks = cur.fetchall()

    print(f"Fetching historical data for {len(banks)} public banks...")
    
    for lei, ticker, name in banks:
        # Use primary ticker, but check for historical override
        fetch_ticker = HISTORY_TICKER_MAP.get(lei, ticker)
        
        safe_name = name[:30].encode('ascii', 'replace').decode('ascii')
        print(f"  {fetch_ticker:12} | {safe_name} (LEI: {lei[:8]}...)", end=" ")
        
        data_bundle = fetch_price_history(fetch_ticker, period="5y")
        
        if data_bundle and not data_bundle['monthly'].empty:
            df_hist = data_bundle['monthly']
            df_fy = data_bundle['financial_years']
            
            # 1. Monthly History Guard
            cur.execute("SELECT COUNT(*) FROM market_history WHERE lei = ?", (lei,))
            local_count = cur.fetchone()[0]
            
            if local_count > len(df_hist) + 3:
                print(f"SKIPPED MONTHLY - Local history is richer")
            else:
                # Clear and Insert Monthly
                cur.execute("DELETE FROM market_history WHERE lei = ?", (lei,))
                for _, row in df_hist.iterrows():
                    cur.execute("""
                        INSERT OR REPLACE INTO market_history 
                        (lei, ticker, date, close, dividend, dividend_ttm, dividend_yield, market_cap,
                         buyback_annual, buyback_yield, payout_yield)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (lei, ticker, row['date'], row['close'], row['dividend'], 
                          row['dividend_ttm'], row['dividend_yield'], row.get('market_cap'),
                          row.get('buyback_annual'), row.get('buyback_yield'), row.get('payout_yield')))

            # 2. Financial Year Attribution Insert
            if not df_fy.empty:
                cur.execute("DELETE FROM market_financial_years WHERE lei = ?", (lei,))
                for _, row in df_fy.iterrows():
                    cur.execute("""
                        INSERT INTO market_financial_years
                        (lei, ticker, fy, avg_price, avg_market_cap, net_income,
                         dividend_amt, buyback_amt, eps_fy, dps_fy,
                         dividend_yield_fy, buyback_yield_fy, total_yield_fy)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (lei, ticker, int(row['fy']), row['avg_price'], row['avg_market_cap'], row['net_income'],
                          row['dividend_amt'], row['buyback_amt'], row['eps_fy'], row['dps_fy'],
                          row['dividend_yield_fy'], row['buyback_yield_fy'], row['total_yield_fy']))

            print(f"OK ({len(df_hist)} months, {len(df_fy)} fiscal years)")
        else:
            print("FAIL")
    
    conn.commit()
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--history':
        refresh_market_history()
    else:
        refresh_market_data()

