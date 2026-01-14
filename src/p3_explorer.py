import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import re
import os
import sys

# Add the 'src' directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from eba_benchmarking.config import DB_NAME

# Setup
st.set_page_config(page_title="Pillar 3 Benchmarking", layout="wide")
DB_PATH = DB_NAME

# Bank LEI Map (Static fallback)
LEI_MAP_STATIC = {
    'NLPK02SGC0U1AABDLL56': 'Alpha Bank',
    'JEUVK5RWVJEN8W0C9M24': 'Eurobank',
    '5UMCZOEYKCVFAW8ZLO05': 'National Bank of Greece',
    '213800OYHR4PPVA77574': 'Piraeus Bank',
    '635400L14KNHJ3DMBX37': 'Bank of Cyprus',
}

GREEK_LEIS = list(LEI_MAP_STATIC.keys())

# Tables config
BANK_SPECIFIC_TABLES = ['facts_cre', 'facts_mrk', 'facts_sov', 'facts_oth']
NON_BANK_TABLES = ['market_data', 'macro_economics', 'ecb_stats', 'eba_kris', 'base_rates', 'bog_macro']


@st.cache_data
def load_dimension_mappings():
    """Load all dimension mappings from the database into dictionaries for fast lookup."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    mappings = {}
    
    # dim_portfolio
    cursor.execute("SELECT portfolio, label FROM dim_portfolio")
    mappings['portfolio'] = dict(cursor.fetchall())
    
    # dim_exposure
    cursor.execute("SELECT exposure, label FROM dim_exposure")
    mappings['exposure'] = dict(cursor.fetchall())
    
    # dim_status
    cursor.execute("SELECT status, label FROM dim_status")
    mappings['status'] = dict(cursor.fetchall())
    
    # dim_perf_status
    cursor.execute("SELECT perf_status, label FROM dim_perf_status")
    mappings['perf_status'] = dict(cursor.fetchall())
    
    # dim_nace_codes
    cursor.execute("SELECT nace_codes, label FROM dim_nace_codes")
    mappings['nace_codes'] = dict(cursor.fetchall())
    
    # dim_mkt_modprod
    cursor.execute("SELECT mkt_modprod, label FROM dim_mkt_modprod")
    mappings['mkt_modprod'] = dict(cursor.fetchall())
    
    # dim_mkt_risk
    cursor.execute("SELECT mkt_risk, label FROM dim_mkt_risk")
    mappings['mkt_risk'] = dict(cursor.fetchall())
    
    # dim_maturity
    cursor.execute("SELECT maturity, label FROM dim_maturity")
    mappings['maturity'] = dict(cursor.fetchall())
    
    # dim_accounting_portfolio
    cursor.execute("SELECT accounting_portfolio, label FROM dim_accounting_portfolio")
    mappings['accounting_portfolio'] = dict(cursor.fetchall())
    
    # dim_assets_fv
    cursor.execute("SELECT assets_fv, label FROM dim_assets_fv")
    mappings['assets_fv'] = dict(cursor.fetchall())
    
    # dim_assets_stages
    cursor.execute("SELECT assets_stages, label FROM dim_assets_stages")
    mappings['assets_stages'] = dict(cursor.fetchall())
    
    # dim_financial_instruments
    cursor.execute("SELECT financial_instruments, label FROM dim_financial_instruments")
    mappings['financial_instruments'] = dict(cursor.fetchall())
    
    # dim_country (by country id for numeric lookups)
    cursor.execute("SELECT country, label FROM dim_country")
    mappings['country_id'] = dict(cursor.fetchall())
    
    # dim_country (by iso_code for text lookups)
    cursor.execute("SELECT iso_code, label FROM dim_country WHERE iso_code IS NOT NULL AND iso_code NOT LIKE '\\_%' ESCAPE '\\'")
    mappings['country_iso'] = dict(cursor.fetchall())
    
    conn.close()
    return mappings


def translate_value(val, mapping):
    """Translate a single value using a mapping dictionary."""
    if pd.isna(val):
        return val
    # Handle numpy types
    if hasattr(val, 'item'):
        val = val.item()
    key = str(val)
    result = mapping.get(key)
    if result is not None:
        return result
    # Try integer key as fallback
    return mapping.get(int(val), val)


def translate_dimensions(df, table_name, dim_mappings):
    """Translate dimension codes to human-readable labels."""
    if df.empty:
        return df
    
    df = df.copy()
    
    if table_name == 'facts_cre':
        # Translate portfolio
        if 'portfolio' in df.columns:
            df['Portfolio'] = df['portfolio'].apply(lambda x: translate_value(x, dim_mappings.get('portfolio', {})))
        
        # Translate exposure
        if 'exposure' in df.columns:
            df['Exposure Type'] = df['exposure'].apply(lambda x: translate_value(x, dim_mappings.get('exposure', {})))
        
        # Translate status
        if 'status' in df.columns:
            df['Status'] = df['status'].apply(lambda x: translate_value(x, dim_mappings.get('status', {})))
        
        # Translate perf_status
        if 'perf_status' in df.columns:
            df['Performance Status'] = df['perf_status'].apply(lambda x: translate_value(x, dim_mappings.get('perf_status', {})))
        
        # Translate nace_codes
        if 'nace_codes' in df.columns:
            df['NACE Code'] = df['nace_codes'].apply(lambda x: translate_value(x, dim_mappings.get('nace_codes', {})))
        
        # Translate country (try ISO code first, then ID)
        if 'country' in df.columns:
            def translate_country(val):
                if pd.isna(val):
                    return val
                # Handle numpy types
                if hasattr(val, 'item'):
                    val = val.item()
                key = str(val)
                # Try ISO code lookup first
                result = dim_mappings.get('country_iso', {}).get(key)
                if result:
                    return result
                # Fall back to ID lookup (try both string and int)
                result = dim_mappings.get('country_id', {}).get(key)
                if result:
                    return result
                # Try integer conversion
                try:
                    return dim_mappings.get('country_id', {}).get(int(key), key)
                except (ValueError, TypeError):
                    return key
            df['Country'] = df['country'].apply(translate_country)
        
        # Drop original numeric columns
        cols_to_drop = [c for c in ['portfolio', 'exposure', 'status', 'perf_status', 'nace_codes', 'country'] if c in df.columns]
        df = df.drop(columns=cols_to_drop)
    
    elif table_name == 'facts_mrk':
        # Translate portfolio
        if 'portfolio' in df.columns:
            df['Portfolio'] = df['portfolio'].apply(lambda x: translate_value(x, dim_mappings.get('portfolio', {})))
        
        # Translate mkt_modprod
        if 'mkt_modprod' in df.columns:
            df['Market Mod Prod'] = df['mkt_modprod'].apply(lambda x: translate_value(x, dim_mappings.get('mkt_modprod', {})))
        
        # Translate mkt_risk
        if 'mkt_risk' in df.columns:
            df['Market Risk'] = df['mkt_risk'].apply(lambda x: translate_value(x, dim_mappings.get('mkt_risk', {})))
        
        # Drop original numeric columns
        cols_to_drop = [c for c in ['portfolio', 'mkt_modprod', 'mkt_risk'] if c in df.columns]
        df = df.drop(columns=cols_to_drop)
    
    elif table_name == 'facts_sov':
        # Translate country (try ISO code first, then ID)
        if 'country' in df.columns:
            def translate_country(val):
                if pd.isna(val):
                    return val
                # Handle numpy types
                if hasattr(val, 'item'):
                    val = val.item()
                key = str(val)
                # Try ISO code lookup first
                result = dim_mappings.get('country_iso', {}).get(key)
                if result:
                    return result
                # Fall back to ID lookup (try both string and int)
                result = dim_mappings.get('country_id', {}).get(key)
                if result:
                    return result
                # Try integer conversion
                try:
                    return dim_mappings.get('country_id', {}).get(int(key), key)
                except (ValueError, TypeError):
                    return key
            df['Country'] = df['country'].apply(translate_country)
        
        # Translate maturity
        if 'maturity' in df.columns:
            df['Maturity'] = df['maturity'].apply(lambda x: translate_value(x, dim_mappings.get('maturity', {})))
        
        # Translate accounting_portfolio
        if 'accounting_portfolio' in df.columns:
            df['Accounting Portfolio'] = df['accounting_portfolio'].apply(lambda x: translate_value(x, dim_mappings.get('accounting_portfolio', {})))
        
        # Drop original numeric columns
        cols_to_drop = [c for c in ['country', 'maturity', 'accounting_portfolio'] if c in df.columns]
        df = df.drop(columns=cols_to_drop)
    
    elif table_name == 'facts_oth':
        # Translate assets_fv
        if 'assets_fv' in df.columns:
            df['Assets FV Hierarchy'] = df['assets_fv'].apply(lambda x: translate_value(x, dim_mappings.get('assets_fv', {})))
        
        # Translate assets_stages
        if 'assets_stages' in df.columns:
            df['Assets Stage'] = df['assets_stages'].apply(lambda x: translate_value(x, dim_mappings.get('assets_stages', {})))
        
        # Translate exposure
        if 'exposure' in df.columns:
            df['Exposure Type'] = df['exposure'].apply(lambda x: translate_value(x, dim_mappings.get('exposure', {})))
        
        # Translate financial_instruments
        if 'financial_instruments' in df.columns:
            df['Financial Instrument'] = df['financial_instruments'].apply(lambda x: translate_value(x, dim_mappings.get('financial_instruments', {})))
        
        # Drop original numeric columns
        cols_to_drop = [c for c in ['assets_fv', 'assets_stages', 'exposure', 'financial_instruments'] if c in df.columns]
        df = df.drop(columns=cols_to_drop)
    
    return df

@st.cache_data
def load_pillar3_data():
    conn = sqlite3.connect(DB_PATH)
    
    # Load Facts
    query = """
    SELECT 
        f.lei,
        f.period,
        f.template_code,
        f.row_id,
        f.amount,
        f.dimension_name,
        d.p3_label,
        d.category,
        d.eba_item_id
    FROM facts_pillar3 f
    LEFT JOIN pillar3_dictionary d 
      ON f.template_code = d.template_code AND f.row_id = d.row_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Map Bank Names using static map for Pillar 3 (which focuses on these 5)
    df['Bank'] = df['lei'].apply(lambda x: LEI_MAP_STATIC.get(x, x))
    
    return df

@st.cache_data
def load_institutions_metadata():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT lei, name, country_name, Systemic_Importance, region FROM institutions", conn)
    except:
        df = pd.DataFrame(columns=['lei', 'name', 'country_name', 'Systemic_Importance', 'region'])
    conn.close()
    return df

@st.cache_data
def fetch_table_data(table_name, limit=5000):
    conn = sqlite3.connect(DB_PATH)
    try:
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error loading table {table_name}: {e}")
        df = pd.DataFrame()
    conn.close()
    return df

@st.cache_data
def fetch_bank_data_filtered(table_name, leis):
    if not leis:
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_PATH)
    placeholders = ','.join(['?'] * len(leis))
    try:
        query = f"SELECT * FROM {table_name} WHERE lei IN ({placeholders})"
        df = pd.read_sql(query, conn, params=leis)
    except Exception as e:
        st.error(f"Error loading table {table_name}: {e}")
        df = pd.DataFrame()
    conn.close()
    return df

def get_unique_leis_from_table(table_name):
    conn = sqlite3.connect(DB_PATH)
    try:
        query = f"SELECT DISTINCT lei FROM {table_name}"
        df = pd.read_sql(query, conn)
        leis = df['lei'].tolist()
    except:
        leis = []
    conn.close()
    return leis

def show_pillar3_page():
    st.title("Pillar 3 Static Benchmarking")
    
    # Sidebar - Data Management
    if st.sidebar.button("Refresh Data", key='refresh_p3'):
        st.cache_data.clear()
        st.rerun()

    df = load_pillar3_data()
    
    # Sidebar Filters
    st.sidebar.header("Filters")
    
    # 1. Select Banks
    all_banks = sorted(df['Bank'].unique())
    selected_banks = st.sidebar.multiselect("Select Banks", all_banks, default=all_banks)
    
    # 2. Select Template
    all_templates = sorted(df['template_code'].unique())
    if not all_templates:
        st.warning("No data found.")
        return
        
    selected_template = st.sidebar.selectbox("Select Template", all_templates)
    
    # 3. Select Period
    # Filter periods based on template availability if needed, but global is fine
    all_periods = sorted(df['period'].unique())
    selected_period = st.sidebar.selectbox("Select Period", all_periods, index=len(all_periods)-1)
    
    # Filter Data
    mask = (
        (df['Bank'].isin(selected_banks)) & 
        (df['template_code'] == selected_template) &
        (df['period'] == selected_period)
    )
    subset = df[mask]
    
    if subset.empty:
        st.warning("No data found for the selected filters.")
        return
        
    # Main View
    st.subheader(f"Template: {selected_template} ({selected_period})")
    
    # Create a nice label combining ID and P3 Label
    subset['Row Label'] = subset['row_id'].astype(str) + " - " + subset['p3_label'].fillna('')
    
    # Append dimension if it's not Default
    mask_dim = (subset['dimension_name'].notna()) & (subset['dimension_name'] != 'Default')
    subset.loc[mask_dim, 'Row Label'] += " (" + subset.loc[mask_dim, 'dimension_name'] + ")"
    
    pivot_df = subset.pivot_table(
        index=['row_id', 'Row Label', 'dimension_name', 'category'],
        columns='Bank',
        values='amount',
        aggfunc='sum'
    ).reset_index()
    
    # Sort by Row ID naturally
    def get_sort_key(rid):
        # Handle "EU 1", "1", "4a"
        m = re.match(r'^([^\d]*)(\d+)([a-z]*)', str(rid), re.I)
        if m:
            prefix, num, suffix = m.groups()
            return (prefix, int(num), suffix.lower())
        return ("", 9999, str(rid))
    
    pivot_df['sort_tuple'] = pivot_df['row_id'].apply(get_sort_key)
    pivot_df = pivot_df.sort_values('sort_tuple').drop(columns=['sort_tuple'])
    
    st.dataframe(pivot_df, use_container_width=True)
    
    # Simple Chart
    st.subheader("Visual Comparison")
    
    # Select a row to visualize
    row_options = pivot_df['Row Label'].unique()
    selected_row = st.selectbox("Select Row to Visualize", row_options)
    
    if selected_row:
        chart_data = subset[subset['Row Label'] == selected_row]
        fig = px.bar(
            chart_data, 
            x='Bank', 
            y='amount', 
            title=f"Comparison: {selected_row}",
            color='Bank',
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

def show_database_explorer():
    st.title("Database Explorer")
    
    st.sidebar.header("Explorer Options")
    dataset_type = st.sidebar.radio("Data Category", ["Bank Specific Data (Transparency)", "Market / Macro Data"])
    
    meta_df = load_institutions_metadata()
    # Fill NA for filtering
    meta_df['Systemic_Importance'] = meta_df['Systemic_Importance'].fillna('Other')
    meta_df['region'] = meta_df['region'].fillna('Unknown')
    
    if dataset_type == "Bank Specific Data (Transparency)":
        table_name = st.sidebar.selectbox("Select Table", BANK_SPECIFIC_TABLES)
        
        # --- Advanced Filters ---
        st.sidebar.subheader("Filter Banks")
        
        # Systemic Importance
        all_sys = sorted(meta_df['Systemic_Importance'].unique())
        sel_sys = st.sidebar.multiselect("Systemic Importance", all_sys, default=['GSIB', 'OSII'])
        
        # Region
        all_regions = sorted(meta_df['region'].unique())
        sel_regions = st.sidebar.multiselect("Region", all_regions, default=all_regions)
        # ------------------------
        
        # Get unique LEIs currently in this table
        available_leis = get_unique_leis_from_table(table_name)
        
        if not available_leis:
            st.warning(f"No data found in table {table_name}")
            return

        # Filter available LEIs based on Metadata Filters
        # 1. Filter Metadata DF first
        filtered_meta = meta_df[
            (meta_df['Systemic_Importance'].isin(sel_sys)) &
            (meta_df['region'].isin(sel_regions))
        ]
        valid_leis_set = set(filtered_meta['lei'])
        
        # 2. Intersect with available data
        final_leis_options = [l for l in available_leis if l in valid_leis_set]
        
        # Create a mapping for the UI name
        # We prefer the institution name, fallback to static map, fallback to LEI
        ui_map = pd.Series(filtered_meta.name.values, index=filtered_meta.lei).to_dict()
        # Overlay static map for Greek banks to ensure familiar naming
        ui_map.update({k: v for k, v in LEI_MAP_STATIC.items() if k in valid_leis_set})
        
        def format_func(lei):
            return f"{ui_map.get(lei, lei)} ({lei})"
        
        # Determine defaults: The 4 Greek Banks
        # Only if they are in the final_leis_options
        TARGET_DEFAULTS = ['NLPK02SGC0U1AABDLL56', 'JEUVK5RWVJEN8W0C9M24', '5UMCZOEYKCVFAW8ZLO05', '213800OYHR4PPVA77574']
        defaults = [lei for lei in TARGET_DEFAULTS if lei in final_leis_options]
        
        selected_leis = st.sidebar.multiselect(
            f"Select Banks ({len(final_leis_options)} available)", 
            final_leis_options, 
            default=defaults,
            format_func=format_func
        )
        
        if st.sidebar.button("Load Data", key='load_bank_data'):
            with st.spinner("Fetching data..."):
                df = fetch_bank_data_filtered(table_name, selected_leis)
                
                # Load dimension mappings and translate
                dim_mappings = load_dimension_mappings()
                df = translate_dimensions(df, table_name, dim_mappings)
                
                # Add Bank Name column for readability (at the beginning)
                if not df.empty and 'lei' in df.columns:
                    # Use full map for display
                    full_map = pd.Series(meta_df.name.values, index=meta_df.lei).to_dict()
                    full_map.update(LEI_MAP_STATIC)
                    bank_name_col = df['lei'].apply(lambda x: full_map.get(x, x))
                    # Insert Bank Name at position 0
                    df = pd.concat([bank_name_col.rename('Bank Name'), df], axis=1)
                    
                st.subheader(f"Data: {table_name}")
                st.write(f"Rows: {len(df)}")
                st.dataframe(df, use_container_width=True)
                
                # Download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, f"{table_name}_extract.csv", "text/csv")
    
    else:
        # Market / Macro
        table_name = st.sidebar.selectbox("Select Table", NON_BANK_TABLES)
        
        if st.sidebar.button("Load Data", key='load_macro_data'):
            with st.spinner("Fetching data..."):
                df = fetch_table_data(table_name, limit=10000)
                
                st.subheader(f"Data: {table_name}")
                st.write(f"Rows: {len(df)}")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, f"{table_name}_extract.csv", "text/csv")

def main():
    page = st.sidebar.radio("Navigation", ["Pillar 3 Dashboard", "Database Explorer"])
    
    if page == "Pillar 3 Dashboard":
        show_pillar3_page()
    else:
        show_database_explorer()

if __name__ == "__main__":
    main()
