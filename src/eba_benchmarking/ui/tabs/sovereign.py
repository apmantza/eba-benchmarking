import streamlit as st
import pandas as pd
from eba_benchmarking.data import (
    get_sovereign_kpis, get_sovereign_averages
)
from eba_benchmarking.plotting import (
    plot_sov_portfolios, plot_sov_portfolios_percent,
    plot_home_bias_vs_cet1, plot_home_bias_trend, plot_solvency_trend,
    plot_sov_composition, plot_sov_composition_percent
)

def render_sovereign_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys):
    """
    Renders the Sovereign Portfolio Analysis tab.
    """
    st.subheader("Sovereign Portfolio Analysis")
    df_sov = get_sovereign_kpis(selected_leis)
    df_sov_bench = get_sovereign_averages(base_country, base_region, base_sys)
    
    if not df_sov.empty:
        latest_sov = df_sov['period'].max()
        df_slat = df_sov[df_sov['period'] == latest_sov].copy()
        
        # --- SOVEREIGN KPI CARDS ---
        base_sov_latest = df_slat[df_slat['name'] == base_bank_name].copy()
        if not base_sov_latest.empty:
            total_sov_amt = base_sov_latest['amount'].sum()
            
            # Top 3 Exposures
            top_3 = base_sov_latest.groupby('country_name')['amount'].sum().sort_values(ascending=False).head(3)
            
            c_hdr = st.columns(5)
            c_hdr[0].metric("Total Sovereign Exposure", f"{total_sov_amt/1000:.1f}B")
            
            # Additional Highlight: Home Bias
            home_bias_val = base_sov_latest[base_sov_latest['country_iso'] == base_country]['amount'].sum()
            cet1_val = df_sov.loc[(df_sov['name']==base_bank_name) & (df_sov['period']==latest_sov), 'CET1 Capital'].iloc[0] if 'CET1 Capital' in df_sov.columns else 0
            
            # Check if we can get CET1 from get_solvency_kpis logic or if its already in df_sov?
            # get_sovereign_kpis might not have CET1.
            # However, plot_home_bias_vs_cet1 fetches it. It must be available.
            # Assuming 'CET1 Capital' is not in df_sov by default unless merged.
            # Let's check imports. get_solvency_kpis is not imported here.
            # But plot_home_bias_vs_cet1 uses it internally OR expects it passed.
            # Actually plot_home_bias_vs_cet1 in plotting.py calls get_solvency_kpis if column missing?
            # No, plotting functions usually take data.
            # Let's peek at plot_home_bias_vs_cet1 call in line 52. It passes df_slat.
            # If df_slat doesn't have CET1, the plot function will fail or fetch it.
            # To be safe, let's display Home Bias Ratio if available, else just Exposure to Home.
            
            # Actually, let's just show top 3 + Total. Home Bias is shown in chart below.
            # Adding Home Bias to highlight means we need to calc it here.
            # If we don't have CET1 here easily, let's just show Top 3.
            
            # The prompt says "add home bias % in the highlights".
            # I will try to calculate it or just place it if column exists.
            
            # Let's fetch CET1 just for this highlight to be precise.
            from eba_benchmarking.data import get_solvency_kpis
            df_solv_temp = get_solvency_kpis([base_sov_latest['lei'].iloc[0]])
            cet1 = 0
            if not df_solv_temp.empty:
                cet1 = df_solv_temp[df_solv_temp['period']==latest_sov]['CET1 Capital'].iloc[0]
            
            hb_ratio = (home_bias_val / cet1) if cet1 > 0 else 0
            c_hdr[1].metric(f"Home Bias ({base_country})", f"{hb_ratio:.1%}")

            for i, (ctry, amt) in enumerate(top_3.items()):
                if i+2 < 5:
                    c_hdr[i+2].metric(f"Top {i+1}: {ctry}", f"{amt/1000:.1f}B")
            st.divider()

        # Row 1: Portfolio Breakdown
        st.markdown("### 💼 Accounting Portfolio Composition")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_sov_portfolios(df_slat, base_bank_name, df_sov_bench), width='stretch')
        with c2:
            st.plotly_chart(plot_sov_portfolios_percent(df_slat, base_bank_name, df_sov_bench), width='stretch')
            
        # Row 2: Concentration & Trends
        st.markdown("### 🎯 Concentration & Exposure Trends")
        c3, c4 = st.columns(2)
        with c3:
            # Home Bias vs CET1 Snapshow (Latest)
            st.plotly_chart(plot_home_bias_vs_cet1(df_slat, base_bank_name, base_country, df_sov_bench), width='stretch')
        with c4:
            # Total Sovereign Trend
            df_port_trend = df_sov.groupby(['name', 'period'])['amount'].sum().reset_index()
            df_b_trend = df_sov_bench.groupby(['name', 'period'])['amount'].sum().reset_index()
            st.plotly_chart(plot_solvency_trend(df_port_trend, df_b_trend, 'amount', "Total Sovereign Exposure Trend", base_bank_name), width='stretch')
        
        st.markdown("### 🏠 Sell-Side: Home Bias Analysis")
        # Calc for base bank and use generic benchmarks which now support home_bias_ratio if available
        # But we need get_sovereign_averages to return home_bias_ratio. 
        # Assuming df_sov_bench has processed metrics or raw data to calculate it.
        # pass df_sov_bench to plot_home_bias_trend directly.
        
        # Removed note as per request
        st.plotly_chart(plot_home_bias_trend(df_sov, base_bank_name, base_country, df_sov_bench), width='stretch')
             
        # Row 3: Material Composition - Country
        st.markdown("---")
        st.markdown("### 🗺️ Material Country Exposures (Total Portfolio, Items >= 5%)")
        c5, c6 = st.columns(2)
        with c5:
             st.plotly_chart(plot_sov_composition(df_slat, "Country Composition (Amounts)", base_bank_name, dim='country'), width='stretch')
        with c6:
             st.plotly_chart(plot_sov_composition_percent(df_slat, "Country Composition (%)", base_bank_name, dim='country'), width='stretch')
            
        # Row 4: Material Composition - Maturity
        st.markdown("### ⏳ Material Maturity Profile (Total Portfolio, Items >= 5%)")
        c7, c8 = st.columns(2)
        with c7:
            st.plotly_chart(plot_sov_composition(df_slat, "Maturity Composition (Amounts)", base_bank_name, dim='maturity'), width='stretch')
        with c8:
             st.plotly_chart(plot_sov_composition_percent(df_slat, "Maturity Composition (%)", base_bank_name, dim='maturity'), width='stretch')
            
        # Download
        st.markdown("---")
        st.markdown("### 📥 Download Sovereign Dataset")
        st.caption("Includes granular time-series data for selected banks and benchmarks.")
        df_sov_exp = pd.concat([df_sov, df_sov_bench], ignore_index=True)
        csv = df_sov_exp.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full Sovereign Data (CSV)", data=csv, file_name='eba_benchmarking_sovereign.csv', mime='text/csv')
    else:
        st.warning("No sovereign exposure data found.")
