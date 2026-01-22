import pandas as pd
import sqlite3
import streamlit as st
import os
from ..config import DB_NAME, SOLVENCY_ITEMS
from .base import MIN_PERIOD, get_benchmark_leis

@st.cache_data
def get_solvency_kpis(lei_list):
    """Fetches specific solvency items and calculates derived ratios including Texas Ratio and RWA Density."""
    if not lei_list or not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    
    items = list(SOLVENCY_ITEMS.keys())
    items_str = "'" + "','".join(items) + "'"
    
    query = f"""
    SELECT f.lei, COALESCE(i.short_name, i.commercial_name) as name, f.period, f.item_id, f.amount
    FROM facts_oth f JOIN institutions i ON f.lei = i.lei
    WHERE f.lei IN ({leis_str}) AND f.item_id IN ({items_str}) AND f.period >= '{MIN_PERIOD}'
    """
    try:
        df = pd.read_sql(query, conn)
        
        # Also fetch Total Assets for RWA Density
        query_assets = f"""
        SELECT f.lei, f.period, f.amount as total_assets
        FROM facts_oth f
        WHERE f.lei IN ({leis_str}) AND f.item_id = '2521010' AND f.period >= '{MIN_PERIOD}'
        """
        df_assets = pd.read_sql(query_assets, conn)
        conn.close()
        
        if df.empty: return pd.DataFrame()
        df_pivot = df.pivot_table(index=['lei', 'name', 'period'], columns='item_id', values='amount', aggfunc='sum').reset_index()
        
        df_pivot.rename(columns=SOLVENCY_ITEMS, inplace=True)
        for col in SOLVENCY_ITEMS.values():
            if col not in df_pivot.columns: df_pivot[col] = 0
        
        # Merge Total Assets
        if not df_assets.empty:
            df_pivot = pd.merge(df_pivot, df_assets, on=['lei', 'period'], how='left')
        else:
            df_pivot['total_assets'] = 0
            
        df_pivot['Total Capital'] = df_pivot['CET1 Capital'] + df_pivot['AT1 Capital'] + df_pivot['Tier 2 Capital']
        df_pivot['AT1 Ratio (calc)'] = df_pivot.apply(lambda x: x['AT1 Capital'] / x['TREA'] if x['TREA'] > 0 else 0, axis=1)
        df_pivot['Tier 2 Ratio (calc)'] = df_pivot.apply(lambda x: x['Tier 2 Capital'] / x['TREA'] if x['TREA'] > 0 else 0, axis=1)
        
        # RWA Density: TREA / Total Assets
        df_pivot['RWA Density'] = df_pivot.apply(
            lambda x: x['TREA'] / x['total_assets'] if x.get('total_assets', 0) > 0 else 0, axis=1
        )
        
        return df_pivot
    except:
        if conn: conn.close()
        return pd.DataFrame()

@st.cache_data  
def get_solvency_with_texas_ratio(lei_list):
    """Combines solvency KPIs with AQ data to calculate Texas Ratio."""
    from .asset_quality import get_aq_breakdown
    
    df_solv = get_solvency_kpis(lei_list)
    if df_solv.empty: return df_solv
    
    df_aq = get_aq_breakdown(lei_list)
    if df_aq.empty: return df_solv
    
    # Merge on lei and period
    df_merged = pd.merge(
        df_solv, 
        df_aq[['lei', 'period', 'NPL_Amount', 'Total_Provisions']], 
        on=['lei', 'period'], 
        how='left'
    )
    
    # Texas Ratio = NPLs / (CET1 Capital + Total Provisions)
    df_merged['Texas Ratio'] = df_merged.apply(
        lambda x: x['NPL_Amount'] / (x['CET1 Capital'] + x.get('Total_Provisions', 0)) 
        if (x['CET1 Capital'] + x.get('Total_Provisions', 0)) > 0 else 0, 
        axis=1
    )
    
    return df_merged

@st.cache_data
def get_solvency_averages(country_iso, region, systemic_importance, size_category=None):
    """Calculates Domestic, Regional, and EU Averages based on Size logic."""
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    groups = get_benchmark_leis(country_iso, region, systemic_importance, size_category)
    
    items = list(SOLVENCY_ITEMS.keys())

    def get_pivoted_data(lei_list, label):
        if not lei_list: return pd.DataFrame()
        leis_sql = "'" + "','".join([str(l) for l in lei_list]) + "'"
        
        # 1. Fetch Solvency Items + Total Assets
        items_with_assets = items + ['2521010']
        items_str_ext = "'" + "','".join(items_with_assets) + "'"
        query = f"SELECT lei, period, item_id, amount FROM facts_oth WHERE lei IN ({leis_sql}) AND item_id IN ({items_str_ext}) AND period >= '{MIN_PERIOD}'"
        df_raw = pd.read_sql(query, conn)
        
        if df_raw.empty: return pd.DataFrame()
        
        df_banks = df_raw.pivot_table(index=['lei', 'period'], columns='item_id', values='amount', aggfunc='sum').reset_index()
        
        # Mapping for readability
        cols_map = {**SOLVENCY_ITEMS, '2521010': 'total_assets'}
        df_banks.rename(columns=cols_map, inplace=True)
        
        # 2. Fetch NPL & Provisions for Texas Ratio
        # NPL Amount: 2520603 (Gross Loans) with status 2 (Non-performing)
        # Provisions: 2520613 (Total Provisions) - sum of all statuses
        query_aq = f"""
        SELECT lei, period, 
               SUM(CASE WHEN item_id='2520603' AND perf_status='2' THEN amount ELSE 0 END) as NPL_Amount,
               SUM(CASE WHEN item_id='2520613' THEN amount ELSE 0 END) as Total_Provisions
        FROM facts_cre 
        WHERE lei IN ({leis_sql}) 
          AND item_id IN ('2520603', '2520613')
          AND period >= '{MIN_PERIOD}'
        GROUP BY lei, period
        """
        df_aq = pd.read_sql(query_aq, conn)
        
        if not df_aq.empty:
            df_banks = pd.merge(df_banks, df_aq, on=['lei', 'period'], how='left')
            df_banks['NPL_Amount'] = df_banks['NPL_Amount'].fillna(0)
            df_banks['Total_Provisions'] = df_banks['Total_Provisions'].fillna(0)
        else:
            df_banks['NPL_Amount'] = 0
            df_banks['Total_Provisions'] = 0

        # --- WEIGHTED AVERAGES ---
        def weighted_avg(group):
            d = {}
            # We must handle NaNs: only average over banks that have the data
            def get_w_avg(metric_col, weight_col):
                if metric_col not in group.columns or weight_col not in group.columns: return 0
                valid = group[[metric_col, weight_col]].dropna()
                if not valid.empty and valid[weight_col].sum() > 0:
                    return (valid[metric_col] * valid[weight_col]).sum() / valid[weight_col].sum()
                return group[metric_col].mean() # Fallback

            d['CET1 Ratio'] = get_w_avg('CET1 Ratio', 'TREA')
            d['Total Capital Ratio'] = get_w_avg('Total Capital Ratio', 'TREA')
            d['Leverage Ratio'] = get_w_avg('Leverage Ratio', 'TREA')
            
            # AT1/T2 Ratios
            if 'AT1 Capital' in group.columns and 'TREA' in group.columns:
                group['AT1_R'] = group['AT1 Capital'] / group['TREA']
                d['AT1 Ratio (calc)'] = get_w_avg('AT1_R', 'TREA')
            
            if 'Tier 2 Capital' in group.columns and 'TREA' in group.columns:
                group['T2_R'] = group['Tier 2 Capital'] / group['TREA']
                d['Tier 2 Ratio (calc)'] = get_w_avg('T2_R', 'TREA')
            
            # RWA Density: TREA / Total Assets
            if 'TREA' in group.columns and 'total_assets' in group.columns:
                group['RWA_Den'] = group['TREA'] / group['total_assets']
                d['RWA Density'] = get_w_avg('RWA_Den', 'total_assets')

            # Absolute Amounts (Mean of reporting banks)
            for col in ['CET1 Capital', 'AT1 Capital', 'Tier 2 Capital', 'TREA', 'total_assets', 'NPL_Amount', 'Total_Provisions']:
                if col in group.columns:
                    d[col] = group[col].mean()
            
            d['Total Capital'] = sum([d.get(c, 0) for c in ['CET1 Capital', 'AT1 Capital', 'Tier 2 Capital'] if pd.notna(d.get(c))])
            
            # Texas Ratio (Weighted for Group): Sum(NPL) / Sum(CET1 + Prov)
            if 'NPL_Amount' in group.columns and 'CET1 Capital' in group.columns and 'Total_Provisions' in group.columns:
                valid_tx = group[(group['CET1 Capital'].notnull()) | (group['Total_Provisions'].notnull())]
                agg_npl = valid_tx['NPL_Amount'].sum()
                agg_cap = valid_tx['CET1 Capital'].sum()
                agg_prov = valid_tx['Total_Provisions'].sum()
                if (agg_cap + agg_prov) > 0:
                    d['Texas Ratio'] = agg_npl / (agg_cap + agg_prov)
                else:
                    d['Texas Ratio'] = 0

            return pd.Series(d)
        
        df_f = df_banks.groupby('period').apply(weighted_avg, include_groups=False).reset_index()
        df_f['name'] = label
        return df_f

    dfs = []
    for lbl, leis in groups.items():
        dfs.append(get_pivoted_data(leis, lbl))
    
    conn.close()
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

@st.cache_data
def get_regional_peers_raw_data(region, systemic_importance, exclude_country=None, size_category=None):
    """Fetches raw solvency data for Regional peers (Size-based)."""
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    # Base query
    query = "SELECT lei FROM institutions WHERE region = ? AND country_iso != ?"
    params = [region, exclude_country or '']
    
    if size_category:
        query += " AND size_category = ?"
        params.append(size_category)
    
    leis = pd.read_sql(query, conn, params=params)['lei'].tolist()
    conn.close()
    return get_solvency_kpis(leis) if leis else pd.DataFrame()

@st.cache_data
def get_rwa_composition_averages(country_iso, region, systemic_importance, size_category=None):
    """
    Calculates Domestic, Regional, EU peer averages for RWA composition.
    """
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    # Get peer groups
    groups = get_benchmark_leis(country_iso, region, systemic_importance, size_category)
    
    # Get RWA items from dictionary
    df_dict = pd.read_sql("SELECT item_id, label FROM dictionary WHERE tab_name = 'RWA'", conn)
    if df_dict.empty:
        conn.close()
        return pd.DataFrame()
    
    items_str = "'" + "','".join(df_dict['item_id'].tolist()) + "'"
    
    all_results = []
    for label, leis in groups.items():
        if not leis: continue
        leis_str = "'" + "','".join([str(l) for l in leis]) + "'"
        
        query = f"""
        SELECT f.period, f.item_id, AVG(f.amount) as amount
        FROM facts_oth f
        WHERE f.lei IN ({leis_str}) 
          AND f.item_id IN ({items_str})
          AND f.period >= '{MIN_PERIOD}'
        GROUP BY f.period, f.item_id
        """
        df_group = pd.read_sql(query, conn)
        if df_group.empty: continue
        
        # Merge with labels
        df_group = pd.merge(df_group, df_dict, on='item_id', how='left')
        df_group['name'] = label
        all_results.append(df_group)
    
    conn.close()
    return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()

@st.cache_data
def get_rwa_composition(lei_list):
    """
    Fetches RWA breakdown data for selected banks.
    Adapted from get_rwa_composition_averages logic (querying facts_oth).
    """
    if not lei_list or not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    # Get RWA items
    df_dict = pd.read_sql("SELECT item_id, label FROM dictionary WHERE tab_name = 'RWA'", conn)
    if df_dict.empty:
        conn.close()
        return pd.DataFrame()
    
    items_str = "'" + "','".join(df_dict['item_id'].tolist()) + "'"
    leis_str = "'" + "','".join([str(l) for l in lei_list]) + "'"
    
    # Query facts_oth (where RWA summary data lives)
    query = f"""
    SELECT f.lei, COALESCE(i.short_name, i.commercial_name) as name, f.period, f.item_id, f.amount
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
        
        # Merge with labels
        df_dict['item_id'] = df_dict['item_id'].astype(str)
        df['item_id'] = df['item_id'].astype(str)
        return pd.merge(df, df_dict, on='item_id', how='left')
    except:
        if conn: conn.close()
        return pd.DataFrame()
