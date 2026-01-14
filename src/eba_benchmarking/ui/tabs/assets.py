import streamlit as st
import pandas as pd
from eba_benchmarking.data import (
    get_assets_kpis, get_assets_averages
)
from eba_benchmarking.plotting import (
    plot_asset_composition, plot_asset_composition_percent,
    plot_benchmark_bar, plot_solvency_trend
)

def render_assets_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys):
    """
    Renders the Asset Structure Analysis tab.
    """
    st.subheader("Asset Structure Analysis")
    df_assets = get_assets_kpis(selected_leis)
    df_assets_bench = get_assets_averages(base_country, base_region, base_sys, base_size)
    
    if not df_assets.empty:
        latest_assets = df_assets['period'].max()
        df_alat = df_assets[df_assets['period'] == latest_assets].copy()
        df_abench_lat = df_assets_bench[df_assets_bench['period'] == latest_assets] if not df_assets_bench.empty else None
        
        # Summary
        base_assets_latest = df_alat[df_alat['name'] == base_bank_name].iloc[0] if not df_alat[df_alat['name'] == base_bank_name].empty else None
        if base_assets_latest is not None:
            c_hdr = st.columns(4)
            c_hdr[0].metric("Total Assets", f"{base_assets_latest['Total Assets']/1000:.1f}B")
            c_hdr[1].metric("Loans to Assets", f"{base_assets_latest['Loans to Assets']:.1%}")
            c_hdr[2].metric("Securities to Assets", f"{base_assets_latest['Securities to Assets']:.1%}")
            c_hdr[3].metric("Cash to Assets", f"{base_assets_latest['Cash to Assets']:.1%}")
            st.divider()

        # Row 1: Composition
        st.markdown("### 📊 Asset Composition")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_asset_composition(df_alat, base_bank_name, df_assets_bench), width='stretch')
        with c2:
            st.plotly_chart(plot_asset_composition_percent(df_alat, base_bank_name, df_assets_bench), width='stretch')
            
        # Row 2: Intensity & Growth
        st.markdown("### 📈 Intensity & Growth")
        c3, c4 = st.columns(2)
        with c3:
            df_intense = df_alat[['name', 'Loans to Assets']].copy()
            if df_abench_lat is not None:
                df_intense = pd.concat([df_intense, df_abench_lat[['name', 'Loans to Assets']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_intense, 'Loans to Assets', "Loans-to-Assets Ratio (Latest)", base_bank_name, format_pct=True), width='stretch')
        with c4:
            st.plotly_chart(plot_solvency_trend(df_assets, df_assets_bench, 'Loans and advances', "Loans Growth Trend", base_bank_name), width='stretch')
            
        # Row 3: Securities & Liquidity
        c5, c6 = st.columns(2)
        with c5:
            df_sec_ratio = df_alat[['name', 'Securities to Assets']].copy()
            if df_abench_lat is not None:
                df_sec_ratio = pd.concat([df_sec_ratio, df_abench_lat[['name', 'Securities to Assets']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_sec_ratio, 'Securities to Assets', "Securities-to-Assets Ratio (Latest)", base_bank_name, format_pct=True), width='stretch')
        with c6:
            st.plotly_chart(plot_solvency_trend(df_assets, df_assets_bench, 'Securities to Assets', "Securities-to-Assets Trend", base_bank_name), width='stretch')

        # Row 4: Liquidity
        c7, c8 = st.columns(2)
        with c7:
            df_liq = df_alat[['name', 'Cash to Assets']].copy()
            if df_abench_lat is not None:
                df_liq = pd.concat([df_liq, df_abench_lat[['name', 'Cash to Assets']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_liq, 'Cash to Assets', "Cash-to-Assets Ratio (Latest)", base_bank_name, format_pct=True), width='stretch')
        with c8:
            st.plotly_chart(plot_solvency_trend(df_assets, df_assets_bench, 'Cash to Assets', "Cash-to-Assets Trend", base_bank_name), width='stretch')

        # Download
        st.markdown("### 📥 Download Assets Dataset")
        df_assets_exp = pd.concat([df_assets, df_assets_bench], ignore_index=True)
        csv = df_assets_exp.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full Assets Data (CSV)", data=csv, file_name='eba_benchmarking_assets.csv', mime='text/csv', key="dl_assets_custom")
    else:
        st.warning("No asset data found.")
