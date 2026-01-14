import streamlit as st
import pandas as pd
import io
from ...data.credit_risk import get_cre_filter_options, get_cre_data, get_dim_maps
from eba_benchmarking.utils import format_value

def render_credit_risk_tab(selected_leis, base_bank_name=None, *args, **kwargs):
    st.header("Credit Risk Deep-Dive")
    st.markdown("Explore granular data from the Credit Risk (CRE) table.")

    if not selected_leis:
        st.warning("Please select at least one bank to view data.")
        return

    # --- FILTERS ---
    # Fetch dimension maps for label display in filters
    dim_maps = get_dim_maps()
    
    with st.expander("🔎 Data Filters", expanded=True):
        # Fetch available options (IDs) based on selected LEIs
        options_map_ids = get_cre_filter_options(selected_leis)
        
        if not options_map_ids:
            st.error("No data found for the selected banks in the Credit Risk table.")
            return

        # Helper to format options as "ID - Label"
        def format_options(col_name, ids):
            labels_map = dim_maps.get(col_name, {})
            # Return list of tuples (id, display_label) or just list of display_labels?
            # Streamlit selectbox options are just values. We can map them.
            # But the filter query needs IDs.
            # Best approach: Use format_func in st.multiselect if we pass IDs.
            return ids
        
        # Helper for format_func
        def get_label_func(col_name):
            labels_map = dim_maps.get(col_name, {})
            def fmt(val):
                lbl = labels_map.get(str(val), "")
                return f"{val} ({lbl})" if lbl and str(val) != lbl else str(val)
            return fmt

        col1, col2, col3 = st.columns(3)
        col4, col5 = st.columns(2)
        
        filters = {}

        with col1:
            filters['portfolio'] = st.multiselect("Portfolio", options=options_map_ids.get('portfolio', []), format_func=get_label_func('portfolio'), key="cre_portfolio")
            filters['status'] = st.multiselect("Status", options=options_map_ids.get('status', []), format_func=get_label_func('status'), key="cre_status")
        
        with col2:
            filters['exposure'] = st.multiselect("Exposure Class", options=options_map_ids.get('exposure', []), format_func=get_label_func('exposure'), key="cre_exposure")
            filters['perf_status'] = st.multiselect("Perf. Status", options=options_map_ids.get('perf_status', []), format_func=get_label_func('perf_status'), key="cre_perf_status")
            
        with col3:
            filters['country'] = st.multiselect("Country", options=options_map_ids.get('country', []), format_func=get_label_func('country'), key="cre_country")

        with col4:
             filters['nace_codes'] = st.multiselect("NACE Codes", options=options_map_ids.get('nace_codes', []), format_func=get_label_func('nace_codes'), key="cre_nace")
        
        with col5:
             # Added format_func for Item ID
             filters['item_id'] = st.multiselect("Item ID", options=options_map_ids.get('item_id', []), format_func=get_label_func('item_id'), key="cre_item_id")

    # --- DATA FETCHING ---
    df = get_cre_data(selected_leis, filters)
    
    if df.empty:
        st.info("No data matches the selected filters.")
        return

    # --- DISPLAY & EXPORT ---
    st.subheader(f"Results ({len(df)} rows)")
    
    # Reorder columns to show Labels next to IDs, or hide IDs if preferred. 
    # Current query returns: lei, Bank, period, item_id, "Item Label", portfolio, "Portfolio Label", etc.
    # Rename columns for cleaner display
    df_display = df.copy()
    rename_map = {
        'Item Label': 'Item',
        'Portfolio Label': 'Portfolio',
        'Exposure Label': 'Exposure Class',
        'Status Label': 'Status',
        'Perf Status Label': 'Perf. Status',
        'Country Label': 'Country',
        'NACE Label': 'NACE Sector',
        # Raw IDs
        'item_id': 'Item ID',
        'portfolio': 'Portfolio ID',
        'exposure': 'Exposure ID',
        'status': 'Status ID',
        'perf_status': 'Perf. Status ID',
        'country': 'Country Code',
        'nace_codes': 'NACE Code'
    }
    df_display.rename(columns=rename_map, inplace=True)

    # Reorder columns
    cols_order = [
        'period', 'Bank', 
        'Item', 
        'Portfolio', 
        'Exposure Class',
        'Status',
        'Perf. Status',
        'Country',
        'NACE Sector',
        'amount',
        # Raw IDs at end
        'Item ID', 'Portfolio ID', 'Exposure ID', 'Status ID', 'Perf. Status ID', 'Country Code', 'NACE Code'
    ]
    
    st.dataframe(df_display[cols_order], use_container_width=True, height=500)
    
    # Export options
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download CSV",
            csv,
            "credit_risk_deep_dive.csv",
            "text/csv",
            key='download-cre-csv'
        )

    with col_dl2:
        # Excel export
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
        
        st.download_button(
            label="📊 Download Excel",
            data=buffer,
            file_name="credit_risk_deep_dive.xlsx",
            mime="application/vnd.ms-excel",
            key='download-cre-excel'
        )
