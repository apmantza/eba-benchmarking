import pandas as pd
import re

def normalize_period(period_str):
    """
    Standardizes inconsistent period strings into 'YYYY-MM-DD' (Month End).
    Supports: YYYY, YYYY-MM, YYYY-QX, YYYY-MXX, YYYY-MM-DD
    """
    if pd.isna(period_str) or not str(period_str).strip():
        return None
    
    p = str(period_str).strip()
    
    try:
        # 1. Handle Quarterly (YYYY-QX)
        if re.match(r'^\d{4}-Q[1-4]$', p):
            year, q = p.split('-Q')
            month = int(q) * 3
            return pd.Timestamp(year=int(year), month=month, day=1).replace(day=pd.Timestamp(year=int(year), month=month, day=1).days_in_month).strftime('%Y-%m-%d')
        
        # 2. Handle Eurostat Monthly (YYYY-MXX)
        if re.match(r'^\d{4}-M\d{2}$', p):
            year, month = p.split('-M')
            return pd.Timestamp(year=int(year), month=int(month), day=1).replace(day=pd.Timestamp(year=int(year), month=int(month), day=1).days_in_month).strftime('%Y-%m-%d')
        
        # 3. Handle Yearly (YYYY)
        if re.match(r'^\d{4}$', p):
            return f"{p}-12-31"
        
        # 4. Handle YYYYMM (e.g., 201412)
        if re.match(r'^\d{6}$', p):
            year = int(p[:4])
            month = int(p[4:])
            return pd.Timestamp(year=year, month=month, day=1).replace(day=pd.Timestamp(year=year, month=month, day=1).days_in_month).strftime('%Y-%m-%d')

        # 5. Handle YYYY-MM
        if re.match(r'^\d{4}-\d{2}$', p):
            year, month = p.split('-')
            return pd.Timestamp(year=int(year), month=int(month), day=1).replace(day=pd.Timestamp(year=int(year), month=int(month), day=1).days_in_month).strftime('%Y-%m-%d')
            
        # 5. Default: Try pandas to_datetime and force to month end
        dt = pd.to_datetime(p)
        return dt.replace(day=dt.days_in_month).strftime('%Y-%m-%d')
        
    except:
        return p # Return original if parsing fails

def get_item_mapping(conn, year):
    """
    Returns a dict mapping {original_id: canonical_id} for a specific exercise year.
    """
    try:
        query = f"SELECT original_item_id, canonical_item_id FROM item_mappings WHERE exercise_year = '{year}'"
        df = pd.read_sql(query, conn)
        return dict(zip(df['original_item_id'], df['canonical_item_id']))
    except:
        return {}

def format_value(val, unit=None, decimals=2):
    """
    Format a numeric value with optional unit sealing and decimal precision.
    unit: 'M' (Millions), 'B' (Billions), 'K' (Thousands), '%' (Percentage)
    """
    if pd.isna(val) or val is None:
        return "-"
    
    try:
        val = float(val)
    except:
        return val

    if unit == 'M':
         return f"{val/1e6:,.{decimals}f}M"
    elif unit == 'B':
         return f"{val/1e9:,.{decimals}f}B"
    elif unit == 'K':
         return f"{val/1e3:,.{decimals}f}K"
    elif unit == '%':
         # Assumes val is 0.12 for 12%
         return f"{val*100:,.{decimals}f}%"
    else:
         return f"{val:,.{decimals}f}"
