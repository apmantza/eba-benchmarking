import streamlit as st
import pandas as pd
import os
import sys

# Add the 'src' directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from eba_benchmarking.config import DB_NAME
from eba_benchmarking.config import DB_NAME
from eba_benchmarking.data import get_master_data, get_financial_data, get_profitability_kpis, get_liquidity_kpis

# Import UI Tabs
from eba_benchmarking.ui.tabs.insights import render_insights_tab
from eba_benchmarking.ui.tabs.solvency import render_solvency_tab
from eba_benchmarking.ui.tabs.asset_quality import render_asset_quality_tab
from eba_benchmarking.ui.tabs.rwa import render_rwa_tab
from eba_benchmarking.ui.tabs.profitability import render_profitability_tab
from eba_benchmarking.ui.tabs.generic import render_generic_tab
from eba_benchmarking.ui.tabs.sovereign import render_sovereign_tab
from eba_benchmarking.ui.tabs.assets import render_assets_tab
from eba_benchmarking.ui.tabs.liabilities import render_liabilities_tab
from eba_benchmarking.ui.tabs.liquidity import render_liquidity_tab
from eba_benchmarking.ui.tabs.market_data import render_market_data_tab
from eba_benchmarking.ui.tabs.yields import render_yields_tab
from eba_benchmarking.ui.tabs.country_bench import render_country_bench_tab
from eba_benchmarking.ui.tabs.benchmarking_dashboard import render_benchmarking_dashboard_tab

# --- CONFIGURATION ---
st.set_page_config(page_title="EBA Benchmarking", layout="wide", page_icon="🏦")

# --- MAIN APP ---

st.sidebar.title("Peer Group Builder")

df_master = get_master_data()

if st.sidebar.button("🔄 Clear Data Cache"):
    st.cache_data.clear()
    st.rerun()

if df_master.empty: 
    st.error("⚠️ Database empty or commercial names missing. Run pipeline.")
    st.stop()

# Hardcoded base bank - National Bank of Greece
# Bank of Cyprus is included in domestic peers as it's listed on ATHEX
BASE_BANK_NAME = "National Bank of Greece"
ATHEX_PEER_LEIS = ['635400L14KNHZXPUZM19']  # Bank of Cyprus Holdings

base_bank_name = BASE_BANK_NAME
base_row_matches = df_master[df_master['commercial_name'] == base_bank_name]
if base_row_matches.empty:
    st.error(f"⚠️ Base bank '{base_bank_name}' not found in database. Run pipeline.")
    st.stop()

base_row = base_row_matches.iloc[0]
base_lei = base_row['lei']
base_country = base_row.get('country_iso', 'Unknown')
base_biz_model = base_row.get('business_model', 'Unknown')
base_size = base_row.get('size_category', 'Unknown')
base_region = base_row.get('region', 'Unknown')
base_sys = base_row.get('Systemic_Importance', 'Other')
base_assets = base_row.get('total_assets', 0)

st.sidebar.info(f"""
**{base_bank_name}**
📍 {base_row.get('country_name','N/A')} ({base_country} | {base_region})
🏦 {base_biz_model} | {base_sys}
⚖️ {base_size} (Assets: {base_assets/1000:,.1f}bn)
""")

peer_strategy = st.sidebar.radio("Peer Group", [
    "Domestic Peers (incl. BoC)", 
    "Manual Selection"
])
selected_leis = [base_lei]

if peer_strategy == "Domestic Peers (incl. BoC)":
    # Domestic peers (GR) + Bank of Cyprus (listed on ATHEX)
    peers = df_master[
        (
            (df_master['country_iso'] == base_country) | 
            (df_master['lei'].isin(ATHEX_PEER_LEIS))
        ) & 
        (df_master['lei'] != base_lei) &
        (df_master['Systemic_Importance'].isin(['GSIB', 'OSII']))
    ]
    selected_leis.extend(peers.head(9)['lei'].tolist())
elif peer_strategy == "Manual Selection":
    avail = df_master[df_master['lei'] != base_lei]
    sel = st.sidebar.multiselect("Select Peers (Max 9)", avail['commercial_name'].unique(), max_selections=9)
    selected_leis.extend(avail[avail['commercial_name'].isin(sel)]['lei'].tolist())

# DASHBOARD
st.title(f"Benchmarking: {base_bank_name}")

# Fetch Standard KPIs for header
df_std = get_financial_data(selected_leis)

# Enrich with Profitability (RoE, Cost to Income, NIM) for Insights
df_prof = get_profitability_kpis(selected_leis)
if not df_prof.empty and not df_std.empty:
    cols_to_merge = ['lei', 'period', 'RoE (Annualized)', 'Cost to Income', 'NIM (Annualized)']
    cols_to_merge = [c for c in cols_to_merge if c in df_prof.columns]
    df_std = pd.merge(df_std, df_prof[cols_to_merge], on=['lei', 'period'], how='left')

# Enrich with Liquidity (LDR) for Insights
df_liq = get_liquidity_kpis(selected_leis)
if not df_liq.empty and not df_std.empty:
    cols_liq = ['lei', 'period', 'LDR']
    cols_liq = [c for c in cols_liq if c in df_liq.columns]
    df_std = pd.merge(df_std, df_liq[cols_liq], on=['lei', 'period'], how='left')

if not df_std.empty:
    latest = df_std['period'].max()
    df_std_lat = df_std[df_std['period'] == latest].copy()
    st.caption(f"Period: {latest} | Banks: {len(df_std_lat)} | Peer Group: {peer_strategy}")

# TABS
tabs_list = [
    "📊 Benchmarking Dashboard",
    "🔎 Deep-Dive Explorer",
    "Solvency", 
    "Asset Quality", 
    "RWA", 
    "Profitability", 
    "Market Risk", 
    "Credit Risk", 
    "Sovereign", 
    "Assets",
    "Liabilities",
    "Liquidity",
    "Market Data",
    "Yields & Funding",
    "Country Benchmarking"
]
tabs = st.tabs(tabs_list)

# 0. BENCHMARKING DASHBOARD
with tabs[0]:
    render_benchmarking_dashboard_tab(base_lei, base_bank_name, base_country, base_region, base_sys, base_size)

# 1. DEEP-DIVE EXPLORER
with tabs[1]:
    # Import locally to avoid circular dependency issues if any
    from eba_benchmarking.ui.tabs.benchmarking_dashboard import render_custom_explorer
    render_custom_explorer(base_lei, base_bank_name, base_country, base_region, base_sys, base_size)

# 2. SOLVENCY TAB
with tabs[2]:
    render_solvency_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys)

# 3. ASSET QUALITY TAB
with tabs[3]:
    render_asset_quality_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys)

# 4. RWA TAB
with tabs[4]:
    render_rwa_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys)

# 5. PROFITABILITY TAB
with tabs[5]:
    # Note: Using base_lei for Jaws/Waterfall specifics if needed, passing it explicitly
    render_profitability_tab(selected_leis, base_bank_name, base_country, base_size, base_lei, base_region, base_sys)

# 6. MARKET RISK & 7. CREDIT RISK (Generic)
with tabs[6]:
    from eba_benchmarking.ui.tabs.market_risk import render_market_risk_tab
    render_market_risk_tab(selected_leis, base_bank_name)
with tabs[7]:
    from eba_benchmarking.ui.tabs.credit_risk import render_credit_risk_tab
    render_credit_risk_tab(selected_leis, base_bank_name)

# 8. SOVEREIGN TAB
with tabs[8]:
    render_sovereign_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys)

# 9. ASSETS TAB
with tabs[9]:
    render_assets_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys)

# 10. LIABILITIES TAB
with tabs[10]:
    render_liabilities_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys)

# 11. LIQUIDITY TAB
with tabs[11]:
    render_liquidity_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys)

# 12. MARKET DATA TAB
with tabs[12]:
    render_market_data_tab(selected_leis, base_bank_name)

# 13. YIELDS & FUNDING TAB
with tabs[13]:
    render_yields_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys)

# 14. COUNTRY BENCHMARKING
with tabs[14]:
    render_country_bench_tab(base_country, base_bank_name, selected_leis)