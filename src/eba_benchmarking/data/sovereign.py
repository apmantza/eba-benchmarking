import pandas as pd
import sqlite3
import streamlit as st
import os
from ..config import DB_NAME
from .base import MIN_PERIOD, get_benchmark_leis

@st.cache_data
def get_sovereign_kpis(lei_list):
    """Fetches sovereign exposures by portfolio, country, and maturity."""
    if not lei_list or not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    port_map = {'2520812': 'Held for trading', '2520813': 'Designated at FV', '2520814': 'FVOCI', '2520815': 'Amortised Cost'}
    items_str = "'" + "','".join(port_map.keys()) + "'"
    mat_map = {1: 0.125, 2: 0.625, 3: 1.5, 4: 2.5, 5: 4.0, 6: 7.5, 7: 15.0}
    query = f"""
    SELECT f.lei, i.commercial_name as name, f.period, f.item_id, f.country as country_id, c.label as country_name, c.iso_code as country_iso, i.country_iso as bank_country_iso, f.maturity as maturity_id, m.label as maturity_label, f.amount
    FROM facts_sov f JOIN institutions i ON f.lei = i.lei LEFT JOIN dim_country c ON f.country = c.country LEFT JOIN dim_maturity m ON f.maturity = m.maturity
    WHERE f.lei IN ({leis_str}) AND f.item_id IN ({items_str}) AND f.period >= '{MIN_PERIOD}' AND f.country != 0 AND f.maturity != 8
    """
    try:
        df = pd.read_sql(query, conn)
        df_cet1 = pd.read_sql(f"SELECT lei, period, amount as cet1 FROM facts_oth WHERE lei IN ({leis_str}) AND item_id = '2520102' AND period >= '{MIN_PERIOD}'", conn)
        conn.close()
        if df.empty: return pd.DataFrame()
        df['portfolio'] = df['item_id'].map(port_map)
        df['maturity_years'] = df['maturity_id'].map(mat_map)
        return pd.merge(df, df_cet1, on=['lei', 'period'], how='left') if not df_cet1.empty else df.assign(cet1=0)
    except Exception as e:
        if conn: conn.close()
        return pd.DataFrame()

@st.cache_data
def get_sovereign_averages(country_iso, region, systemic_importance):
    """Calculates Domestic, Regional, EU averages for Sovereign metrics."""
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    
    groups = get_benchmark_leis(country_iso, region, systemic_importance)
    port_map = {'2520812': 'Held for trading', '2520813': 'Designated at FV', '2520814': 'FVOCI', '2520815': 'Amortised Cost'}
    items_str = "'2520812','2520813','2520814','2520815'"
    mat_map = {1: 0.125, 2: 0.625, 3: 1.5, 4: 2.5, 5: 4.0, 6: 7.5, 7: 15.0}
    all_results = []
    for label, leis in groups.items():
        if not leis: continue
        leis_sql = "'" + "','".join([str(l) for l in leis]) + "'"
        df = pd.read_sql(f"SELECT lei, period, item_id, maturity, country as country_id, amount FROM facts_sov WHERE lei IN ({leis_sql}) AND item_id IN ({items_str}) AND period >= '{MIN_PERIOD}' AND country != 0 AND maturity != 8", conn)
        if df.empty: continue
        df['portfolio'] = df['item_id'].map(port_map); df['maturity_years'] = df['maturity'].map(mat_map)
        df_avg_port = df.groupby(['lei', 'period', 'portfolio'])['amount'].sum().reset_index().groupby(['period', 'portfolio'])['amount'].mean().reset_index()
        df_mat = df.groupby(['period']).apply(lambda x: (x['maturity_years'] * x['amount']).sum() / x['amount'].sum() if x['amount'].sum() > 0 else 0, include_groups=False).reset_index()
        df_mat.columns = ['period', 'mean_maturity']
        df_conc_raw = df.groupby(['lei', 'period', 'country_id']).agg({'amount': 'sum'}).reset_index()
        df_cet1_grp = pd.read_sql(f"SELECT lei, period, amount as cet1 FROM facts_oth WHERE lei IN ({leis_sql}) AND item_id = '2520102' AND period >= '{MIN_PERIOD}'", conn)
        df_conc = pd.merge(df_conc_raw, df_cet1_grp, on=['lei', 'period'])
        df_bank_max = df_conc.groupby(['lei', 'period']).apply(lambda x: x['amount'].max() / x['cet1'].iloc[0] if x['cet1'].iloc[0] > 0 else 0, include_groups=False).reset_index()
        df_bank_max.columns = ['lei', 'period', 'conc_ratio']
        df_avg_conc = df_bank_max.groupby('period')['conc_ratio'].mean().reset_index().rename(columns={'conc_ratio': 'concentration_ratio'})
        
        # Home Bias (Exp to Home Country / CET1)
        # We need Home Country for each LEI
        df_home_map = pd.read_sql(f"SELECT lei, country_iso as home_iso FROM institutions WHERE lei IN ({leis_sql})", conn)
        df_exp_home = pd.read_sql(f"SELECT f.lei, f.period, c.iso_code as exp_iso, f.amount FROM facts_sov f LEFT JOIN dim_country c ON f.country = c.country WHERE f.lei IN ({leis_sql}) AND f.item_id IN ({items_str}) AND f.period >= '{MIN_PERIOD}'", conn)
        df_exp_home = pd.merge(df_exp_home, df_home_map, on='lei')
        df_exp_home = df_exp_home[df_exp_home['exp_iso'] == df_exp_home['home_iso']]
        df_home_sum = df_exp_home.groupby(['lei', 'period'])['amount'].sum().reset_index().rename(columns={'amount': 'home_exp'})
        df_home_r = pd.merge(df_home_sum, df_cet1_grp, on=['lei', 'period'], how='left') # Use left to keep banks with exposure
        # If no home exposure, it's 0 (fill later if needed, but merge handles intersection)
        if not df_home_r.empty:
            df_home_r['hb_ratio'] = df_home_r.apply(lambda x: x['home_exp'] / x['cet1'] if x['cet1'] > 0 else 0, axis=1)
            df_avg_hb = df_home_r.groupby('period')['hb_ratio'].mean().reset_index().rename(columns={'hb_ratio': 'home_bias_ratio'})
        else:
            df_avg_hb = pd.DataFrame(columns=['period', 'home_bias_ratio'])

        df_combined = pd.merge(pd.merge(pd.merge(df_avg_port, df_mat, on='period', how='left'), df_avg_conc, on='period', how='left'), df_avg_hb, on='period', how='left')
        df_combined['name'] = label; all_results.append(df_combined)
    conn.close()
    return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
