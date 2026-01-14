import streamlit as st
import pandas as pd
from eba_benchmarking.data import (
    get_solvency_kpis, get_solvency_averages,
    get_rwa_composition, get_rwa_composition_averages
)
from eba_benchmarking.plotting import (
    plot_benchmark_bar, plot_solvency_trend, plot_rwa_composition
)

def render_rwa_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys):
    """
    Renders the RWA (Risk Weighted Assets) tab.
    """
    st.subheader("Risk-Weighted Assets Analysis")
    
    # Fetch solvency data which now includes RWA Density
    df_rwa = get_solvency_kpis(selected_leis)
    df_rwa_bench = get_solvency_averages(base_country, base_region, base_sys, base_size)
    
    if not df_rwa.empty:
        latest_rwa = df_rwa['period'].max()
        df_rwa_lat = df_rwa[df_rwa['period'] == latest_rwa].copy()
        df_rwa_bench_lat = df_rwa_bench[df_rwa_bench['period'] == latest_rwa] if not df_rwa_bench.empty else None
        
        # Summary KPIs
        base_rwa_lat = df_rwa_lat[df_rwa_lat['name'] == base_bank_name].iloc[0] if not df_rwa_lat[df_rwa_lat['name'] == base_bank_name].empty else None
        if base_rwa_lat is not None:
            c1, c2, c3 = st.columns(3)
            # TREA is in millions in DB. Display in Billions.
            c1.metric("Total RWA (TREA)", f"€{base_rwa_lat['TREA']/1000:,.1f}B")
            c2.metric("RWA Density", f"{base_rwa_lat.get('RWA Density', 0):.1%}")
            
            # Total Assets is in Millions. Display in Billions.
            total_assets_val = base_rwa_lat.get('total_assets', 0)
            c3.metric("Total Assets", f"€{total_assets_val/1000:,.1f}B")
            st.divider()
        
        # Row 1: Total RWA
        st.markdown("### ⚖️ Total Risk-Weighted Assets (TREA)")
        c_trea1, c_trea2 = st.columns(2)
        with c_trea1:
            df_trea_bar = df_rwa_lat[['name', 'TREA']].copy()
            # Scale to Billions for bar chart values
            # df_trea_bar['TREA'] = df_trea_bar['TREA'] / 1e3 # REMOVED: plot_benchmark_bar handles scaling if format_pct=False
            # Wait, amount_unit is 1e6. So TREA is in M. 
            # To get Billions: TREA (in M) / 1000.
            # But plot_benchmark_bar handles scaling if format_pct=False.
            # Wait, plot_benchmark_bar in basic.py: 
            # if not format_pct: df_plot[metric_col] = df_plot[metric_col] / 1000.0
            # So if TREA is in Millions, it divides by 1000 -> Billions. 
            # So the Bar Chart is ALREADY doing Billions if raw data is Millions.
            # Let's check df_rwa units. get_solvency_kpis usually returns M.
            # So Bar chart is fine.
            
            if df_rwa_bench_lat is not None and 'TREA' in df_rwa_bench_lat.columns:
                df_trea_bar = pd.concat([df_trea_bar, df_rwa_bench_lat[['name', 'TREA']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_trea_bar, 'TREA', "Total RWA (Latest)", base_bank_name, format_pct=False), width='stretch', key='rwa_trea_bar')
        with c_trea2:
            # Trend Chart: plot_solvency_trend automatically handles formatting to Billions if it detects "TREA" (Amount/Capital).
            # I added logic in solvency.py to detect 'Amount' or 'Capital' but TREA might drift.
            # Update call to ensure it's treated as amount. Title "Total RWA Trend" has "Total" not "Amount".
            # 'TREA' is not 'Capital'.
            # I should update title or ensure logic covers TREA.
            st.plotly_chart(plot_solvency_trend(df_rwa, df_rwa_bench, 'TREA', "Total RWA Amount Trend (TREA)", base_bank_name), width='stretch', key='rwa_trea_trend')
        
        # Row 2: RWA Density
        st.markdown("### 📊 RWA Density (Risk Intensity)")
        # Removed info note as per request
        
        if 'RWA Density' in df_rwa.columns:
            c_den1, c_den2 = st.columns(2)
            with c_den1:
                df_den_bar = df_rwa_lat[['name', 'RWA Density']].copy()
                if df_rwa_bench_lat is not None and 'RWA Density' in df_rwa_bench_lat.columns:
                    df_den_bar = pd.concat([df_den_bar, df_rwa_bench_lat[['name', 'RWA Density']]], ignore_index=True)
                st.plotly_chart(plot_benchmark_bar(df_den_bar, 'RWA Density', "RWA Density (Latest)", base_bank_name, format_pct=True), width='stretch', key='rwa_density_bar')
            with c_den2:
                st.plotly_chart(plot_solvency_trend(df_rwa, df_rwa_bench, 'RWA Density', "RWA Density Trend", base_bank_name), width='stretch', key='rwa_density_trend')
        
        # Row 3: RWA Composition (from raw category data)
        st.markdown("### 🧩 RWA Composition by Category")
        df_rwa_raw = get_rwa_composition(selected_leis)
        df_rwa_raw_bench = get_rwa_composition_averages(base_country, base_region, base_sys, base_size)
        
        if not df_rwa_raw.empty:
            df_rwa_raw_lat = df_rwa_raw[df_rwa_raw['period'] == latest_rwa].copy()
            
            # Combine with benchmarks for latest period
            if not df_rwa_raw_bench.empty:
                df_rwa_bench_lat = df_rwa_raw_bench[df_rwa_raw_bench['period'] == latest_rwa].copy()
                df_rwa_raw_combined = pd.concat([df_rwa_raw_lat, df_rwa_bench_lat], ignore_index=True)
            else:
                df_rwa_raw_combined = df_rwa_raw_lat
            
            # RWA Composition Charts
            c_comp1, c_comp2 = st.columns(2)
            with c_comp1:
                 st.plotly_chart(plot_rwa_composition(df_rwa_raw_combined, base_bank_name, show_pct=False), width='stretch', key='rwa_comp_abs')
            with c_comp2:
                 st.plotly_chart(plot_rwa_composition(df_rwa_raw_combined, base_bank_name, show_pct=True), width='stretch', key='rwa_comp_pct')
            
            # Show composition table
            with st.expander("View Raw Data"):
                df_rwa_pivot = df_rwa_raw_lat.pivot_table(
                    index=['name', 'lei'], columns='label', values='amount', aggfunc='sum'
                ).reset_index()
                st.dataframe(df_rwa_pivot, use_container_width=True)
        
        # Download
        st.markdown("### 📥 Download RWA Dataset")
        # Combine Main RWA data and Composition Data
        df_rwa_exp = pd.concat([df_rwa, df_rwa_bench], ignore_index=True)
        if not df_rwa_raw.empty:
            # Pivot raw composition for easier view
             df_rwa_pivot = df_rwa_raw.pivot_table(
                    index=['name', 'lei', 'period'], columns='label', values='amount', aggfunc='sum'
             ).reset_index()
             df_rwa_exp = pd.merge(df_rwa_exp, df_rwa_pivot, on=['name', 'lei', 'period'], how='left')
             
        csv = df_rwa_exp.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download RWA Data (CSV)", data=csv, file_name='eba_benchmarking_rwa.csv', mime='text/csv')
    else:
        st.warning("No RWA data found.")
