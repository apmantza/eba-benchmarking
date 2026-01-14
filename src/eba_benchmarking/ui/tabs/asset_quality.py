import streamlit as st
import pandas as pd
from eba_benchmarking.data import (
    get_financial_data, get_asset_quality_averages,
    get_eba_kris, get_aq_breakdown, get_aq_breakdown_averages
)
from eba_benchmarking.plotting import (
    plot_benchmark_bar, plot_solvency_trend
)

def render_asset_quality_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys):
    """
    Renders the Asset Quality tab.
    """
    st.subheader("Asset Quality Analysis")
    
    # Fetch Data
    df_std = get_financial_data(selected_leis)
    df_aq_bench = get_asset_quality_averages(base_country, base_region, base_sys, base_size)
    df_eu_kris = get_eba_kris(base_country)
    
    if not df_std.empty:
        latest = df_std['period'].max()
        
        # Highlights
        base_aq_lat = df_std[df_std['name'] == base_bank_name].sort_values('period').iloc[-1] if not df_std[df_std['name'] == base_bank_name].empty else None
        
        # Need Stage 2 / 3 data for highlights which is in df_aq_bk
        df_aq_bk = get_aq_breakdown(selected_leis)
        base_aq_bk_lat = None
        if not df_aq_bk.empty:
             base_aq_sorted = df_aq_bk[df_aq_bk['name'] == base_bank_name].sort_values('period')
             if not base_aq_sorted.empty:
                base_aq_bk_lat = base_aq_sorted.iloc[-1]
        
        if base_aq_lat is not None:
             c1, c2, c3, c4 = st.columns(4)
             c1.metric("NPL Ratio", f"{base_aq_lat['npl_ratio']:.1%}")
             
             if base_aq_bk_lat is not None:
                 c2.metric("Stage 3 Coverage", f"{base_aq_bk_lat.get('Stage 3 Coverage', 0):.1%}")
                 c3.metric("Stage 2 Ratio", f"{base_aq_bk_lat.get('Stage 2 Ratio', 0):.1%}")
                 c4.metric("Forborne Ratio", f"{base_aq_bk_lat.get('Forborne Ratio', 0):.1%}")
             else:
                 c2.metric("Stage 3 Coverage", "-")
                 c3.metric("Stage 2 Ratio", "-")
                 c4.metric("Forborne Ratio", "-")
             st.divider()

        # Row 1: NPL Ratio
        st.markdown("### ☣️ NPL Ratio")
        c1, c2 = st.columns(2)
        with c1:
            # Prepare latest data including averages
            df_aq_latest = df_std[df_std['period'] == latest].copy()
            df_aq_bench_latest = df_aq_bench[df_aq_bench['period'] == latest] if not df_aq_bench.empty else None
            
            df_npl_bar = df_aq_latest[['name', 'npl_ratio']].copy()
            if df_aq_bench_latest is not None:
                df_npl_bar = pd.concat([df_npl_bar, df_aq_bench_latest[['name', 'npl_ratio']]], ignore_index=True)
            
            st.plotly_chart(plot_benchmark_bar(df_npl_bar, 'npl_ratio', "NPL Ratio (Latest)", base_bank_name, format_pct=True), width='stretch')
        with c2:
            # Use solvency trend plotter for consistency
            st.plotly_chart(plot_solvency_trend(df_std, df_aq_bench, 'npl_ratio', "NPL Ratio Trend", base_bank_name, df_eu_kris), width='stretch')
            
        # Row 2: Coverage Ratios
        st.markdown("### 🛡️ Coverage Ratios (Prudence)")
        # df_aq_bk fetched above for highlights
        df_aq_bk_avg = get_aq_breakdown_averages(base_country, base_region, base_sys, base_size)
        
        if not df_aq_bk.empty:
            df_aq_bk_lat = df_aq_bk[df_aq_bk['period'] == latest].copy()
            # Prepare latest benchmarks for breakdown
            df_aq_bk_bench_lat = df_aq_bk_avg[df_aq_bk_avg['period'] == latest] if not df_aq_bk_avg.empty else None
            
            # Stage 3 Coverage
            c3, c4 = st.columns(2)
            with c3:
                # Add benchmarks
                df_cov3_lat = df_aq_bk_lat[['name', 'Stage 3 Coverage']].copy()
                if df_aq_bk_bench_lat is not None and 'Stage 3 Coverage' in df_aq_bk_bench_lat.columns:
                     df_cov3_lat = pd.concat([df_cov3_lat, df_aq_bk_bench_lat[['name', 'Stage 3 Coverage']]], ignore_index=True)
                st.plotly_chart(plot_benchmark_bar(df_cov3_lat, 'Stage 3 Coverage', "Stage 3 (NPL) Coverage (Latest)", base_bank_name, format_pct=True), width='stretch')
            with c4:
                st.plotly_chart(plot_solvency_trend(df_aq_bk, df_aq_bk_avg, 'Stage 3 Coverage', "Stage 3 Coverage Trend", base_bank_name), width='stretch')

            # Stage 2 Coverage
            c5, c6 = st.columns(2)
            with c5:
                # Add benchmarks
                df_cov_lat = df_aq_bk_lat[['name', 'Stage 2 Coverage']].copy()
                if df_aq_bk_bench_lat is not None and 'Stage 2 Coverage' in df_aq_bk_bench_lat.columns:
                     df_cov_lat = pd.concat([df_cov_lat, df_aq_bk_bench_lat[['name', 'Stage 2 Coverage']]], ignore_index=True)
                st.plotly_chart(plot_benchmark_bar(df_cov_lat, 'Stage 2 Coverage', "Stage 2 Coverage (Latest)", base_bank_name, format_pct=True), width='stretch')
            with c6:
                st.plotly_chart(plot_solvency_trend(df_aq_bk, df_aq_bk_avg, 'Stage 2 Coverage', "Stage 2 Coverage Trend", base_bank_name), width='stretch')
            
            # Stage 2 Ratio Analysis
            st.markdown("### ⚠️ Sell-Side: Stage 2 Ratio Analysis (Leading Risk Indicator)")
            c_s2_1, c_s2_2 = st.columns(2)
            with c_s2_1:
                 # Bar Chart for Latest Stage 2
                 df_s2_lat = df_aq_bk_lat[['name', 'Stage 2 Ratio']].copy()
                 if df_aq_bk_bench_lat is not None and 'Stage 2 Ratio' in df_aq_bk_bench_lat.columns:
                     df_s2_lat = pd.concat([df_s2_lat, df_aq_bk_bench_lat[['name', 'Stage 2 Ratio']]], ignore_index=True)
                 st.plotly_chart(plot_benchmark_bar(df_s2_lat, 'Stage 2 Ratio', "Stage 2 Ratio (Latest)", base_bank_name, format_pct=True), width='stretch')
            with c_s2_2:
                 # Trend
                 st.plotly_chart(plot_solvency_trend(df_aq_bk, df_aq_bk_avg, 'Stage 2 Ratio', "Stage 2 Ratio Trend (~SICR)", base_bank_name), width='stretch')

            # Forborne Ratio (Early Warning)
            if 'Forborne Ratio' in df_aq_bk.columns:
                st.markdown("### 🔄 Forborne Ratio (Restructured Loans)")
                # Removed info note
                c_fb1, c_fb2 = st.columns(2)
                with c_fb1:
                    df_fb_lat = df_aq_bk_lat[['name', 'Forborne Ratio']].copy()
                    if df_aq_bk_bench_lat is not None and 'Forborne Ratio' in df_aq_bk_bench_lat.columns:
                         df_fb_lat = pd.concat([df_fb_lat, df_aq_bk_bench_lat[['name', 'Forborne Ratio']]], ignore_index=True)
                    st.plotly_chart(plot_benchmark_bar(df_fb_lat, 'Forborne Ratio', "Forborne Ratio (Latest)", base_bank_name, format_pct=True), width='stretch', key='aq_forborne_bar')
                with c_fb2:
                    st.plotly_chart(plot_solvency_trend(df_aq_bk, df_aq_bk_avg, 'Forborne Ratio', "Forborne Ratio Trend", base_bank_name), width='stretch', key='aq_forborne_trend')
            
            # Write-off Rate REMOVED

        # Download
        st.markdown("### 📥 Download Asset Quality Dataset")
        # Combine bank data, averages and EU baseline
        df_aq_exp = pd.concat([df_std[['name', 'lei', 'period', 'npl_ratio']], df_aq_bench], ignore_index=True)
        if not df_aq_bk.empty:
            df_aq_exp = pd.merge(df_aq_exp, df_aq_bk, on=['name', 'lei', 'period'], how='left')
            
        csv = df_aq_exp.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full Asset Quality Data (CSV)", data=csv, file_name='eba_benchmarking_asset_quality.csv', mime='text/csv')
    else:
        st.warning("No asset quality data found.")
