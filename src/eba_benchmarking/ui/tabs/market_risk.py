import streamlit as st
import pandas as pd
import io
from ...data.market_risk import get_mrk_filter_options, get_mrk_data, get_mrk_dim_maps
from eba_benchmarking.utils import format_value

def render_market_risk_tab(selected_leis, base_bank_name=None, *args, **kwargs):
    st.header("Market Risk Deep-Dive")
    st.markdown("Explore granular data from the Market Risk (MRK) table.")

    if not selected_leis:
        st.warning("Please select at least one bank to view data.")
        return

    # --- FILTERS ---
    dim_maps = get_mrk_dim_maps()
    
    with st.expander("🔎 Data Filters", expanded=True):
        options_map_ids = get_mrk_filter_options(selected_leis)
        
        if not options_map_ids:
            st.error("No data found for the selected banks in the Market Risk table.")
            return

        # Helper for format_func
        def get_label_func(col_name):
            labels_map = dim_maps.get(col_name, {})
            def fmt(val):
                lbl = labels_map.get(str(val), "")
                return f"{val} ({lbl})" if lbl and str(val) != lbl else str(val)
            return fmt

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        
        filters = {}

        with col1:
            filters['portfolio'] = st.multiselect("Portfolio", options=options_map_ids.get('portfolio', []), format_func=get_label_func('portfolio'), key="mrk_portfolio")
        
        with col2:
            filters['mkt_risk'] = st.multiselect("Market Risk Type", options=options_map_ids.get('mkt_risk', []), format_func=get_label_func('mkt_risk'), key="mrk_risk")
            
        with col3:
            # Updated to mkt_modprod
            filters['mkt_modprod'] = st.multiselect("Market Product", options=options_map_ids.get('mkt_modprod', []), format_func=get_label_func('mkt_modprod'), key="mrk_prod")

        with col4:
             filters['item_id'] = st.multiselect("Item ID", options=options_map_ids.get('item_id', []), key="mrk_item_id")

    # --- DATA FETCHING ---
    df = get_mrk_data(selected_leis, filters)
    
    if df.empty:
        st.info("No data matches the selected filters.")
        return

    # --- DISPLAY & EXPORT ---
    st.subheader(f"Results ({len(df)} rows)")

    cols_order = [
        'period', 'Bank', 'item_id', 
        'Portfolio Label', 'portfolio', 
        'Product Label', 'mkt_modprod',
        'Risk Label', 'mkt_risk',
        'amount'
    ]
    
    st.dataframe(df[cols_order], use_container_width=True, height=500)
    
    # Export options
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download CSV",
            csv,
            "market_risk_deep_dive.csv",
            "text/csv",
            key='download-mrk-csv'
        )

    with col_dl2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
        
        st.download_button(
            label="📊 Download Excel",
            data=buffer,
            file_name="market_risk_deep_dive.xlsx",
            mime="application/vnd.ms-excel",
            key='download-mrk-excel'
        )
