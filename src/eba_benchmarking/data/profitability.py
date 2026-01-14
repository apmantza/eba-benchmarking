import pandas as pd
import sqlite3
import streamlit as st
import os
from ..config import DB_NAME, PROFITABILITY_ITEMS
from .base import MIN_PERIOD, get_benchmark_leis

def calculate_implied_rates(df):
    """
    Calculates implied yields and funding costs for a DataFrame 
    containing profitability and balance sheet items.
    """
    if df.empty: return df

    # Helper: Annualization
    if 'ann_factor' not in df.columns:
        df['month'] = df['period'].apply(lambda x: int(x.split('-')[1]) if isinstance(x, str) else 12)
        df['ann_factor'] = 12 / df['month']

    # --- YIELDS ---
    # Loans Yield
    if 'Int Inc: Loans' in df.columns and 'Loans and advances' in df.columns:
        df['Implied Loan Yield'] = df.apply(
            lambda x: (x['Int Inc: Loans'] / x['Loans and advances']) * x['ann_factor'] if x['Loans and advances'] > 0 else 0, axis=1
        )
    
    # Securities Yield
    if 'Int Inc: Debt Securities' in df.columns and 'Debt Securities' in df.columns:
        df['Implied Securities Yield'] = df.apply(
            lambda x: (x['Int Inc: Debt Securities'] / x['Debt Securities']) * x['ann_factor'] if x['Debt Securities'] > 0 else 0, axis=1
        )
    
    # --- COSTS ---
    # Deposit Cost
    if 'Int Exp: Deposits' in df.columns and 'Customer Deposits' in df.columns:
        df['Implied Deposit Cost'] = df.apply(
            lambda x: (x['Int Exp: Deposits'] / x['Customer Deposits']) * x['ann_factor'] if x['Customer Deposits'] > 0 else 0, axis=1
        )

    # Debt Issued Cost
    if 'Int Exp: Debt Securities' in df.columns and 'Debt Securities Issued' in df.columns:
        df['Implied Debt Cost'] = df.apply(
            lambda x: (x['Int Exp: Debt Securities'] / x['Debt Securities Issued']) * x['ann_factor'] if x['Debt Securities Issued'] > 0 else 0, axis=1
        )

    # Implied Interbank & Other Funding Cost (Residual)
    # Total Interest Exp - (Deposits + Debt) / (Total Liab - Customer Deposits - Debt Issued)
    if 'Interest Expenses' in df.columns:
        df['Implied Interbank Cost'] = df.apply(
            lambda x: ((x['Interest Expenses'] - x.get('Int Exp: Deposits', 0) - x.get('Int Exp: Debt Securities', 0)) / 
                       (x['total_liabilities'] - x.get('Customer Deposits', 0) - x.get('Debt Securities Issued', 0))) * x['ann_factor'] 
                       if (x['total_liabilities'] - x.get('Customer Deposits', 0) - x.get('Debt Securities Issued', 0)) > 0 else 0,
            axis=1
        )

    # Total Funding Cost
    if 'Interest Expenses' in df.columns and 'total_liabilities' in df.columns:
        df['Implied Funding Cost'] = df.apply(
            lambda x: (x['Interest Expenses'] / x['total_liabilities']) * x['ann_factor'] if x['total_liabilities'] > 0 else 0, axis=1
        )
    
    # Cleanup Outliers (0% - 20%)
    # Only clean the absolute rates, not the margins
    rate_cols = ['Implied Loan Yield', 'Implied Securities Yield', 'Implied Deposit Cost', 'Implied Debt Cost', 'Implied Interbank Cost', 'Implied Funding Cost']
    for col in rate_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x if 0 <= x <= 0.20 else 0)

    # --- SPREADS OVER EURIBOR 3M ---
    # Fetch Euribor 3M
    try:
        conn = sqlite3.connect(DB_NAME)
        # Assuming period in df is YYYY-MM-DD or YYYY-MM
        # Base rates table uses YYYY-MM-DD (normalized) based on recent checks
        df_euribor = pd.read_sql("SELECT date, value as euribor_3m FROM base_rates WHERE metric = 'Euribor 3M'", conn)
        conn.close()
        
        if not df_euribor.empty:
            # Map df period to YYYY-MM
            df['period_m'] = df['period'].apply(lambda x: str(x)[:7])
            
            # Map euribor date to YYYY-MM
            df_euribor['period_m'] = df_euribor['date'].apply(lambda x: str(x)[:7])
            
            # Select only necessary columns to avoid confusion
            df_euribor_clean = df_euribor[['period_m', 'euribor_3m']].copy()
            
            # Merge
            df = pd.merge(df, df_euribor_clean, on='period_m', how='left')
            
            # Euribor 3M is likely stored as %, e.g. 3.5. Convert to decimal.
            df['euribor_decimal'] = df['euribor_3m'] / 100
            
            # Calculate Margins
            for col in rate_cols:
                if col in df.columns:
                    # Remove "Implied " for the margin name
                    margin_name = col.replace("Implied ", "")
                    # Construct Margin Column Name: "Margin: Loan Yield", "Margin: Funding Cost"
                    margin_col = f"Margin: {margin_name}"
                    df[margin_col] = df[col] - df['euribor_decimal']
                    
    except Exception as e:
        print(f"Error calculating spreads: {e}")
        # Add columns with NaN if fail, to avoid KeyErrors later
        for col in rate_cols:
             margin_col = f"Margin: {col.replace('Implied ', '')}"
             if margin_col not in df.columns:
                 df[margin_col] = None

    return df

@st.cache_data
def get_profitability_kpis(lei_list):
    """
    Fetches profitability items and calculates key ratios:
    - RoE (Return on Equity)
    - RoA (Return on Assets)
    - Cost-to-Income Ratio (CIR)
    - Net Interest Margin (NIM)
    """
    if not lei_list or not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    leis_str = "'" + "','".join([str(l) for l in lei_list]) + "'"
    items = list(PROFITABILITY_ITEMS.keys())
    items_str = "'" + "','".join(items) + "'"
    
    query = f"""
        SELECT f.lei, i.commercial_name as name, f.period, f.item_id, f.amount 
        FROM facts_oth f 
        JOIN institutions i ON f.lei = i.lei 
        WHERE f.lei IN ({leis_str}) 
          AND f.item_id IN ({items_str}) 
          AND f.period >= '{MIN_PERIOD}'
    """
    
    try:
        df = pd.read_sql(query, conn)
        conn.close()
        if df.empty: return pd.DataFrame()
        
        df_pivot = df.pivot_table(
            index=['lei', 'name', 'period'], 
            columns='item_id', 
            values='amount', 
            aggfunc='sum'
        ).reset_index()
        
        # Rename columns using config
        df_pivot.rename(columns=PROFITABILITY_ITEMS, inplace=True)
        
        # Ensure all columns exist
        for col in PROFITABILITY_ITEMS.values():
            if col not in df_pivot.columns: df_pivot[col] = 0
            
        # --- CALCULATIONS ---
        
        # 0. Annualization Factor
        # Extract month from period string (YYYY-MM-DD)
        df_pivot['month'] = df_pivot['period'].apply(lambda x: int(x.split('-')[1]) if isinstance(x, str) else 12)
        df_pivot['ann_factor'] = 12 / df_pivot['month']
        
        # 1. Return on Equity (RoE) = Net Profit / Total Equity
        # Standard (YTD)
        df_pivot['RoE'] = df_pivot.apply(
            lambda x: x['Net Profit'] / x['Total Equity'] if x['Total Equity'] > 0 else 0, 
            axis=1
        )
        # Annualized
        df_pivot['RoE (Annualized)'] = df_pivot['RoE'] * df_pivot['ann_factor']
        
        # 2. Return on Assets (RoA) = Net Profit / Total Assets
        # Standard (YTD)
        df_pivot['RoA'] = df_pivot.apply(
            lambda x: x['Net Profit'] / x['Total Assets'] if x['Total Assets'] > 0 else 0, 
            axis=1
        )
        # Annualized
        df_pivot['RoA (Annualized)'] = df_pivot['RoA'] * df_pivot['ann_factor']
        
        # 2b. Return on RWA (RoRWA) = Net Profit / TREA
        # Standard (YTD)
        if 'TREA' in df_pivot.columns:
            df_pivot['RoRWA'] = df_pivot.apply(
                lambda x: x['Net Profit'] / x['TREA'] if x['TREA'] > 0 else 0, 
                axis=1
            )
            # Annualized
            df_pivot['RoRWA (Annualized)'] = df_pivot['RoRWA'] * df_pivot['ann_factor']
        else:
            df_pivot['RoRWA'] = 0
            df_pivot['RoRWA (Annualized)'] = 0
        
        # 3. Cost to Income Ratio (CIR) = (Admin Expenses + Depreciation) / Total Operating Income
        # Note: Expenses are positive in DB, so we sum them.
        df_pivot['Operating Expenses'] = df_pivot['Admin Expenses'] + df_pivot['Depreciation']
        df_pivot['Cost to Income'] = df_pivot.apply(
            lambda x: x['Operating Expenses'] / x['Total Operating Income'] if x['Total Operating Income'] > 0 else 0, 
            axis=1
        )
        
        # 4. Net Interest Margin (NIM) = (Interest Income - Interest Expenses) / Total Assets
        # (Simplified NIM as Average Interest Earning Assets is hard to get precisely)
        df_pivot['Net Interest Income'] = df_pivot['Interest Income'] - df_pivot['Interest Expenses']
        df_pivot['NIM'] = df_pivot.apply(
            lambda x: x['Net Interest Income'] / x['Total Assets'] if x['Total Assets'] > 0 else 0, 
            axis=1
        )
        df_pivot['NIM (Annualized)'] = df_pivot['NIM'] * df_pivot['ann_factor']
        
        # 5. Non-Interest Income portion
        df_pivot['Non-Interest Income'] = df_pivot['Total Operating Income'] - df_pivot['Net Interest Income']
        
        # 6. Granular Components
        df_pivot['Net Trading Income'] = df_pivot['Trading Income'] + df_pivot['FX Income']
        # Calculate Tax Expenses (Expectation: PBT > Net Profit usually, so PBT - Net Profit = Tax)
        df_pivot['Tax Expenses'] = df_pivot['Profit Before Tax'] - df_pivot['Net Profit']
        
        # 7. New Ratios: Net Fees / Assets & Cost of Risk
        df_pivot['Net Fees / Assets'] = df_pivot.apply(
            lambda x: x['Net Fee & Commission Income'] / x['Total Assets'] if x['Total Assets'] > 0 else 0,
            axis=1
        )
        df_pivot['Net Fees / Assets (Annualized)'] = df_pivot['Net Fees / Assets'] * df_pivot['ann_factor']
        
        df_pivot['Cost of Risk'] = df_pivot.apply(
            lambda x: x['Impairment Cost'] / x['Total Assets'] if x['Total Assets'] > 0 else 0,
            axis=1
        )
        df_pivot['Cost of Risk (Annualized)'] = df_pivot['Cost of Risk'] * df_pivot['ann_factor']
        
        # 8. Cost per Assets (Operating Efficiency)
        # OpEx / Total Assets - shows cost efficiency relative to size
        df_pivot['Cost per Assets'] = df_pivot.apply(
            lambda x: x['Operating Expenses'] / x['Total Assets'] if x['Total Assets'] > 0 else 0,
            axis=1
        )
        df_pivot['Cost per Assets (Annualized)'] = df_pivot['Cost per Assets'] * df_pivot['ann_factor']

        return df_pivot
        
    except Exception as e:
        if conn: conn.close()
        print(f"Error fetching profitability data: {e}")
        return pd.DataFrame()

@st.cache_data
def get_nii_analysis(lei_list):
    """
    Fetches detailed Interest Income/Expense components and Balance Sheet volumes 
    to calculate implied yields and costs.
    """
    if not lei_list or not os.path.exists(DB_NAME): return pd.DataFrame()
    
    # Reuse existing modules to fetch data pieces
    # 1. P&L Items
    df_pl = get_profitability_kpis(lei_list)
    if df_pl.empty: return pd.DataFrame()
    
    # 2. Asset Volumes (Loans, Securities)
    from .assets import get_assets_kpis
    df_assets = get_assets_kpis(lei_list)
    
    # 3. Liability Volumes (Deposits, Debt Issued)
    from .liabilities import get_liabilities_kpis
    df_liabs = get_liabilities_kpis(lei_list)
    
    # Merge everything on [lei, name, period]
    df = pd.merge(df_pl, df_assets[['lei', 'period', 'Loans and advances', 'Debt Securities', 'Total Assets']], on=['lei', 'period'], how='left')
    df = pd.merge(df, df_liabs[['lei', 'period', 'Customer Deposits', 'Debt Securities Issued', 'total_liabilities']], on=['lei', 'period'], how='left')
    
    return calculate_implied_rates(df)

@st.cache_data
def get_nii_averages(country_iso, region, systemic_importance, size_category=None):
    """Calculates Domestic, Regional, EU averages for NII Analysis (Implied Rates) based on Size logic."""
    # 1. Fetch Profitability Averages (Contains Interest Inc/Exp components)
    df_prof_avg = get_profitability_averages(country_iso, region, systemic_importance, size_category)
    if df_prof_avg.empty: return pd.DataFrame()
    
    # 2. Fetch Asset Averages (Contains Loans, Debt Sec volumes)
    from .assets import get_assets_averages
    df_asset_avg = get_assets_averages(country_iso, region, systemic_importance, size_category)
    
    # 3. Fetch Liability Averages (Contains Deposits, Debt Issued volumes)
    from .liabilities import get_liabilities_averages
    df_liab_avg = get_liabilities_averages(country_iso, region, systemic_importance, size_category)
    
    # Merge
    # We merge on [name, period]. 'lei' is not present in averages DF or is meaningless.
    df = pd.merge(df_prof_avg, df_asset_avg[['name', 'period', 'Loans and advances', 'Debt Securities', 'Total Assets']], on=['name', 'period'], how='left')
    df = pd.merge(df, df_liab_avg[['name', 'period', 'Customer Deposits', 'Debt Securities Issued', 'total_liabilities']], on=['name', 'period'], how='left')
    
    return calculate_implied_rates(df)

@st.cache_data
def get_profitability_averages(country_iso, region, systemic_importance, size_category=None):
    """Calculates Domestic, Regional, EU averages for Profitability based on Size logic."""
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    groups = get_benchmark_leis(country_iso, region, systemic_importance, size_category)
    
    all_results = []
    
    for label, leis in groups.items():
        if not leis: continue
        
        # Fetch raw data for the group
        df_group = get_profitability_kpis(leis)
        
        if df_group.empty: continue
        
        # --- NO OUTLIER REMOVAL ---
        df_filtered = df_group.copy()
        
        if df_filtered.empty: continue
        
        # --- WEIGHTED AVERAGES ---
        # We weigh by Total Assets (or Equity/Income depending on metric, but Assets is standard proxy)
        def weighted_avg(group):
            w = group['Total Assets'] # Weight
            d = {}
            
            def get_w_avg(col):
                if col not in group.columns or 'Total Assets' not in group.columns: return 0
                valid = group[[col, 'Total Assets']].dropna()
                if not valid.empty and valid['Total Assets'].sum() > 0:
                    return (valid[col] * valid['Total Assets']).sum() / valid['Total Assets'].sum()
                return group[col].mean()

            # Ratios
            d['RoE'] = get_w_avg('RoE')
            d['RoE (Annualized)'] = get_w_avg('RoE (Annualized)')
            
            d['RoA'] = get_w_avg('RoA')
            d['RoA (Annualized)'] = get_w_avg('RoA (Annualized)')
            
            d['Cost to Income'] = get_w_avg('Cost to Income')
            
            d['NIM'] = get_w_avg('NIM')
            d['NIM (Annualized)'] = get_w_avg('NIM (Annualized)')

            d['Net Fees / Assets'] = get_w_avg('Net Fees / Assets')
            d['Net Fees / Assets (Annualized)'] = get_w_avg('Net Fees / Assets (Annualized)')
            
            d['Cost of Risk'] = get_w_avg('Cost of Risk')
            d['Cost of Risk (Annualized)'] = get_w_avg('Cost of Risk (Annualized)')
            
            d['Cost per Assets'] = get_w_avg('Cost per Assets')
            d['Cost per Assets (Annualized)'] = get_w_avg('Cost per Assets (Annualized)')
            
            d['RoRWA'] = get_w_avg('RoRWA')
            d['RoRWA (Annualized)'] = get_w_avg('RoRWA (Annualized)')
            
            # Absolute Amounts (Mean)
            cols = [
                'Net Profit', 'Total Operating Income', 'Operating Expenses', 
                'Net Interest Income', 'Non-Interest Income', 'Total Assets',
                'Dividend Income', 'Net Fee & Commission Income', 'Net Trading Income', 
                'Other Operating Income', 'Admin Expenses', 'Depreciation', 'Provisions', 
                'Impairment Cost', 'Tax Expenses',
                'Int Inc: Debt Securities', 'Int Inc: Loans', 
                'Int Exp: Deposits', 'Int Exp: Debt Securities', 'Interest Income', 'Interest Expenses'
            ]
            for c in cols:
                if c in group.columns: d[c] = group[c].mean()
                
            return pd.Series(d)

        df_avg = df_filtered.groupby('period').apply(weighted_avg, include_groups=False).reset_index()
        df_avg['name'] = label
        all_results.append(df_avg)

    conn.close()
    return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()