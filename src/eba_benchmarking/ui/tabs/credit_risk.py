import streamlit as st
import pandas as pd
import io
from ...data.credit_risk import get_cre_filter_options, get_cre_data
from eba_benchmarking.utils import format_value

def render_credit_risk_tab(selected_leis, base_bank_name=None, *args, **kwargs):
    st.header("Credit Risk Deep-Dive")
    st.markdown("Explore granular data from the Credit Risk (CRE) table.")

    if not selected_leis:
        st.warning("Please select at least one bank to view data.")
        return

    # --- FILTERS ---
    with st.expander("🔎 Data Filters", expanded=True):
        # Fetch available options based on selected LEIs
        options_map = get_cre_filter_options(selected_leis)
        
        if not options_map:
            st.error("No data found for the selected banks in the Credit Risk table.")
            return

        col1, col2, col3 = st.columns(3)
        col4, col5 = st.columns(2)
        
        filters = {}

        with col1:
            filters['portfolio'] = st.multiselect("Portfolio", options=options_map.get('portfolio', []), key="cre_portfolio")
            filters['status'] = st.multiselect("Status", options=options_map.get('status', []), key="cre_status")
        
        with col2:
            filters['exposure'] = st.multiselect("Exposure Class", options=options_map.get('exposure', []), key="cre_exposure")
            filters['perf_status'] = st.multiselect("Perf. Status", options=options_map.get('perf_status', []), key="cre_perf_status")
            
        with col3:
            # Replaced/Removed Residence and Sector
            filters['country'] = st.multiselect("Country", options=options_map.get('country', []), key="cre_country")
            # filters['counterparty_sector'] was removed as column doesn't exist

        with col4:
             filters['nace_codes'] = st.multiselect("NACE Codes", options=options_map.get('nace_codes', []), key="cre_nace")
        
        with col5:
             filters['item_id'] = st.multiselect("Item ID", options=options_map.get('item_id', []), key="cre_item_id")

    # --- DATA FETCHING ---
    df = get_cre_data(selected_leis, filters)
    
    if df.empty:
        st.info("No data matches the selected filters.")
        return

    # --- DISPLAY & EXPORT ---
    st.subheader(f"Results ({len(df)} rows)")
    
    # Calculate simple totals
    total_amount = df['amount'].sum()
    st.metric("Total Amount (Filtered)", format_value(total_amount, 'M', decimals=0))

    st.dataframe(df, use_container_width=True, height=500)
    
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
