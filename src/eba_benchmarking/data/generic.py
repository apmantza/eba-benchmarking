import pandas as pd
import sqlite3
import streamlit as st
import os
from ..config import DB_NAME
from .base import MIN_PERIOD

@st.cache_data
def get_tab_data(tab_name, lei_list):
    """
    Fetches all data for a specific tab across all facts tables.
    Optimized to minimize SQL queries (one per fact table instead of one per template).
    """
    if not lei_list or not os.path.exists(DB_NAME):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_NAME)
    
    # 1. Fetch Dictionary for the Tab
    try:
        df_dict = pd.read_sql(f"SELECT item_id, label, category, template FROM dictionary WHERE tab_name = '{tab_name}'", conn)
    except Exception:
        conn.close()
        return pd.DataFrame()

    if df_dict.empty:
        conn.close()
        return pd.DataFrame()

    # 2. Map Templates to Tables
    template_to_table = {
        'Capital': 'facts_oth', 
        'P&L': 'facts_oth', 
        'Leverage': 'facts_oth', 
        'RWA OV1': 'facts_oth', 
        'Assets': 'facts_oth', 
        'Liabilities': 'facts_oth', 
        'Credit Risk_STA_a': 'facts_cre', 
        'Credit Risk_STA_b': 'facts_cre', 
        'Credit Risk_IRB_a': 'facts_cre', 
        'Credit Risk_IRB_b': 'facts_cre', 
        'NPE': 'facts_cre', 
        'Forborne exposures': 'facts_cre', 
        'Market Risk': 'facts_mrk', 
        'Sovereign': 'facts_sov', 
        'NACE': 'facts_cre', 
        'Collateral': 'facts_cre'
    }

    # 3. Group Items by Target Table
    table_items_map = {}
    for template in df_dict['template'].unique():
        target_table = template_to_table.get(template)
        if not target_table:
            continue
        
        items = df_dict[df_dict['template'] == template]['item_id'].unique().tolist()
        if target_table not in table_items_map:
            table_items_map[target_table] = []
        table_items_map[target_table].extend(items)

    # 4. Execute Queries (One per Table)
    all_data = []
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"

    for table, items in table_items_map.items():
        if not items:
            continue
            
        # Deduplicate items
        items = list(set(items))
        items_str = "'" + "','".join([str(i) for i in items]) + "'"
        
        query = f"""
        SELECT 
            f.lei, 
            i.commercial_name as name, 
            f.period, 
            f.item_id, 
            f.amount 
        FROM {table} f 
        JOIN institutions i ON f.lei = i.lei 
        WHERE f.lei IN ({leis_str}) 
          AND f.item_id IN ({items_str}) 
          AND f.period >= '{MIN_PERIOD}'
        """
        try:
            df_temp = pd.read_sql(query, conn)
            if not df_temp.empty:
                all_data.append(df_temp)
        except Exception as e:
            # Table might not exist yet or other DB error
            print(f"Error querying {table}: {e}")
            pass

    conn.close()

    if not all_data:
        return pd.DataFrame()

    # 5. Merge and Format
    df_final = pd.concat(all_data, ignore_index=True)
    df_final['item_id'] = df_final['item_id'].astype(str)
    df_dict['item_id'] = df_dict['item_id'].astype(str)
    
    return pd.merge(df_final, df_dict, on='item_id', how='left')

@st.cache_data
def get_financial_data(lei_list):
    """Legacy helper for standard KPIs across OTH and CRE."""
    if not lei_list or not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    sql_oth = f"""
    SELECT f.lei, i.commercial_name as name, f.period, CASE 
        WHEN f.item_id = '2520140' THEN 'CET1 Ratio' WHEN f.item_id = '2520141' THEN 'Tier 1 Ratio' WHEN f.item_id = '2520142' THEN 'Total Capital Ratio' WHEN f.item_id = '2520905' THEN 'Leverage Ratio'
        WHEN f.item_id = '2520129' THEN 'AT1 Capital' WHEN f.item_id = '2520135' THEN 'Tier 2 Capital' WHEN f.item_id = '2520138' THEN 'Total Risk Exposure Amount (Cap)'
        WHEN f.item_id = '2520316' THEN 'Total Operating Income' WHEN f.item_id = '2520317' THEN 'Admin Expenses' WHEN f.item_id = '2520318' THEN 'Depreciation' WHEN f.item_id = '2520309' THEN 'Net Fee Income'
        WHEN f.item_id = '2520301' THEN 'Interest Income' WHEN f.item_id = '2520302' THEN 'Int Inc: Debt Securities' WHEN f.item_id = '2520303' THEN 'Int Inc: Loans'
        WHEN f.item_id = '2520304' THEN 'Interest Expenses' WHEN f.item_id = '2520305' THEN 'Int Exp: Deposits' WHEN f.item_id = '2520306' THEN 'Int Exp: Debt Securities'
        WHEN f.item_id = '2520201' THEN 'RWA: Credit Risk' WHEN f.item_id = '2520220' THEN 'Total Risk Exposure Amount' ELSE 'Other'
    END as kpi, f.amount FROM facts_oth f JOIN institutions i ON f.lei = i.lei WHERE f.lei IN ({leis_str}) AND f.period >= '{MIN_PERIOD}'
    """
    try:
        df_oth = pd.read_sql(sql_oth, conn)
        sql_cre = f"SELECT f.lei, f.period, SUM(amount) as total_loans, SUM(CASE WHEN perf_status = 2 THEN amount ELSE 0 END) as npl_amt FROM facts_cre f WHERE f.lei IN ({leis_str}) AND f.item_id = '2520605' AND f.period >= '{MIN_PERIOD}' GROUP BY f.lei, f.period"
        df_cre = pd.read_sql(sql_cre, conn); conn.close()
        df_oth_p = df_oth.pivot_table(index=['lei', 'name', 'period'], columns='kpi', values='amount', aggfunc='sum').reset_index() if not df_oth.empty else pd.DataFrame(columns=['lei', 'name', 'period'])
        df_final = pd.merge(df_oth_p, df_cre, on=['lei', 'period'], how='left') if not df_cre.empty else df_oth_p
        if 'npl_amt' in df_final.columns: df_final['npl_ratio'] = df_final['npl_amt'] / df_final['total_loans']
        return df_final
    except:
        if conn: conn.close()
        return pd.DataFrame()