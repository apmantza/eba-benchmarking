import streamlit as st
import pandas as pd
from eba_benchmarking.data import (
    get_liquidity_kpis, get_liquidity_averages
)
from eba_benchmarking.plotting import (
    plot_benchmark_bar, plot_solvency_trend
)

def render_liquidity_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys):
    """
    Renders the Liquidity & Funding Structure tab.
    """
    st.subheader("Liquidity & Funding Structure")
    
    # Fetch Data
    df_liq = get_liquidity_kpis(selected_leis)
    df_liq_bench = get_liquidity_averages(base_country, base_region, base_sys, base_size)
    
    if not df_liq.empty:
        latest_liq = df_liq['period'].max()
        df_liq_lat = df_liq[df_liq['period'] == latest_liq].copy()
        
        # Latest Benchmarks
        df_liq_bench_lat = df_liq_bench[df_liq_bench['period'] == latest_liq] if not df_liq_bench.empty else None
        
        # Row 1: LDR
        st.markdown("### 💧 Loan-to-Deposit Ratio (LDR)")
        c_ldr1, c_ldr2 = st.columns(2)
        with c_ldr1:
             # Bar
             df_ldr_bar = df_liq_lat[['name', 'LDR']].copy()
             if df_liq_bench_lat is not None:
                 df_ldr_bar = pd.concat([df_ldr_bar, df_liq_bench_lat[['name', 'LDR']]], ignore_index=True)
             st.plotly_chart(plot_benchmark_bar(df_ldr_bar, 'LDR', "LDR (Latest)", base_bank_name, format_pct=True), width='stretch', key='liq_ldr_bar')
        with c_ldr2:
             # Trend
             st.plotly_chart(plot_solvency_trend(df_liq, df_liq_bench, 'LDR', "LDR Trend", base_bank_name), width='stretch', key='liq_ldr_trend')
        
        # Row 2: Funding Gap
        st.markdown("### 📉 Funding Gap (Loans - Deposits)")
        c_gap1, c_gap2 = st.columns(2)
        with c_gap1:
             df_gap_bar = df_liq_lat[['name', 'Funding Gap']].copy()
             if df_liq_bench_lat is not None:
                 df_gap_bar = pd.concat([df_gap_bar, df_liq_bench_lat[['name', 'Funding Gap']]], ignore_index=True)
             st.plotly_chart(plot_benchmark_bar(df_gap_bar, 'Funding Gap', "Funding Gap (Latest) [€M]", base_bank_name, format_pct=False), width='stretch', key='liq_gap_bar')
        with c_gap2:
             st.plotly_chart(plot_solvency_trend(df_liq, df_liq_bench, 'Funding Gap', "Funding Gap Trend", base_bank_name), width='stretch', key='liq_gap_trend')
             
        # Download
        st.markdown("### 📥 Download Liquidity Dataset")
        df_liq_exp = pd.concat([df_liq, df_liq_bench], ignore_index=True)
        csv = df_liq_exp.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Liquidity Data (CSV)", data=csv, file_name='eba_benchmarking_liquidity.csv', mime='text/csv')
    else:
        st.warning("No liquidity data available.")
