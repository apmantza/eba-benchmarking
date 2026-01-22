import pandas as pd
import sqlite3
import streamlit as st
import os
from ..config import DB_NAME
from .base import MIN_PERIOD, get_benchmark_leis
from .solvency import get_solvency_kpis

@st.cache_data
def get_aq_breakdown(lei_list):
    """Calculates granular AQ breakdown including Stage ratios, Coverage, Forborne, Write-offs, and Texas Ratio."""
    if not lei_list or not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    
    # Main query: NPE items (2520603=Exp, 2520613=Prov) + Forborne (2520703, 2520713) + Write-offs (2521708)
    query = f"""
    SELECT f.lei, COALESCE(i.short_name, i.commercial_name) as name, f.period, f.item_id, f.perf_status, SUM(f.amount) as amount
    FROM facts_cre f JOIN institutions i ON f.lei = i.lei
    WHERE f.lei IN ({leis_str}) 
      AND f.item_id IN ('2520603', '2520613', '2520703', '2520713', '2521708') 
      AND f.period >= '{MIN_PERIOD}'
    GROUP BY f.lei, f.period, f.item_id, f.perf_status
    """
    try:
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return pd.DataFrame()

        # Separate main NPE data from forborne and write-offs
        df_npe = df[df['item_id'].isin(['2520603', '2520613'])].copy()
        df_forborne = df[df['item_id'].isin(['2520703', '2520713'])].copy()
        df_writeoff = df[df['item_id'] == '2521708'].copy()
        
        # --- MAIN NPE PIVOT ---
        df_npe['type'] = df_npe['item_id'].map({'2520603': 'Exp', '2520613': 'Prov'})
        df_p = df_npe.pivot_table(index=['lei', 'name', 'period'], 
                              columns=['type', 'perf_status'], 
                              values='amount', aggfunc='sum').fillna(0)
        df_p.columns = [f"{t}_{s}" for t, s in df_p.columns]
        
        # --- FORBORNE PIVOT ---
        if not df_forborne.empty:
            df_forborne['type'] = df_forborne['item_id'].map({'2520703': 'Forb_Exp', '2520713': 'Forb_Prov'})
            df_fb = df_forborne.pivot_table(index=['lei', 'name', 'period'],
                                           columns=['type', 'perf_status'],
                                           values='amount', aggfunc='sum').fillna(0)
            df_fb.columns = [f"{t}_{s}" for t, s in df_fb.columns]
            df_p = df_p.join(df_fb, how='left')
        
        # --- WRITE-OFF PIVOT ---
        if not df_writeoff.empty:
            df_wo = df_writeoff.pivot_table(index=['lei', 'name', 'period'],
                                           columns='perf_status',
                                           values='amount', aggfunc='sum').fillna(0)
            df_wo.columns = [f"WriteOff_{s}" for s in df_wo.columns]
            df_p = df_p.join(df_wo, how='left')
        
        df_p = df_p.fillna(0)
        
        # --- CALCULATE RATIOS ---
        
        # Stage 3 Coverage: Prov_23 / Exp_23
        df_p['Stage 3 Coverage'] = df_p.apply(lambda x: x.get('Prov_23', 0) / x.get('Exp_23', 0) if x.get('Exp_23', 0) > 0 else 0, axis=1)
        
        # Stage 2 Coverage: Prov_12 / Exp_12
        df_p['Stage 2 Coverage'] = df_p.apply(lambda x: x.get('Prov_12', 0) / x.get('Exp_12', 0) if x.get('Exp_12', 0) > 0 else 0, axis=1)

        # Stage 2 Ratio: Exp_12 / Exp_1
        df_p['Stage 2 Ratio'] = df_p.apply(lambda x: x.get('Exp_12', 0) / x.get('Exp_1', 0) if x.get('Exp_1', 0) > 0 else 0, axis=1)

        # NPL Ratio: Exp_2 / (Exp_1 + Exp_2)
        df_p['npl_ratio'] = df_p.apply(lambda x: x.get('Exp_2', 0) / (x.get('Exp_1', 0) + x.get('Exp_2', 0)) if (x.get('Exp_1', 0) + x.get('Exp_2', 0)) > 0 else 0, axis=1)
        
        # Total Performing Loans (for Forborne Ratio denominator)
        df_p['Total_Loans'] = df_p.apply(lambda x: x.get('Exp_1', 0) + x.get('Exp_2', 0), axis=1)
        
        # Total NPL Amount (for Texas Ratio and Write-off Rate)
        df_p['NPL_Amount'] = df_p.apply(lambda x: x.get('Exp_2', 0), axis=1)
        
        # Total Provisions
        df_p['Total_Provisions'] = df_p.apply(lambda x: x.get('Prov_1', 0) + x.get('Prov_2', 0) + x.get('Prov_12', 0), axis=1)
        
        # Forborne Ratio: Total Forborne Exp (perf_status 0 or 1+2) / Total Loans
        forb_cols = [c for c in df_p.columns if c.startswith('Forb_Exp_')]
        if forb_cols:
            df_p['Forborne_Total'] = df_p[forb_cols].sum(axis=1)
            df_p['Forborne Ratio'] = df_p.apply(lambda x: x['Forborne_Total'] / x['Total_Loans'] if x['Total_Loans'] > 0 else 0, axis=1)
        else:
            df_p['Forborne Ratio'] = 0
        
        # Write-off Rate: Accumulated Write-offs / NPL Amount
        wo_cols = [c for c in df_p.columns if c.startswith('WriteOff_')]
        if wo_cols:
            df_p['WriteOff_Total'] = df_p[wo_cols].sum(axis=1).abs()  # Write-offs are negative
            df_p['Write-off Rate'] = df_p.apply(lambda x: x['WriteOff_Total'] / x['NPL_Amount'] if x['NPL_Amount'] > 0 else 0, axis=1)
        else:
            df_p['Write-off Rate'] = 0

        return df_p.reset_index()
        

    except Exception as e:
        if conn: conn.close()
        return pd.DataFrame()

@st.cache_data
def get_asset_quality_averages(country_iso, region, systemic_importance, size_category=None):
    """Calculates Domestic, Regional, EU peer averages for NPL Ratio based on Size logic."""
    from .generic import get_financial_data
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    groups = get_benchmark_leis(country_iso, region, systemic_importance, size_category)
    
    all_results = []
    for label, leis in groups.items():
        if not leis: continue
        df_group_raw = get_financial_data(leis)
        if df_group_raw.empty: continue
        df_group_raw.rename(columns={'Total Risk Exposure Amount (Cap)': 'TREA'}, inplace=True)
        
        # --- NO OUTLIER REMOVAL ---
        df_filtered = df_group_raw.copy()
        
        def aq_weighted(group):
            valid = group[['npl_ratio', 'TREA']].dropna()
            if not valid.empty and valid['TREA'].sum() > 0:
                return (valid['npl_ratio'] * valid['TREA']).sum() / valid['TREA'].sum()
            return group['npl_ratio'].mean()
        
        df_avg = df_filtered.groupby('period').apply(aq_weighted, include_groups=False).reset_index()
        df_avg.columns = ['period', 'npl_ratio']
        df_avg['name'] = label
        all_results.append(df_avg)
    conn.close()
    return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()

@st.cache_data
def get_aq_breakdown_averages(country_iso, region, systemic_importance, size_category=None):
    """Calculates Domestic, Regional, EU peer averages based on Size logic."""
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    # Get bank groups
    groups = get_benchmark_leis(country_iso, region, systemic_importance, size_category)
    
    conn.close()
    
    all_results = []
    for label, leis in groups.items():
        if not leis: continue
        
        # Get AQ breakdown for all banks in group
        df_group = get_aq_breakdown(leis)
        if df_group.empty: continue
        
        # Calculate weighted averages by period
        # Weight by total exposure (Exp_1 + Exp_2) - i.e., total loan book
        def weighted_avg(group):
            d = {}
            
            # Calculate weight (total exposure)
            if 'Exp_1' not in group.columns:
                group['Exp_1'] = 0
            if 'Exp_2' not in group.columns:
                group['Exp_2'] = 0
            group['weight'] = group['Exp_1'] + group['Exp_2']
            
            def get_w_avg(col):
                valid = group[[col, 'weight']].dropna()
                if not valid.empty and valid['weight'].sum() > 0:
                    return (valid[col] * valid['weight']).sum() / valid['weight'].sum()
                return group[col].mean() if col in group.columns else 0
            
            # Stage 2 Ratio
            if 'Stage 2 Ratio' in group.columns:
                d['Stage 2 Ratio'] = get_w_avg('Stage 2 Ratio')
            
            # Stage 3 Coverage
            if 'Stage 3 Coverage' in group.columns:
                d['Stage 3 Coverage'] = get_w_avg('Stage 3 Coverage')
            
            # Stage 2 Coverage
            if 'Stage 2 Coverage' in group.columns:
                d['Stage 2 Coverage'] = get_w_avg('Stage 2 Coverage')
            
            # Forborne Ratio
            if 'Forborne Ratio' in group.columns:
                d['Forborne Ratio'] = get_w_avg('Forborne Ratio')
            
            # Write-off Rate
            if 'Write-off Rate' in group.columns:
                d['Write-off Rate'] = get_w_avg('Write-off Rate')
            
            return pd.Series(d)
        
        df_avg = df_group.groupby('period').apply(weighted_avg, include_groups=False).reset_index()
        df_avg['name'] = label
        all_results.append(df_avg)
    
    return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
