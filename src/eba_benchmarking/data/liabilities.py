import pandas as pd
import sqlite3
import streamlit as st
import os
from ..config import DB_NAME
from .base import MIN_PERIOD, get_benchmark_leis
from .solvency import get_solvency_kpis

@st.cache_data
def get_liabilities_kpis(lei_list):
    """
    Fetches main liability categories.
    Uses item 2521215 with instrument and exposure dimensions.
    - Instrument 30, Exposure 101: Central Bank
    - Instrument 30, Exposure 102: Interbank
    - Instrument 30, Exposure 301+401: Customer Deposits
    - Instrument 40: Debt Securities Issued
    - Instrument 12: Derivatives
    - 2521214: Total Liabilities
    """
    if not lei_list or not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    
    # 1. Fetch breakdown from 2521215
    query_brk = f"""
    SELECT lei, period, financial_instruments, exposure, SUM(amount) as amount
    FROM facts_oth 
    WHERE lei IN ({leis_str}) AND item_id = '2521215' AND period >= '{MIN_PERIOD}'
    GROUP BY lei, period, financial_instruments, exposure
    """
    
    # 2. Fetch Total Liabilities from 2521214
    query_tot = f"""
    SELECT f.lei, i.commercial_name as name, f.period, SUM(f.amount) as total_liabilities
    FROM facts_oth f
    JOIN institutions i ON f.lei = i.lei
    WHERE f.lei IN ({leis_str}) AND f.item_id = '2521214' AND f.period >= '{MIN_PERIOD}'
    GROUP BY f.lei, f.period
    """

    # 3. Fetch Equity (CET1) from 2520102
    query_eq = f"""
    SELECT lei, period, SUM(amount) as equity
    FROM facts_oth
    WHERE lei IN ({leis_str}) AND item_id = '2520102' AND period >= '{MIN_PERIOD}'
    GROUP BY lei, period
    """
    
    try:
        df_brk = pd.read_sql(query_brk, conn)
        df_tot = pd.read_sql(query_tot, conn)
        df_eq = pd.read_sql(query_eq, conn)
        conn.close()
        
        if df_tot.empty: return pd.DataFrame()
        
        # Process breakdown
        def aggregate_liabilities(group):
            d = {}
            # Customer Deposits (301: NFC, 401: Households)
            d['Customer Deposits'] = group[(group['financial_instruments'] == 30) & (group['exposure'].isin([301, 401]))]['amount'].sum()
            # Interbank (102: Credit Institutions)
            d['Interbank Deposits'] = group[(group['financial_instruments'] == 30) & (group['exposure'] == 102)]['amount'].sum()
            # Central Bank (101)
            d['Central Bank Funding'] = group[(group['financial_instruments'] == 30) & (group['exposure'] == 101)]['amount'].sum()
            # Debt Securities Issued (40)
            d['Debt Securities Issued'] = group[group['financial_instruments'] == 40]['amount'].sum()
            # Derivatives (12)
            d['Derivatives (Liab)'] = group[group['financial_instruments'] == 12]['amount'].sum()
            return pd.Series(d)

        df_agg = df_brk.groupby(['lei', 'period']).apply(aggregate_liabilities, include_groups=False).reset_index()
        
        df_final = pd.merge(df_tot, df_agg, on=['lei', 'period'], how='left').fillna(0)
        df_final = pd.merge(df_final, df_eq, on=['lei', 'period'], how='left').fillna(0)
        
        # Total Equity & Liabilities
        df_final['total_eq_liab'] = df_final['total_liabilities'] + df_final['equity']
        
        # Other Liabilities calculation (residual of total_liabilities)
        sum_known = df_final['Customer Deposits'] + df_final['Interbank Deposits'] + df_final['Central Bank Funding'] + df_final['Debt Securities Issued'] + df_final['Derivatives (Liab)']
        df_final['Other Liabilities'] = (df_final['total_liabilities'] - sum_known).apply(lambda x: max(0, x))
        
        # Ratios (relative to total equity & liabilities)
        df_final['Customer Deposit Ratio'] = df_final.apply(lambda x: x['Customer Deposits'] / x['total_eq_liab'] if x['total_eq_liab'] > 0 else 0, axis=1)
        df_final['Wholesale Funding Ratio'] = df_final.apply(lambda x: (x['Interbank Deposits'] + x['Debt Securities Issued']) / x['total_eq_liab'] if x['total_eq_liab'] > 0 else 0, axis=1)
        df_final['Equity Ratio'] = df_final.apply(lambda x: x['equity'] / x['total_eq_liab'] if x['total_eq_liab'] > 0 else 0, axis=1)
        
        return df_final
        
    except Exception as e:
        if conn: conn.close()
        print(f"Error in get_liabilities_kpis: {e}")
        return pd.DataFrame()

@st.cache_data
def get_liabilities_averages(country_iso, region, systemic_importance, size_category=None):
    """Calculates Domestic, Regional, EU group averages for Liabilities based on Size logic."""
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    groups = get_benchmark_leis(country_iso, region, systemic_importance, size_category)
    
    all_results = []
    
    for label, leis in groups.items():
        if not leis: continue
        df_group = get_liabilities_kpis(leis)
        if df_group.empty: continue
        
        # --- NO OUTLIER REMOVAL ---
        df_filtered = df_group.copy()

        if df_filtered.empty: continue

        def weighted_avg(group):
            w = group['total_eq_liab']
            d = {}
            def get_w_avg(m_col):
                v = group[[m_col, 'total_eq_liab']].dropna()
                return (v[m_col] * v['total_eq_liab']).sum() / v['total_eq_liab'].sum() if v['total_eq_liab'].sum() > 0 else group[m_col].mean()
            
            d['Customer Deposit Ratio'] = get_w_avg('Customer Deposit Ratio')
            d['Wholesale Funding Ratio'] = get_w_avg('Wholesale Funding Ratio')
            d['Equity Ratio'] = get_w_avg('Equity Ratio')
            
            for col in ['total_liabilities', 'total_eq_liab', 'equity', 'Customer Deposits', 'Interbank Deposits', 'Central Bank Funding', 'Debt Securities Issued', 'Other Liabilities']:
                d[col] = group[col].mean()
            return pd.Series(d)

        df_avg = df_filtered.groupby('period').apply(weighted_avg, include_groups=False).reset_index().assign(name=label)
        all_results.append(df_avg)
    conn.close()
    return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()

@st.cache_data
def get_deposit_beta(lei_list):
    """
    Calculates Deposit Beta: the sensitivity of implied deposit cost to ECB rate changes.
    Beta = Δ(Implied Deposit Cost) / Δ(ECB Deposit Facility Rate)
    
    A beta < 1 means the bank passes through less than 100% of rate increases to depositors (positive for margins).
    A beta > 1 means the bank has to pass through more than rates (negative for margins).
    """
    if not lei_list or not os.path.exists(DB_NAME): return pd.DataFrame()
    
    # 1. Get Implied Deposit Cost from NII Analysis
    from .profitability import get_nii_analysis
    df_nii = get_nii_analysis(lei_list)
    
    if df_nii.empty or 'Implied Deposit Cost' not in df_nii.columns:
        return pd.DataFrame()
    
    # 2. Get ECB Deposit Facility Rate
    conn = sqlite3.connect(DB_NAME)
    df_ecb = pd.read_sql("SELECT date, value as ecb_rate FROM base_rates WHERE metric = 'Deposit Facility Rate'", conn)
    conn.close()
    
    if df_ecb.empty:
        return pd.DataFrame()
    
    # Normalize periods
    df_nii['period_m'] = df_nii['period'].apply(lambda x: str(x)[:7])
    df_ecb['period_m'] = df_ecb['date'].apply(lambda x: str(x)[:7])
    df_ecb['ecb_rate'] = df_ecb['ecb_rate'] / 100  # Convert from % to decimal
    
    # Merge
    df = pd.merge(df_nii[['lei', 'name', 'period', 'period_m', 'Implied Deposit Cost']], 
                  df_ecb[['period_m', 'ecb_rate']], on='period_m', how='left')
    
    if df['ecb_rate'].isna().all():
        return pd.DataFrame()
    
    # Sort by period for proper diff calculation
    df = df.sort_values(['lei', 'period'])
    
    # 3. Calculate changes (period over period)
    df['deposit_cost_change'] = df.groupby('lei')['Implied Deposit Cost'].diff()
    df['ecb_rate_change'] = df.groupby('lei')['ecb_rate'].diff()
    
    # 4. Calculate Beta (only where ECB rate changed significantly)
    # Beta = Δ Deposit Cost / Δ ECB Rate
    df['deposit_beta'] = df.apply(
        lambda x: x['deposit_cost_change'] / x['ecb_rate_change'] 
        if x['ecb_rate_change'] is not None and abs(x['ecb_rate_change']) > 0.001 
        else None, 
        axis=1
    )
    
    # 5. Calculate cumulative beta (from a reference point, e.g., Q4 2021 before rate hikes)
    # Reference: Q4 2021 (rates were ~0, deposits were cheap)
    ref_period = '2021-12'
    
    for lei in df['lei'].unique():
        mask = df['lei'] == lei
        df_bank = df[mask].copy()
        
        # Find reference values
        ref_row = df_bank[df_bank['period_m'] == ref_period]
        if ref_row.empty:
            # Fallback to earliest period
            ref_row = df_bank.iloc[:1]
        
        if not ref_row.empty:
            ref_dep_cost = ref_row['Implied Deposit Cost'].values[0]
            ref_ecb = ref_row['ecb_rate'].values[0] if not pd.isna(ref_row['ecb_rate'].values[0]) else 0
            
            df.loc[mask, 'cumulative_deposit_change'] = df.loc[mask, 'Implied Deposit Cost'] - ref_dep_cost
            df.loc[mask, 'cumulative_ecb_change'] = df.loc[mask, 'ecb_rate'] - ref_ecb
            
            # Cumulative Beta
            df.loc[mask, 'cumulative_beta'] = df.loc[mask].apply(
                lambda x: x['cumulative_deposit_change'] / x['cumulative_ecb_change']
                if x['cumulative_ecb_change'] is not None and abs(x['cumulative_ecb_change']) > 0.005
                else None,
                axis=1
            )
    
    return df

