import streamlit as st
import pandas as pd

from eba_benchmarking.data import (
    get_solvency_kpis, get_solvency_averages,
    get_financial_data, get_asset_quality_averages,
    get_aq_breakdown, get_aq_breakdown_averages,
    get_profitability_kpis, get_profitability_averages,
    get_nii_analysis, get_nii_averages,
    get_sovereign_kpis, get_sovereign_averages
)


def render_overview_tab(base_lei, base_bank_name, base_country, base_size, df_std=None, base_region=None, base_sys=None):
    """
    Renders the Bank Overview tab with executive summary.
    """
    st.subheader(f"Executive Summary: {base_bank_name}")


    
    # 1. Fetch Latest Metrics for Base Bank
    # Solvency
    df_s = get_solvency_kpis([base_lei])
    # Asset Quality (using financial data for NPL ratio for now, or specific module)
    df_aq = get_financial_data([base_lei])
    # Asset Quality Breakdown (for Stage 2 Ratio)
    df_aq_bk = get_aq_breakdown([base_lei])
    # Profitability
    df_p = get_profitability_kpis([base_lei])
    # Yields
    df_y = get_nii_analysis([base_lei])
    # Sovereign
    df_sov = get_sovereign_kpis([base_lei])
    
    # 2. Fetch Latest Averages
    # Solvency Avg
    df_s_avg = get_solvency_averages(base_country, base_region, base_sys)
    # AQ Avg (NPL Ratio)
    df_aq_avg = get_asset_quality_averages(base_country, base_region, base_sys)
    # AQ Breakdown Avg (Stage 2 Ratio, S2/S3 Coverage)
    df_aq_bk_avg = get_aq_breakdown_averages(base_country, base_region, base_sys)
    # Profitability Avg
    df_p_avg = get_profitability_averages(base_country, base_region, base_sys)
    # Yields Avg
    df_y_avg = get_nii_averages(base_country, base_region, base_sys)
    # Sovereign Avg
    df_sov_avg = get_sovereign_averages(base_country, base_region, base_sys)
    
    if df_s.empty and df_p.empty:
        st.warning("No data available for this bank.")
        return

    # Helper to extract latest value
    def get_latest(df, col):
        if df.empty or col not in df.columns: return None
        return df.sort_values('period').iloc[-1][col]

    def get_latest_avg(df, col, group_name):
        if df.empty or col not in df.columns: return None
        d = df[(df['name'].str.contains(group_name))].sort_values('period')
        if d.empty: return None
        return d.iloc[-1][col]

    # --- PRE-CALCULATE DERIVED METRICS ---
    
    # 1. Non-Interest Income %
    if not df_p.empty:
        df_p['Non-Interest Income %'] = df_p.apply(lambda x: x['Non-Interest Income']/x['Total Operating Income'] if x['Total Operating Income'] else 0, axis=1)
    if not df_p_avg.empty:
        df_p_avg['Non-Interest Income %'] = df_p_avg.apply(lambda x: x['Non-Interest Income']/x['Total Operating Income'] if x['Total Operating Income'] else 0, axis=1)

    # 2. Sovereign Metrics
    # Base Bank
    df_sov_metrics = pd.DataFrame()
    if not df_sov.empty:
        # Concentration: Max Country Exposure / CET1
        sov_conc = df_sov.groupby(['period', 'country_name'])['amount'].sum().reset_index()
        # Join CET1 (which is per period)
        sov_cet1 = df_sov[['period', 'cet1']].drop_duplicates()
        sov_conc = pd.merge(sov_conc, sov_cet1, on='period')
        
        # Calculate ratio per country then take max per period
        sov_conc['ratio'] = sov_conc.apply(lambda x: x['amount']/x['cet1'] if x['cet1'] > 0 else 0, axis=1)
        df_conc_max = sov_conc.groupby('period')['ratio'].max().reset_index().rename(columns={'ratio': 'Sovereign Conc. vs CET1'})
        
        # Total Portfolio
        df_sov_tot = df_sov.groupby('period')['amount'].sum().reset_index().rename(columns={'amount': 'Total Sovereign Portfolio'})
        
        df_sov_metrics = pd.merge(df_conc_max, df_sov_tot, on='period')

    # Average (Sovereign)
    if not df_sov_avg.empty:
        # Concentration is already 'concentration_ratio'
        df_sov_avg.rename(columns={'concentration_ratio': 'Sovereign Conc. vs CET1'}, inplace=True)
        
        # Total Portfolio: Sum of amounts across portfolios for each period/name
        df_sov_avg_tot = df_sov_avg.groupby(['name', 'period'])['amount'].sum().reset_index().rename(columns={'amount': 'Total Sovereign Portfolio'})
        df_sov_avg = pd.merge(df_sov_avg, df_sov_avg_tot, on=['name', 'period'], suffixes=('', '_tot'))
        # Drop duplicates to keep it clean for get_latest_avg which expects time series
        df_sov_avg = df_sov_avg.drop_duplicates(subset=['name', 'period'])

    # --- SECTIONS ---
    
    # 1. Solvency
    sec_solvency = [
        ("CET1 Ratio", df_s, df_s_avg, True),
        ("Total Capital Ratio", df_s, df_s_avg, True),
        ("Leverage Ratio", df_s, df_s_avg, True)
    ]
    
    # 2. Asset Quality
    sec_aq = [
         ("NPL Ratio", df_aq, df_aq_avg, False),
         ("Stage 2 Ratio", df_aq_bk, df_aq_bk_avg, False),
         ("Stage 3 Coverage", df_aq_bk, df_aq_bk_avg, True),
         ("Stage 2 Coverage", df_aq_bk, df_aq_bk_avg, True)
    ]
    
    # 3. Profitability
    sec_prof = [
        ("RoE (Annualized)", df_p, df_p_avg, True),
        ("RoRWA (Annualized)", df_p, df_p_avg, True),
        ("Cost to Income", df_p, df_p_avg, False),
        ("Cost of Risk (Ann.)", df_p, df_p_avg, False),
        ("Non-II %", df_p, df_p_avg, True),
        ("Net Fees / Assets (Ann.)", df_p, df_p_avg, True)
    ]
    
    # 4. Yields (Assets)
    sec_yields = [
        ("Implied Loan Yield", df_y, df_y_avg, True),
        ("Implied Sec. Yield", df_y, df_y_avg, True),
        ("Margin: Loan Yield", df_y, df_y_avg, True),
        ("Margin: Securities Yield", df_y, df_y_avg, True),
    ]
    
    # 5. Costs (Liabilities)
    sec_costs = [
        ("Implied Deposit Cost", df_y, df_y_avg, False),
        ("Margin: Deposit Cost", df_y, df_y_avg, True),
        ("Margin: Funding Cost", df_y, df_y_avg, True)
    ]
    
    # 6. Sovereign Risk
    sec_sov = [
        ("Total Sov. (M€)", df_sov_metrics, df_sov_avg, False),
        ("Sov. Conc. vs CET1", df_sov_metrics, df_sov_avg, False)
    ]

    # --- CONSOLIDATE METRICS ---
    all_rows = []
    
    # Define Sections
    sections = [
        ("🛡️ Solvency", sec_solvency),
        ("☣️ Asset Quality", sec_aq),
        ("💰 Profitability", sec_prof),
        ("📈 Yields (Assets)", sec_yields),
        ("📉 Costs (Liabilities)", sec_costs),
        ("🏛️ Sovereign", sec_sov)
    ]
    
    for category, metrics_list in sections:
        for label, df_bank, df_bench, higher_is_better in metrics_list:
            col = label
            # Map labels to DB column names if different
            if label == "NPL Ratio": col = 'npl_ratio'
            if label == "Cost of Risk (Ann.)": col = 'Cost of Risk (Annualized)'
            if label == "Non-II %": col = 'Non-Interest Income %'
            if label == "Implied Sec. Yield": col = 'Implied Securities Yield'
            if label == "Implied Dep. Cost": col = 'Implied Deposit Cost'
            if label == "Total Sov. (M€)": col = 'Total Sovereign Portfolio'
            if label == "Sov. Conc. vs CET1": col = 'Sovereign Conc. vs CET1'
            if label == "Net Fees / Assets (Ann.)": col = 'Net Fees / Assets (Annualized)'
            if label.startswith("Margin:"): col = label

            val_bank = get_latest(df_bank, col)
            if val_bank is None: continue
            
            val_dom = get_latest_avg(df_bench, col, "Domestic")
            val_reg = get_latest_avg(df_bench, col, "Regional")
            val_eu = get_latest_avg(df_bench, col, "EU")
            
            all_rows.append({
                "Category": category,
                "Metric": label,
                f"{base_bank_name}": val_bank,
                "Domestic Avg": val_dom,
                "vs Domestic": (val_bank - val_dom) if val_dom is not None else None,
                "Regional Avg": val_reg,
                "vs Regional": (val_bank - val_reg) if val_reg is not None else None,
                "EU Avg": val_eu,
                "vs EU": (val_bank - val_eu) if val_eu is not None else None,
                "_higher_is_better": higher_is_better
            })

    if not all_rows:
        st.info("No metrics available.")
        return

    df_ov = pd.DataFrame(all_rows)
    # Set multi-index for nice grouping or just keep Category as column
    # st.dataframe handles columns well. Category as first column is good.
    
    # Styling
    pct_rows = []
    val_rows = []
    for i, r in df_ov.iterrows():
        if "(M€)" in r['Metric'] or "Total Sov" in r['Metric']: val_rows.append(i)
        else: pct_rows.append(i)
        
    data_cols = [f"{base_bank_name}", "Domestic Avg", "Regional Avg", "EU Avg", "vs Domestic", "vs Regional", "vs EU"]
    
    s = df_ov.style
    if pct_rows: s = s.format("{:.2%}", subset=pd.IndexSlice[pct_rows, data_cols], na_rep="")
    if val_rows: s = s.format("{:,.0f}", subset=pd.IndexSlice[val_rows, data_cols], na_rep="")
    
    def color_deviation(val, higher_is_better):
        if pd.isna(val) or pd.isna(higher_is_better): return ""
        is_good = (val > 0) == (higher_is_better)
        color = "green" if is_good else "red"
        return f"color: {color}"

    s = s.apply(lambda x: [
        color_deviation(x["vs Domestic"], df_ov.loc[x.name, "_higher_is_better"]) if col == "vs Domestic" else 
        color_deviation(x["vs Regional"], df_ov.loc[x.name, "_higher_is_better"]) if col == "vs Regional" else
        color_deviation(x["vs EU"], df_ov.loc[x.name, "_higher_is_better"]) if col == "vs EU" else "" 
        for col in x.index
    ], axis=1, subset=["vs Domestic", "vs Regional", "vs EU"])
    
    if '_higher_is_better' in df_ov.columns:
         s = s.hide(['_higher_is_better'], axis=1)
    
    st.markdown("#### Consolidated KPI Overview")
    st.dataframe(s, use_container_width=True, hide_index=True)
