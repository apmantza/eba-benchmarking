import pandas as pd
import sqlite3
import streamlit as st
import os
from ..config import DB_NAME
from .base import MIN_PERIOD, get_benchmark_leis
from .solvency import get_solvency_kpis

@st.cache_data
def get_assets_kpis(lei_list):
    """Fetches main asset categories and calculates ratios."""
    if not lei_list or not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    items = {
        '2521010': 'Total Assets',
        '2521001': 'Cash',
        '2521017': 'Loans FV',
        '2521019': 'Loans AC',
        '2521016': 'Debt Sec FV',
        '2521018': 'Debt Sec AC',
        '2521002': 'Trading Assets',
        '2521003': 'Non-Trading FVTPL',
        '2521004': 'Designated FVTPL'
    }
    items_str = "'" + "','".join(items.keys()) + "'"
    query = f"SELECT f.lei, i.commercial_name as name, f.period, f.item_id, f.amount FROM facts_oth f JOIN institutions i ON f.lei = i.lei WHERE f.lei IN ({leis_str}) AND f.item_id IN ({items_str}) AND f.period >= '{MIN_PERIOD}'"
    try:
        df = pd.read_sql(query, conn); conn.close()
        if df.empty: return pd.DataFrame()
        df_p = df.pivot_table(index=['lei', 'name', 'period'], columns='item_id', values='amount', aggfunc='sum').reset_index().rename(columns=items)
        for col in items.values():
            if col not in df_p.columns: df_p[col] = 0
        df_p['Loans and advances'] = df_p['Loans FV'] + df_p['Loans AC']
        df_p['Debt Securities'] = df_p['Debt Sec FV'] + df_p['Debt Sec AC']
        df_p['Securities'] = df_p['Debt Securities'] + df_p['Trading Assets'] + df_p['Non-Trading FVTPL'] + df_p['Designated FVTPL']
        df_p['Other Assets'] = (df_p['Total Assets'] - df_p['Cash'] - df_p['Loans and advances'] - df_p['Securities']).apply(lambda x: max(0, x))
        df_p['Loans to Assets'] = df_p.apply(lambda x: x['Loans and advances'] / x['Total Assets'] if x['Total Assets'] > 0 else 0, axis=1)
        df_p['Cash to Assets'] = df_p.apply(lambda x: x['Cash'] / x['Total Assets'] if x['Total Assets'] > 0 else 0, axis=1)
        df_p['Securities to Assets'] = df_p.apply(lambda x: x['Securities'] / x['Total Assets'] if x['Total Assets'] > 0 else 0, axis=1)
        return df_p
    except:
        if conn: conn.close()
        return pd.DataFrame()

@st.cache_data
def get_assets_averages(country_iso, region, systemic_importance, size_category=None):
    """Calculates Domestic, Regional, EU peer averages for Asset metrics based on Size logic."""
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    groups = get_benchmark_leis(country_iso, region, systemic_importance, size_category)
    
    all_results = []
    for label, leis in groups.items():
        if not leis: continue
        df_group = get_assets_kpis(leis)
        
        # --- NO OUTLIER REMOVAL ---
        df_filtered = df_group.copy()

        if df_filtered.empty: continue

        def weighted_avg(group):
            w = group['Total Assets']
            d = {}
            
            def get_w_avg(m_col):
                valid = group[[m_col, 'Total Assets']].dropna()
                if not valid.empty and valid['Total Assets'].sum() > 0:
                    return (valid[m_col] * valid['Total Assets']).sum() / valid['Total Assets'].sum()
                return group[m_col].mean()

            d['Loans to Assets'] = get_w_avg('Loans to Assets')
            d['Cash to Assets'] = get_w_avg('Cash to Assets')
            d['Securities to Assets'] = get_w_avg('Securities to Assets')
            
            # Means for amounts (ignoring nulls)
            for col in ['Cash', 'Loans and advances', 'Securities', 'Trading Assets', 'Other Assets', 'Total Assets', 'Debt Securities']:
                d[col] = group[col].mean()
            return pd.Series(d)

        df_avg = df_filtered.groupby('period').apply(weighted_avg, include_groups=False).reset_index().assign(name=label)
        all_results.append(df_avg)
    conn.close()
    return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
