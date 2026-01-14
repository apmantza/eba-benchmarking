"""

Benchmarking Dashboard Data Module



Provides functions to calculate all benchmarking metrics and peer group comparisons

for the Benchmarking Dashboard tab.

"""



import pandas as pd

import numpy as np

import sqlite3

import streamlit as st

import os

from ..config import DB_NAME, PROFITABILITY_ITEMS, SOLVENCY_ITEMS

from .base import MIN_PERIOD, get_master_data





def percentileofscore(values, score):

    """

    Calculate the percentile rank of a score relative to a list of values.

    Equivalent to scipy.stats.percentileofscore with kind='rank'.

    """

    if len(values) == 0:

        return 0

    values = sorted(values)

    n = len(values)

    left = sum(1 for v in values if v < score)

    right = sum(1 for v in values if v <= score)

    return ((left + right) / 2) / n * 100







# =============================================================================

# PEER GROUP DEFINITIONS

# =============================================================================



@st.cache_data

def get_benchmarking_peer_groups(country_iso, region, systemic_importance, size_category=None):

    """

    Returns dict of peer group LEI lists based on size classification.

    

    Groups:

    - Domestic Avg: Same country banks (incl. Bank of Cyprus for GR)

    - Regional (Same Size): Same region, same size category

    - EU (Same Size): All EU banks with same size category

    - EU Large: All EU banks with Large + Huge size categories

    

    Excludes banks with no size_category data.

    """

    # Bank of Cyprus LEI (ATHEX-listed, treated as domestic for Greek banks)

    ATHEX_PEER_LEIS = ['635400L14KNHZXPUZM19']

    

    if not os.path.exists(DB_NAME):

        return {}

    

    conn = sqlite3.connect(DB_NAME)

    try:

        query = """

            SELECT lei, country_iso, region, Systemic_Importance, size_category

            FROM institutions

            WHERE size_category IS NOT NULL

        """

        df = pd.read_sql(query, conn)

    except:

        conn.close()

        return {}

    conn.close()

    

    if df.empty:

        return {}

    

    # Domestic: Same country OR Bank of Cyprus for Greek banks

    if country_iso == 'GR':

        dom = df[

            (df['country_iso'] == country_iso) | 

            (df['lei'].isin(ATHEX_PEER_LEIS))

        ]['lei'].tolist()

    else:

        dom = df[

            df['country_iso'] == country_iso

        ]['lei'].tolist()

    

    # Regional (Same Size): Same region, different country, same size

    if size_category:

        reg_same_size = df[

            (df['region'] == region) & 

            (df['country_iso'] != country_iso) &

            (df['size_category'] == size_category)

        ]['lei'].tolist()

    else:

        reg_same_size = []

    

    # EU (Same Size): All EU with same size category

    if size_category:

        eu_same_size = df[

            df['size_category'] == size_category

        ]['lei'].tolist()

    else:

        eu_same_size = []

    

    # EU Large: All Large + Huge banks

    eu_large = df[

        df['size_category'].isin(['Large (200-500bn)', 'Huge (>500bn)'])

    ]['lei'].tolist()

    

    return {

        "Domestic Avg": dom,

        "Regional (Same Size)": reg_same_size,

        "EU (Same Size)": eu_same_size,

        "EU Large": eu_large

    }





# =============================================================================

# METRICS CALCULATION

# =============================================================================



@st.cache_data

def get_all_benchmarking_metrics(lei_list):

    """

    Fetches and calculates ALL benchmarking metrics for a list of LEIs.

    Returns a DataFrame with one row per bank per period.

    """

    if not lei_list or not os.path.exists(DB_NAME):

        return pd.DataFrame()

    

    conn = sqlite3.connect(DB_NAME)

    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"

    

    # =================================================================

    # 1. PROFITABILITY & BALANCE SHEET DATA

    # =================================================================

    prof_items = list(PROFITABILITY_ITEMS.keys())

    prof_items_str = "'" + "','".join(prof_items) + "'"

    

    query_prof = f"""

    SELECT f.lei, i.commercial_name as name, f.period, f.item_id, SUM(f.amount) as amount

    FROM facts_oth f

    JOIN institutions i ON f.lei = i.lei

    WHERE f.lei IN ({leis_str}) 

      AND f.item_id IN ({prof_items_str})

      AND f.period >= '{MIN_PERIOD}'

    GROUP BY f.lei, i.commercial_name, f.period, f.item_id

    """

    

    try:

        df_prof = pd.read_sql(query_prof, conn)

    except:

        df_prof = pd.DataFrame()

    

    if df_prof.empty:

        conn.close()

        return pd.DataFrame()

    

    # Pivot profitability data

    df_prof_pivot = df_prof.pivot_table(

        index=['lei', 'name', 'period'],

        columns='item_id',

        values='amount',

        aggfunc='sum'

    ).reset_index()

    df_prof_pivot.rename(columns=PROFITABILITY_ITEMS, inplace=True)

    

    # Ensure all columns exist

    for col in PROFITABILITY_ITEMS.values():

        if col not in df_prof_pivot.columns:

            df_prof_pivot[col] = 0

    

    # =================================================================

    # 2. SOLVENCY DATA

    # =================================================================

    solv_items = list(SOLVENCY_ITEMS.keys())

    solv_items_str = "'" + "','".join(solv_items) + "'"

    

    query_solv = f"""

    SELECT f.lei, f.period, f.item_id, SUM(f.amount) as amount

    FROM facts_oth f

    WHERE f.lei IN ({leis_str}) 

      AND f.item_id IN ({solv_items_str})

      AND f.period >= '{MIN_PERIOD}'

    GROUP BY f.lei, f.period, f.item_id

    """

    

    try:

        df_solv = pd.read_sql(query_solv, conn)

    except:

        df_solv = pd.DataFrame()

    

    if not df_solv.empty:

        df_solv_pivot = df_solv.pivot_table(

            index=['lei', 'period'],

            columns='item_id',

            values='amount',

            aggfunc='sum'

        ).reset_index()

        df_solv_pivot.rename(columns=SOLVENCY_ITEMS, inplace=True)

        

        # Remove TREA from profitability if it exists (to avoid conflict, use solvency TREA)

        if 'TREA' in df_prof_pivot.columns:

            df_prof_pivot = df_prof_pivot.drop(columns=['TREA'])

        

        # Merge with profitability

        df = pd.merge(df_prof_pivot, df_solv_pivot, on=['lei', 'period'], how='left')

    else:

        df = df_prof_pivot.copy()

    

    # Ensure TREA and other solvency columns exist (critical for many calculations)

    if 'TREA' not in df.columns:

        df['TREA'] = 0

    else:

        df['TREA'] = df['TREA'].fillna(0)

    if 'CET1 Capital' not in df.columns:

        df['CET1 Capital'] = 0

    if 'AT1 Capital' not in df.columns:

        df['AT1 Capital'] = 0

    if 'Tier 2 Capital' not in df.columns:

        df['Tier 2 Capital'] = 0

    if 'CET1 Ratio' not in df.columns:

        df['CET1 Ratio'] = 0

    if 'Total Capital Ratio' not in df.columns:

        df['Total Capital Ratio'] = 0

    if 'Leverage Ratio' not in df.columns:

        df['Leverage Ratio'] = 0

    

    # =================================================================

    # 3. RWA COMPOSITION

    # =================================================================

    query_rwa = f"""

    SELECT f.lei, f.period, d.label, SUM(f.amount) as amount

    FROM facts_oth f

    JOIN dictionary d ON f.item_id = d.item_id

    WHERE f.lei IN ({leis_str})

      AND d.tab_name = 'RWA'

      AND f.period >= '{MIN_PERIOD}'

    GROUP BY f.lei, f.period, d.label

    """

    

    try:

        df_rwa = pd.read_sql(query_rwa, conn)

    except:

        df_rwa = pd.DataFrame()

    

    if not df_rwa.empty:

        # Pivot RWA data

        df_rwa_pivot = df_rwa.pivot_table(

            index=['lei', 'period'],

            columns='label',

            values='amount',

            aggfunc='sum'

        ).reset_index()

        

        # Merge with main df

        df = pd.merge(df, df_rwa_pivot, on=['lei', 'period'], how='left')

    

    # =================================================================

    # 4. CASH DATA (for Cash/Deposits ratio)

    # =================================================================

    query_cash = f"""

    SELECT lei, period, SUM(amount) as cash

    FROM facts_oth

    WHERE lei IN ({leis_str})

      AND item_id = '2521001'

      AND f.period >= '{MIN_PERIOD}'

    GROUP BY lei, period

    """

    

    try:

        df_cash = pd.read_sql(query_cash, conn)

        if not df_cash.empty:

            df = pd.merge(df, df_cash, on=['lei', 'period'], how='left')

    except:

        df['cash'] = 0

    

    # =================================================================

    # 5. CUSTOMER DEPOSITS

    # =================================================================

    query_deposits = f"""

    SELECT lei, period, SUM(amount) as customer_deposits

    FROM facts_oth

    WHERE lei IN ({leis_str})

      AND item_id = '2521215'

      AND financial_instruments = 30

      AND exposure IN (301, 401)

      AND period >= '{MIN_PERIOD}'

    GROUP BY lei, period

    """

    

    try:

        df_deposits = pd.read_sql(query_deposits, conn)

        if not df_deposits.empty:

            df = pd.merge(df, df_deposits, on=['lei', 'period'], how='left')

    except:

        df['customer_deposits'] = 0

    

    # =================================================================

    # 5. WHOLESALE FUNDING (Debt Securities Issued)

    # =================================================================

    query_wholesale = f"""

    SELECT lei, period, SUM(amount) as debt_securities_issued

    FROM facts_oth

    WHERE lei IN ({leis_str})

      AND item_id = '2521215'

      AND financial_instruments = 40

      AND period >= '{MIN_PERIOD}'

    GROUP BY lei, period

    """

    

    try:

        df_wholesale = pd.read_sql(query_wholesale, conn)

        if not df_wholesale.empty:

            df = pd.merge(df, df_wholesale, on=['lei', 'period'], how='left')

    except:

        df['debt_securities_issued'] = 0

    

    # =================================================================

    # 6. ASSET QUALITY (NPL Ratio & Coverage)

    # =================================================================

    # Note: perf_status is numeric: 1=Performing, 2=Non-Performing

    query_aq = f"""

    SELECT lei, period,

           SUM(CASE WHEN item_id='2520603' AND perf_status=1 THEN amount ELSE 0 END) as performing_loans,

           SUM(CASE WHEN item_id='2520603' AND perf_status=2 THEN amount ELSE 0 END) as npl_amount,

           SUM(CASE WHEN item_id='2520613' AND perf_status=2 THEN ABS(amount) ELSE 0 END) as npl_provisions,

           SUM(CASE WHEN item_id='2520613' THEN ABS(amount) ELSE 0 END) as total_provisions

    FROM facts_cre

    WHERE lei IN ({leis_str})

      AND item_id IN ('2520603', '2520613')

      AND period >= '{MIN_PERIOD}'

    GROUP BY lei, period

    """

    

    try:

        df_aq = pd.read_sql(query_aq, conn)

        if not df_aq.empty:

            df = pd.merge(df, df_aq, on=['lei', 'period'], how='left')

    except:

        df['performing_loans'] = 0

        df['npl_amount'] = 0

        df['npl_provisions'] = 0

        df['total_provisions'] = 0

    

    # =================================================================

    # 7. SOVEREIGN EXPOSURE

    # =================================================================

    # Total sovereign exposure (exclude maturity=8 aggregate bucket)

    query_sov = f"""

    SELECT f.lei, f.period, 

           SUM(f.amount) as total_sovereign,

           i.country_iso as bank_country

    FROM facts_sov f

    JOIN institutions i ON f.lei = i.lei

    WHERE f.lei IN ({leis_str})

      AND f.item_id IN ('2520812', '2520813', '2520814', '2520815')

      AND f.country != 0

      AND f.maturity != 8

      AND f.period >= '{MIN_PERIOD}'

    GROUP BY f.lei, f.period, i.country_iso

    """

    

    try:

        df_sov = pd.read_sql(query_sov, conn)

        if not df_sov.empty:

            df = pd.merge(df, df_sov, on=['lei', 'period'], how='left')

    except:

        df['total_sovereign'] = 0

        df['bank_country'] = ''

    

    # Home country sovereign exposure  

    # NOTE: Exclude maturity=8 (aggregate bucket) to avoid double counting

    query_sov_home = f"""

    SELECT f.lei, f.period, SUM(f.amount) as home_sovereign

    FROM facts_sov f

    JOIN institutions i ON f.lei = i.lei

    JOIN dim_country c ON f.country = c.country

    WHERE f.lei IN ({leis_str})

      AND f.item_id IN ('2520812', '2520813', '2520814', '2520815')

      AND c.iso_code = i.country_iso

      AND f.maturity != 8

      AND f.period >= '{MIN_PERIOD}'

    GROUP BY f.lei, f.period

    """

    

    try:

        df_sov_home = pd.read_sql(query_sov_home, conn)

        if not df_sov_home.empty:

            df = pd.merge(df, df_sov_home, on=['lei', 'period'], how='left')

    except:

        df['home_sovereign'] = 0

    

    conn.close()

    

    # =================================================================

    # CALCULATE DERIVED METRICS

    # =================================================================

    

    # Fill NaN values

    df = df.fillna(0)

    

    # Annualization factor

    df['month'] = df['period'].apply(lambda x: int(str(x).split('-')[1]) if isinstance(x, str) else 12)

    df['ann_factor'] = 12 / df['month']

    

    # --- P&L Metrics ---

    df['Int Inc / Assets'] = df.apply(

        lambda x: (x['Interest Income'] / x['Total Assets']) * x['ann_factor'] if x['Total Assets'] > 0 else 0, axis=1

    )

    

    df['Debt Sec Inc / Total Inc'] = df.apply(

        lambda x: x['Int Inc: Debt Securities'] / x['Total Operating Income'] if x['Total Operating Income'] > 0 else 0, axis=1

    )

    

    df['Int Exp / Assets'] = df.apply(

        lambda x: (x['Interest Expenses'] / x['Total Assets']) * x['ann_factor'] if x['Total Assets'] > 0 else 0, axis=1

    )

    

    df['NIM'] = df.apply(

        lambda x: ((x['Interest Income'] - x['Interest Expenses']) / x['Total Assets']) * x['ann_factor'] if x['Total Assets'] > 0 else 0, axis=1

    )

    

    df['Cost of Deposits'] = df.apply(

        lambda x: (x['Int Exp: Deposits'] / x['customer_deposits']) * x['ann_factor'] if x.get('customer_deposits', 0) > 0 else 0, axis=1

    )

    

    df['Cost of Wholesale'] = df.apply(

        lambda x: (x['Int Exp: Debt Securities'] / x['debt_securities_issued']) * x['ann_factor'] if x.get('debt_securities_issued', 0) > 0 else 0, axis=1

    )

    

    df['Funding Cost'] = df.apply(
        lambda x: (x['Interest Expenses'] / (x['Total Assets'] - x['Total Equity'])) * x['ann_factor'] if (x['Total Assets'] - x['Total Equity']) > 0 else 0,
        axis=1
    )

    

    df['Net Fee Inc / Total Inc'] = df.apply(

        lambda x: x['Net Fee & Commission Income'] / x['Total Operating Income'] if x['Total Operating Income'] > 0 else 0, axis=1

    )



    df['Net Fee Inc / Assets'] = df.apply(

        lambda x: (x['Net Fee & Commission Income'] / x['Total Assets']) * x['ann_factor'] if x['Total Assets'] > 0 else 0, axis=1

    )

    

    df['Gains / Losses'] = df['Trading Income'] + df['FX Income']

    

    df['Operating Expenses'] = df['Admin Expenses'] + df['Depreciation']

    

    df['Cost / Income'] = df.apply(

        lambda x: x['Operating Expenses'] / x['Total Operating Income'] if x['Total Operating Income'] > 0 else 0, axis=1

    )

    

    df['Admin / Total Exp'] = df.apply(

        lambda x: x['Admin Expenses'] / x['Operating Expenses'] if x['Operating Expenses'] > 0 else 0, axis=1

    )

    

    df['Depr / Total Exp'] = df.apply(

        lambda x: x['Depreciation'] / x['Operating Expenses'] if x['Operating Expenses'] > 0 else 0, axis=1

    )

    

    df['Cost of Risk'] = df.apply(

        lambda x: (x['Impairment Cost'] / x['Total Assets']) * x['ann_factor'] if x['Total Assets'] > 0 else 0, axis=1

    )

    

    df['RoA'] = df.apply(

        lambda x: (x['Net Profit'] / x['Total Assets']) * x['ann_factor'] if x['Total Assets'] > 0 else 0, axis=1

    )

    

    df['RoRWA'] = df.apply(

        lambda x: (x['Net Profit'] / x['TREA']) * x['ann_factor'] if x.get('TREA', 0) > 0 else 0, axis=1

    )

    

    df['RoE'] = df.apply(

        lambda x: (x['Net Profit'] / x['Total Equity']) * x['ann_factor'] if x['Total Equity'] > 0 else 0, axis=1

    )

    

    # --- Capital Metrics ---

    df['Tier 1 Ratio'] = df.apply(

        lambda x: (x.get('CET1 Capital', 0) + x.get('AT1 Capital', 0)) / x['TREA'] if x.get('TREA', 0) > 0 else 0, axis=1

    )

    

    df['RWA Density'] = df.apply(

        lambda x: x.get('TREA', 0) / x['Total Assets'] if x['Total Assets'] > 0 and x.get('TREA', 0) > 0 else 0, axis=1

    )

    

    # RWA composition ratios

    trea_col = 'TREA' if 'TREA' in df.columns else 'Total Risk exposure amount'

    

    # Map RWA component columns

    rwa_mappings = {

        'Credit RWA / Total': 'Credit risk (excluding CCR and Securitisations)',

        'Market RWA / Total': 'Position, foreign exchange and commodities risks (Market risk)',

        'Op RWA / Total': 'Operational risk',

        'IRB RWA / Total': ['Credit risk (excluding CCR and Securitisations): Of which the foundation IRB (FIRB) approach',

                           'Credit risk (excluding CCR and Securitisations): Of which the advanced IRB (AIRB) approach']

    }

    

    for ratio_name, source_cols in rwa_mappings.items():

        if isinstance(source_cols, list):

            # Sum multiple columns

            df[ratio_name] = 0

            for col in source_cols:

                if col in df.columns:

                    df[ratio_name] += df[col].fillna(0)

        else:

            if source_cols in df.columns:

                df[ratio_name] = df[source_cols].fillna(0)

            else:

                df[ratio_name] = 0

        

        # Convert to ratio

        df[ratio_name] = df.apply(

            lambda x: x[ratio_name] / x[trea_col] if x.get(trea_col, 0) > 0 else 0, axis=1

        )

    

    # --- Liquidity Metrics ---

    df['Cash / Deposits'] = df.apply(

        lambda x: x.get('cash', 0) / x.get('customer_deposits', 0) if x.get('customer_deposits', 0) > 0 else 0, axis=1

    )

    

    # --- Credit / Asset Quality Metrics ---

    df['NPE Ratio'] = df.apply(

        lambda x: x.get('npl_amount', 0) / (x.get('performing_loans', 0) + x.get('npl_amount', 0)) 

        if (x.get('performing_loans', 0) + x.get('npl_amount', 0)) > 0 else 0, axis=1

    )

    

    # NPL Coverage Ratio = NPL Provisions / NPL Amount

    df['NPL Coverage'] = df.apply(

        lambda x: x.get('npl_provisions', 0) / x.get('npl_amount', 0) 

        if x.get('npl_amount', 0) > 0 else 0, axis=1

    )

    

    # Total Coverage = Total Provisions / Total Gross Loans

    df['Total Coverage'] = df.apply(

        lambda x: x.get('total_provisions', 0) / (x.get('performing_loans', 0) + x.get('npl_amount', 0))

        if (x.get('performing_loans', 0) + x.get('npl_amount', 0)) > 0 else 0, axis=1

    )

    

    df['Sovereign / CET1'] = df.apply(

        lambda x: x.get('total_sovereign', 0) / x.get('CET1 Capital', 0) if x.get('CET1 Capital', 0) > 0 else 0, axis=1

    )

    

    df['Home Bias Ratio'] = df.apply(

        lambda x: x.get('home_sovereign', 0) / x.get('CET1 Capital', 0) if x.get('CET1 Capital', 0) > 0 else 0, axis=1

    )

    

    # =================================================================

    # MERGE ADDITIONAL METRICS FROM OTHER MODULES

    # =================================================================

    from .solvency import get_solvency_with_texas_ratio

    from .asset_quality import get_aq_breakdown

    from .assets import get_assets_kpis

    from .liabilities import get_liabilities_kpis, get_deposit_beta

    

    # 1. Solvency (Texas Ratio)

    df_texas = get_solvency_with_texas_ratio(lei_list)

    if not df_texas.empty and 'Texas Ratio' in df_texas.columns:

        df = pd.merge(df, df_texas[['lei', 'period', 'Texas Ratio']], on=['lei', 'period'], how='left')

    

    # 2. Asset Quality (Forborne Ratio)

    df_aq = get_aq_breakdown(lei_list)

    if not df_aq.empty and 'Forborne Ratio' in df_aq.columns:

        df = pd.merge(df, df_aq[['lei', 'period', 'Forborne Ratio']], on=['lei', 'period'], how='left')

        

    # 3. Balance Sheet (Loans/Assets, Sec/Assets, Cash/Assets)

    df_assets = get_assets_kpis(lei_list)

    if not df_assets.empty:

        cols_to_merge = ['lei', 'period', 'Loans to Assets', 'Securities to Assets', 'Cash to Assets']

        # Filter cols that actually exist

        cols_to_merge = [c for c in cols_to_merge if c in df_assets.columns or c in ['lei', 'period']]

        df = pd.merge(df, df_assets[cols_to_merge], on=['lei', 'period'], how='left')

        

    # 4. Funding / Liabilities

    df_liab = get_liabilities_kpis(lei_list)

    if not df_liab.empty:

        cols_to_merge = ['lei', 'period', 'Customer Deposit Ratio', 'Wholesale Funding Ratio']

        cols_to_merge = [c for c in cols_to_merge if c in df_liab.columns or c in ['lei', 'period']]

        df = pd.merge(df, df_liab[cols_to_merge], on=['lei', 'period'], how='left')

        

    # 5. Liquidity (LDR) - Use existing 'loans' and 'customer_deposits' if available, or fetch from liquidity

    from .liquidity import get_liquidity_kpis

    df_liq = get_liquidity_kpis(lei_list)

    if not df_liq.empty and 'LDR' in df_liq.columns:

         df = pd.merge(df, df_liq[['lei', 'period', 'LDR']], on=['lei', 'period'], how='left')

         

    # 6. Cumulative Deposit Beta

    df_beta = get_deposit_beta(lei_list)

    if not df_beta.empty and 'cumulative_beta' in df_beta.columns:

        # beta is usually calculated on period_m, but we have period. Merge on lei, period.

        # Check if beta has 'period'

        if 'period' in df_beta.columns:

            df = pd.merge(df, df_beta[['lei', 'period', 'cumulative_beta']], on=['lei', 'period'], how='left')

            df.rename(columns={'cumulative_beta': 'Cumulative Deposit Beta'}, inplace=True)



    return df





# =============================================================================

# BENCHMARKING REPORT

# =============================================================================



# Define metrics structure for the report

# Tuple format: (column_name, display_label, higher_is_better)

# higher_is_better: True = higher is better, False = lower is better, None = neutral

BENCHMARKING_METRICS = {
    '📈 Profitability': [
        ('NIM', 'Net Interest Margin', True),
        ('Int Inc / Assets', 'Interest Income / Assets', True),
        ('Int Exp / Assets', 'Interest Expense / Assets', False),
        ('Cost / Income', 'Cost / Income Ratio', False),
        ('Admin / Total Exp', 'Admin / Total Expenses', True),
        ('Cost of Risk', 'Cost of Risk', False),
        ('RoA', 'Return on Assets', True),
        ('RoE', 'Return on Equity', True),
        ('RoRWA', 'Return on RWA', True),
    ],
    '💰 Fee Business': [
        ('Net Fee Inc / Total Inc', 'Net Fees / Total Income', True),
        ('Net Fee Inc / Assets', 'Net Fees / Total Assets', True),
    ],
    '📉 Funding Costs': [
        ('Cost of Deposits', 'Cost of Deposits', False),
        ('Funding Cost', 'Funding Cost', False),
    ],
    '🏛️ Capital & Leverage': [
        ('CET1 Ratio', 'CET1 Ratio', True),
        ('Tier 1 Ratio', 'Tier 1 Ratio', True),
        ('Total Capital Ratio', 'Total Capital Ratio', True),
        ('Leverage Ratio', 'Leverage Ratio', True),
        ('RWA Density', 'RWA Density', True),
    ],
    '🛡️ Asset Quality': [
        ('NPE Ratio', 'NPE Ratio', False),
        ('NPL Coverage', 'NPL Coverage Ratio', True),
        ('Total Coverage', 'Total Coverage Ratio', True),
        ('Texas Ratio', 'Texas Ratio', False),
        ('Forborne Ratio', 'Forborne Ratio', False),
    ],
    '🌍 Concentration': [
        ('Sovereign / CET1', 'Sovereign Exposure / CET1', None),
        ('Home Bias Ratio', 'Home Sovereign / CET1', None),
    ],
    '📊 Balance Sheet Breakdown': [
        ('Loans to Assets', 'Loans / Total Assets', True),
        ('Securities to Assets', 'Securities / Total Assets', False),
        ('Cash to Assets', 'Cash / Total Assets', True),
    ],
    '💧 Funding & Liquidity': [
        ('LDR', 'Loan-to-Deposit Ratio', False),
        ('Customer Deposit Ratio', 'Customer Deposits / Total Liab', True),
        ('Wholesale Funding Ratio', 'Wholesale Funding / Total Liab', False),
    ]
}





def calculate_percentiles(base_value, peer_values, higher_is_better=True):

    """

    Calculate the base bank's percentile rank within the peer group.

    

    Interpretation:

    - 95th percentile = bank is better than 95% of peers (top performer)

    - 50th percentile = bank is at the median

    - 5th percentile = bank is worse than 95% of peers (bottom performer)

    

    For metrics where lower is better (e.g., NPE ratio, costs), the calculation

    is inverted so that a lower value still results in a higher percentile.

    

    Returns: percentile (0-100) where higher is always better

    """

    if len(peer_values) == 0 or pd.isna(base_value):

        return None

    

    # Remove NaN values

    peer_values = [v for v in peer_values if not pd.isna(v)]

    

    if len(peer_values) == 0:

        return None

    

    n = len(peer_values)

    

    if higher_is_better is True:

        # Higher value = better performance

        # Count how many peers the base bank beats (has higher value than)

        peers_beaten = sum(1 for v in peer_values if base_value > v)

    elif higher_is_better is False:

        # Lower value = better performance (e.g., NPE ratio, costs)

        # Count how many peers the base bank beats (has lower value than)

        peers_beaten = sum(1 for v in peer_values if base_value < v)

    else:

        # No direction specified (higher_is_better is None)

        # Just show raw position without inverting

        peers_beaten = sum(1 for v in peer_values if base_value > v)

    

    # Calculate percentile: what % of peers does the bank beat?

    # Add 0.5 to handle ties (bank ties with itself if included in peer group)

    percentile = (peers_beaten / n) * 100

    return round(percentile, 0)





@st.cache_data

def get_benchmarking_report(base_lei, country_iso, region, systemic_importance, size_category=None):

    """

    Generate the complete benchmarking report.

    

    Returns:

    - report_df: DataFrame with metrics, base value, peer averages, and percentiles

    - latest_period: The period used for the report

    """

    # Get peer groups with size-based filtering

    groups = get_benchmarking_peer_groups(country_iso, region, systemic_importance, size_category)

    

    # Get all LEIs (base + all peers)

    all_leis = set([base_lei])

    for leis in groups.values():

        all_leis.update(leis)

    

    # Fetch all metrics for all banks

    df_all = get_all_benchmarking_metrics(list(all_leis))

    

    if df_all.empty:

        return pd.DataFrame(), None

    

    # Get latest period

    latest_period = df_all['period'].max()

    df_latest = df_all[df_all['period'] == latest_period].copy()

    

    # Get base bank data

    df_base = df_latest[df_latest['lei'] == base_lei]

    if df_base.empty:

        return pd.DataFrame(), latest_period

    

    base_row = df_base.iloc[0]

    base_name = base_row.get('name', 'Base Bank')

    

    # Build report data

    report_data = []

    

    for section, metrics in BENCHMARKING_METRICS.items():

        # Add section header

        report_data.append({

            'Section': section,

            'Metric': f"**{section}**",

            'Base Value': None,

            'Domestic Avg': None, 'Dom Pctl': None,

            'Regional (Same Size)': None, 'Reg Pctl': None,

            'EU (Same Size)': None, 'EU Pctl': None,

            'EU Large': None, 'EU Large Pctl': None,

            'is_header': True

        })

        

        for col, label, higher_is_better in metrics:

            base_val = base_row.get(col, 0) if col in base_row.index else 0

            

            row_data = {

                'Section': section,

                'Metric': label,

                'Base Value': base_val,

                'is_header': False

            }

            

            # Calculate averages and percentiles for each peer group

            for group_name, group_leis in groups.items():

                if not group_leis:

                    row_data[group_name] = None

                    row_data[f'{group_name} Pctl'] = None

                    continue

                

                # Get peer data

                df_peers = df_latest[df_latest['lei'].isin(group_leis)]

                

                if df_peers.empty or col not in df_peers.columns:

                    row_data[group_name] = None

                    row_data[f'{group_name} Pctl'] = None

                    continue

                

                peer_values = df_peers[col].dropna().tolist()

                

                if not peer_values:

                    row_data[group_name] = None

                    row_data[f'{group_name} Pctl'] = None

                    continue

                

                # Weighted average (by Total Assets if available)

                if 'Total Assets' in df_peers.columns:

                    weights = df_peers['Total Assets'].fillna(1)

                    valid_mask = df_peers[col].notna()

                    if valid_mask.sum() > 0 and weights[valid_mask].sum() > 0:

                        avg_val = (df_peers.loc[valid_mask, col] * weights[valid_mask]).sum() / weights[valid_mask].sum()

                    else:

                        avg_val = np.mean(peer_values)

                else:

                    avg_val = np.mean(peer_values)

                

                # Calculate percentile (bank's rank position within peer group)

                percentile = calculate_percentiles(base_val, peer_values, higher_is_better)

                

                # Column prefix for percentile column

                pctl_prefix_map = {

                    'Domestic Avg': 'Dom',

                    'Regional (Same Size)': 'Reg',

                    'EU (Same Size)': 'EU',

                    'EU Large': 'EU Large'

                }

                col_prefix = pctl_prefix_map.get(group_name, group_name)

                

                row_data[group_name] = avg_val

                row_data[f'{col_prefix} Pctl'] = percentile

            

            report_data.append(row_data)

    

    report_df = pd.DataFrame(report_data)

    return report_df, latest_period, base_name






@st.cache_data
def get_underlying_bank_data(country_iso, region, systemic_importance, size_category=None):
    """
    Returns raw data for all banks in all peer groups for download.
    """
    groups = get_benchmarking_peer_groups(country_iso, region, systemic_importance, size_category)
    
    # Get all LEIs
    all_leis = set()
    for leis in groups.values():
        all_leis.update(leis)
    
    if not all_leis:
        return pd.DataFrame()
    
    # Fetch all metrics
    df = get_all_benchmarking_metrics(list(all_leis))
    
    if df.empty:
        return pd.DataFrame()
    
    # Get latest period only
    latest_period = df['period'].max()
    df = df[df['period'] == latest_period].copy()
    
    # Add peer group membership columns
    for group_name, group_leis in groups.items():
        df[f'In {group_name}'] = df['lei'].isin(group_leis)
    
    # Return ALL columns
    final_cols = ['lei', 'name', 'period']
    # Add peer group indicators
    for group_name in groups.keys():
        col_name = f'In {group_name}'
        if col_name in df.columns:
            final_cols.append(col_name)
            
    # Add remaining columns (all metrics + raw data)
    existing_cols = set(final_cols)
    for col in df.columns:
        if col not in existing_cols:
            final_cols.append(col)
            
    return df[final_cols]





def get_custom_metric_data(item_ids, item_labels, lei_list):
    """
    Fetches specific items (list) for a list of LEIs from facts_oth.
    Returns a DataFrame with aggregated amounts, pivoted by item label.
    """
    if not lei_list or not os.path.exists(DB_NAME):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    
    # Handle single item case (convert to list)
    if isinstance(item_ids, str):
        item_ids = [item_ids]
    if isinstance(item_labels, str):
        item_labels = [item_labels]
        
    item_ids_str = "'" + "','".join([str(itm) for itm in item_ids]) + "'"
    
    # Map item_id to label for easy renaming later
    id_to_label = dict(zip(item_ids, item_labels))
    
    # We aggregate (SUM) over all dimensions for simplicity in this explorer
    query = f"""
    SELECT f.lei, i.commercial_name as name, f.period, f.item_id, SUM(f.amount) as value
    FROM facts_oth f
    JOIN institutions i ON f.lei = i.lei
    WHERE f.lei IN ({leis_str})
      AND f.item_id IN ({item_ids_str})
      AND f.period >= '{MIN_PERIOD}'
    GROUP BY f.lei, i.commercial_name, f.period, f.item_id
    """
    
    try:
        df = pd.read_sql(query, conn)
    except:
        conn.close()
        return pd.DataFrame()
        
    if df.empty:
        conn.close()
        return pd.DataFrame()

    # Pivot to wide format: One column per item
    df_pivot = df.pivot_table(
        index=['lei', 'name', 'period'],
        columns='item_id',
        values='value',
        aggfunc='sum'
    ).reset_index()
    
    # Rename columns using provided labels
    df_pivot.rename(columns=id_to_label, inplace=True)
    
    # Ensure all requested columns exist (fill with 0 if missing)
    for lbl in item_labels:
        if lbl not in df_pivot.columns:
            df_pivot[lbl] = 0

    # Also fetch Total Assets for normalization
    query_assets = f"""
    SELECT lei, period, SUM(amount) as assets
    FROM facts_oth
    WHERE lei IN ({leis_str})
      AND item_id = '2521010'
      AND period >= '{MIN_PERIOD}'
    GROUP BY lei, period
    """
    try:
        df_assets = pd.read_sql(query_assets, conn)
        # Rename assets to prevent collision if 'Total Assets' is one of the selected items
        if 'assets' in df_pivot.columns:
            # This shouldn't happen unless user selected it, but just safely merge
            df_assets.rename(columns={'assets': '_total_assets_norm'}, inplace=True)
        else:
            df_assets.rename(columns={'assets': 'Total Assets (Normalization)'}, inplace=True)
            
        df_pivot = pd.merge(df_pivot, df_assets, on=['lei', 'period'], how='left')
    except:
        df_pivot['Total Assets (Normalization)'] = 1
        
    conn.close()
    return df_pivot




@st.cache_data
def get_available_metrics_for_explorer():
    """
    Returns a DataFrame of available metrics from dictionary for the explorer.
    """
    if not os.path.exists(DB_NAME):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT item_id, label, category 
    FROM dictionary 
    WHERE item_id IN (SELECT DISTINCT item_id FROM facts_oth)
    ORDER BY category, label
    """
    try:
        df = pd.read_sql(query, conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df
