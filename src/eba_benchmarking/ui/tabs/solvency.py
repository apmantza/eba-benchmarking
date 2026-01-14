import streamlit as st
import pandas as pd
from eba_benchmarking.data import (
    get_solvency_kpis, get_solvency_averages,
    get_eba_kris, get_solvency_with_texas_ratio,
    get_regional_peers_raw_data
)
from eba_benchmarking.plotting import (
    plot_capital_components, plot_solvency_trend,
    plot_capital_ratios, plot_benchmark_bar, plot_texas_ratio
)

def render_solvency_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys):
    """
    Renders the Solvency tab.
    """
    st.subheader("🛡️ Solvency & Capital Analysis")
    
    df_solv = get_solvency_kpis(selected_leis)
    df_solv_bench = get_solvency_averages(base_country, base_region, base_sys, base_size)
    df_eu_kris = get_eba_kris(base_country) # Already contains 'EU'
    
    if not df_solv.empty:
        latest_solv = df_solv['period'].max()
        df_sl_latest = df_solv[df_solv['period'] == latest_solv].copy()
        
        # Latest benchmarks
        df_bench_latest = df_solv_bench[df_solv_bench['period'] == latest_solv] if not df_solv_bench.empty else None
        
        # Highlights
        base_solv_lat = df_sl_latest[df_sl_latest['name'] == base_bank_name].iloc[0] if not df_sl_latest[df_sl_latest['name'] == base_bank_name].empty else None
        if base_solv_lat is not None:
             c1, c2, c3, c4 = st.columns(4)
             c1.metric("Total Capital Ratio", f"{base_solv_lat['Total Capital Ratio']:.1%}")
             c2.metric("CET1 Ratio", f"{base_solv_lat['CET1 Ratio']:.1%}")
             c3.metric("Leverage Ratio", f"{base_solv_lat['Leverage Ratio']:.1%}")
             c4.metric("Total Capital", f"€{base_solv_lat['Total Capital']/1e6:,.0f}M")
             st.divider()

        # Row 1: Capital Components (Amounts)
        st.markdown("### 🏦 Capital Components")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_capital_components(df_sl_latest, base_bank_name, df_bench_latest), width='stretch')
        with c2:
            st.plotly_chart(plot_solvency_trend(df_solv, df_solv_bench, 'Total Capital', "Total Capital Amount Trend", base_bank_name), width='stretch')
            
        # Row 2: Capital Ratios
        st.markdown("### ⚖️ Capital Ratios")
        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(plot_capital_ratios(df_sl_latest, base_bank_name, df_bench_latest), width='stretch')
        with c4:
            st.plotly_chart(plot_solvency_trend(df_solv, df_solv_bench, 'Total Capital Ratio', "Total Capital Ratio Trend", base_bank_name, df_eu_kris), width='stretch')
            
        # Row 3: Leverage Ratio
        st.markdown("### 📉 Leverage Ratio")
        c5, c6 = st.columns(2)
        with c5:
            # For the bar chart, we combine bank data and benchmarks
            df_lev = df_sl_latest[['name', 'Leverage Ratio']].copy()
            if df_bench_latest is not None:
                df_lev = pd.concat([df_lev, df_bench_latest[['name', 'Leverage Ratio']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_lev, 'Leverage Ratio', "Leverage Ratio (Latest)", base_bank_name, format_pct=True), width='stretch')
        with c6:
            st.plotly_chart(plot_solvency_trend(df_solv, df_solv_bench, 'Leverage Ratio', "Leverage Ratio Trend", base_bank_name, df_eu_kris), width='stretch')
        
        # Row 4: RWA Density (REMOVED as per request)
        # st.markdown("### ⚖️ RWA Density (Risk Intensity)")
        # ...
        
        # Row 5: Texas Ratio
        st.markdown("### 🔥 Texas Ratio")
        # Removed info note as per request
        
        # Fetch solvency with Texas Ratio
        df_solv_texas = get_solvency_with_texas_ratio(selected_leis)
        
        if not df_solv_texas.empty and 'Texas Ratio' in df_solv_texas.columns:
            df_texas_lat = df_solv_texas[df_solv_texas['period'] == latest_solv].copy()
            
            # For Texas Ratio trend, we need benchmarks too.
            # Assuming df_solv_bench doesn't have Texas Ratio yet, or get_solvency_with_texas_ratio didn't compute it for peers/avgs?
            # get_solvency_with_texas_ratio takes LEIs. Benchmarks are aggregates.
            # Ideally we recalculate Texas Ratio for benchmarks or fetch it if available.
            # For now, pass df_solv_bench explicitly if it contains Texas Ratio, otherwise it might be missing.
            
            c_tx1, c_tx2 = st.columns(2)
            with c_tx1:
                # Add benchmarks to bar chart
                df_tx_bar = df_texas_lat[['name', 'Texas Ratio']].copy()
                # Benchmarks need 'Texas Ratio'. If df_solv_bench has it, use it.
                if 'Texas Ratio' in df_solv_bench.columns:
                    latest_bench = df_solv_bench[df_solv_bench['period'] == latest_solv]
                    df_tx_bar = pd.concat([df_tx_bar, latest_bench[['name', 'Texas Ratio']]], ignore_index=True)
                
                st.plotly_chart(plot_benchmark_bar(df_tx_bar, 'Texas Ratio', "Texas Ratio (Latest)", base_bank_name, format_pct=True), width='stretch', key='solv_texas_bar')
            with c_tx2:
                # Add benchmarks to trend
                # Only pass benchmarks if 'Texas Ratio' is available
                bench_trend = df_solv_bench if 'Texas Ratio' in df_solv_bench.columns else None
                st.plotly_chart(plot_texas_ratio(df_solv_texas, bench_trend, "Texas Ratio Trend", base_bank_name), width='stretch', key='solv_texas_trend')
        
        # Download - Consolidated Data
        st.markdown("### 📥 Download Solvency Dataset")
        st.caption("Includes Base Bank, Domestic Peers, Regional G-SIB/O-SII Benchmarks, and EU Averages.")
        
        # Prepare EU KRI data for export
        df_eu_exp = df_eu_kris[df_eu_kris['country'] == 'EU'].copy()
        df_eu_exp = df_eu_exp[df_eu_exp['kri_name'].isin(['Total capital ratio', 'Leverage ratio', 'CET 1 capital ratio'])]
        df_eu_exp.rename(columns={'kri_name': 'item_name', 'country': 'name'}, inplace=True)
        
        # Fetch individual banks for Regional Peers
        df_size_peers_raw = get_regional_peers_raw_data(base_region, base_sys, base_country, base_size)
        
        # Combine everything
        df_export = pd.concat([df_solv, df_solv_bench, df_size_peers_raw, df_eu_exp], ignore_index=True)
        # Drop duplicates based on name/period/lei if possible, but df_eu_exp doesn't have lei
        # We can drop by name/period to be safe
        df_export = df_export.drop_duplicates(subset=['name', 'period']).sort_values(['name', 'period'])
        
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full Solvency Data (CSV)", data=csv, file_name='eba_benchmarking_solvency.csv', mime='text/csv')
    else:
        st.warning("No solvency data found.")
