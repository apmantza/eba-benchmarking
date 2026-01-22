import pandas as pd
import sqlite3
import streamlit as st
import os
from ..config import DB_NAME
from .base import MIN_PERIOD, get_benchmark_leis

@st.cache_data
def get_liquidity_kpis(lei_list):
    """
    Calculates key liquidity metrics:
    - LDR (Loan-to-Deposit Ratio) = Loans / Customer Deposits
    - Funding Gap = Loans - Customer Deposits
    """
    if not lei_list or not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    
    # Items needed:
    # Loans: 2521017 (FV) + 2521019 (AC)
    # Customer Deposits: from 2521215 with instrument=30, exposure in (301, 401)
    
    # Query 1: Loans
    query_loans = f"""
    SELECT f.lei, COALESCE(i.short_name, i.commercial_name) as name, f.period, 
           SUM(CASE WHEN f.item_id IN ('2521017', '2521019') THEN f.amount ELSE 0 END) as loans
    FROM facts_oth f
    JOIN institutions i ON f.lei = i.lei
    WHERE f.lei IN ({leis_str}) 
      AND f.item_id IN ('2521017', '2521019')
      AND f.period >= '{MIN_PERIOD}'
    GROUP BY f.lei, f.period
    """
    
    # Query 2: Customer Deposits (NFC + Households)
    query_deposits = f"""
    SELECT lei, period,
           SUM(amount) as customer_deposits
    FROM facts_oth
    WHERE lei IN ({leis_str}) 
      AND item_id = '2521215'
      AND financial_instruments = 30
      AND exposure IN (301, 401)
      AND period >= '{MIN_PERIOD}'
    GROUP BY lei, period
    """
    
    try:
        df_loans = pd.read_sql(query_loans, conn)
        df_deposits = pd.read_sql(query_deposits, conn)
        conn.close()
        
        if df_loans.empty:
            return pd.DataFrame()
        
        # Merge
        df = pd.merge(df_loans, df_deposits, on=['lei', 'period'], how='left')
        df['customer_deposits'] = df['customer_deposits'].fillna(0)
        
        # Calculate LDR
        df['LDR'] = df.apply(
            lambda x: x['loans'] / x['customer_deposits'] if x['customer_deposits'] > 0 else 0,
            axis=1
        )
        
        # Funding Gap (in millions)
        df['Funding Gap'] = df['loans'] - df['customer_deposits']
        
        # Deposit Funding Ratio = Customer Deposits / Loans
        df['Deposit Coverage'] = df.apply(
            lambda x: x['customer_deposits'] / x['loans'] if x['loans'] > 0 else 0,
            axis=1
        )
        
        return df
        
    except Exception as e:
        if conn: conn.close()
        print(f"Error in get_liquidity_kpis: {e}")
        return pd.DataFrame()

@st.cache_data
def get_liquidity_averages(country_iso, region, systemic_importance, size_category=None):
    """Calculates Domestic, Regional, EU averages for Liquidity metrics based on Size logic."""
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    groups = get_benchmark_leis(country_iso, region, systemic_importance, size_category)
    conn.close()
    
    all_results = []
    for label, leis in groups.items():
        if not leis: continue
        df_group = get_liquidity_kpis(leis)
        if df_group.empty: continue
        
        # Weighted average by loans (larger banks get more weight)
        def weighted_avg(group):
            d = {}
            w = group['loans']
            
            def get_w_avg(col):
                valid = group[[col, 'loans']].dropna()
                if not valid.empty and valid['loans'].sum() > 0:
                    return (valid[col] * valid['loans']).sum() / valid['loans'].sum()
                return group[col].mean() if col in group.columns else 0
            
            d['LDR'] = get_w_avg('LDR')
            d['Deposit Coverage'] = get_w_avg('Deposit Coverage')
            d['loans'] = group['loans'].mean()
            d['customer_deposits'] = group['customer_deposits'].mean()
            d['Funding Gap'] = group['Funding Gap'].mean()
            
            return pd.Series(d)
        
        df_avg = df_group.groupby('period').apply(weighted_avg, include_groups=False).reset_index()
        df_avg['name'] = label
        all_results.append(df_avg)
    
    return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
