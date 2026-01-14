import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from eba_benchmarking.data import (
    get_eba_kris, get_financial_data
)

def render_country_bench_tab(base_country, base_bank_name, selected_leis):
    """
    Renders the EBA Country Benchmarking tab.
    """
    st.subheader("EBA Risk Dashboard Benchmarking")
    df_kri = get_eba_kris(base_country)
    
    # Needs financial data for the bank overlay
    df_std = get_financial_data(selected_leis)
    
    if not df_kri.empty:
        kri_options = sorted(df_kri['kri_name'].unique())
        sel_kri = st.selectbox("Select Key Risk Indicator (KRI)", kri_options, index=kri_options.index('Share of non‐performing loans and advances (NPL ratio)') if 'Share of non‐performing loans and advances (NPL ratio)' in kri_options else 0)
        
        # Filter KRI Data
        df_kri_filtered = df_kri[df_kri['kri_name'] == sel_kri].copy()
        
        # Map Bank Data to match KRI logic (Manual mapping for key ones)
        bank_kri_map = {
            'Share of non‐performing loans and advances (NPL ratio)': 'npl_ratio',
            'CET 1 capital ratio': 'CET1 Ratio',
            'Tier 1 capital ratio': 'Tier 1 Ratio',
            'Total capital ratio': 'Total Capital Ratio',
            'Leverage ratio': 'Leverage Ratio',
            'Cost to income ratio': 'Cost to Income'
        }
        
        fig = go.Figure()
        
        # 1. Plot Country Avg
        df_ctry = df_kri_filtered[df_kri_filtered['country'] == base_country].sort_values('period')
        fig.add_trace(go.Scatter(x=df_ctry['period'], y=df_ctry['value'], name=f"EBA: {base_country} Avg", line=dict(dash='dash')))
        
        # 2. Plot EU Avg
        df_eu = df_kri_filtered[df_kri_filtered['country'] == 'EU'].sort_values('period')
        fig.add_trace(go.Scatter(x=df_eu['period'], y=df_eu['value'], name="EBA: EU Avg", line=dict(dash='dot', color='#00CC96', width=3)))
        
        # 3. Plot Base Bank (if mapped)
        if not df_std.empty and sel_kri in bank_kri_map and bank_kri_map[sel_kri] in df_std.columns:
            df_b = df_std[df_std['name'] == base_bank_name].sort_values('period')
            fig.add_trace(go.Scatter(x=df_b['period'], y=df_b[bank_kri_map[sel_kri]], name=base_bank_name, line=dict(color='#FF4B4B', width=4)))
        
        fig.update_layout(title=f"{sel_kri} Benchmarking", height=500, hovermode="x unified", legend=dict(orientation="h", y=1.02))
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("View Data Table"):
            st.dataframe(df_kri_filtered.pivot_table(index='period', columns='country', values='value').sort_index(ascending=False), use_container_width=True)
    else:
        st.warning("No EBA country-level benchmarking data found.")
