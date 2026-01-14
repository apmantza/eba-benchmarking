import streamlit as st
import pandas as pd
from eba_benchmarking.analysis.insights import generate_insights

def render_insights_tab(base_bank_name, df_std):
    """
    Renders the Executive Insights Tab.
    """
    st.header(f"Executive Insights: {base_bank_name}")
    
    if df_std is None or df_std.empty:
        st.warning("No data available for insights.")
        return

    # Filter for Base Bank
    latest = df_std['period'].max()
    df_lat = df_std[df_std['period'] == latest]
    base = df_lat[df_lat['name'] == base_bank_name]
    
    if base.empty:
        st.error(f"Data missing for {base_bank_name}.")
        return
    
    row = base.iloc[0]
    
    # Format Helper
    def fmt(val, is_pct=True):
        if pd.isna(val): return "N/A"
        return f"{val:.1%}" if is_pct else f"{val:.2f}"
        
    roe = row.get('RoE (Annualized)')
    cet1 = row.get('CET1 Ratio')
    npl = row.get('npl_ratio')
    ci = row.get('Cost to Income')
    ldr = row.get('LDR')
    nim = row.get('NIM (Annualized)')
    
    # Row 1: Key Performance Indicators
    st.markdown("#### Key Performance Indicators")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("RoE", fmt(roe))
    c2.metric("NIM", fmt(nim))
    c3.metric("Cost/Income", fmt(ci))
    c4.metric("CET1", fmt(cet1))
    c5.metric("NPL Ratio", fmt(npl))
    c6.metric("LDR", fmt(ldr))
    
    st.divider()
    
    # Row 2: AI Insights
    st.subheader("💡 Strategic Assessment")
    
    insights = generate_insights(df_std, base_bank_name)
    if insights:
        for insight in insights:
            # Use a container for nicer styling
            with st.container():
                st.markdown(insight)
    else:
        st.info("No significant deviations from peers detected.")
