import streamlit as st
import pandas as pd
from eba_benchmarking.data import (
    get_liabilities_kpis, get_liabilities_averages, get_deposit_beta
)
from eba_benchmarking.plotting import (
    plot_liability_composition, plot_liability_composition_percent,
    plot_benchmark_bar, plot_solvency_trend,
    plot_deposit_beta, plot_cumulative_beta
)

def render_liabilities_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys):
    """
    Renders the Liability & Funding Analysis tab.
    """
    st.subheader("Liability & Funding Analysis")
    df_liab = get_liabilities_kpis(selected_leis)
    df_liab_bench = get_liabilities_averages(base_country, base_region, base_sys, base_size)
    
    if not df_liab.empty:
        latest_liab = df_liab['period'].max()
        df_llat = df_liab[df_liab['period'] == latest_liab].copy()
        df_lbench_lat = df_liab_bench[df_liab_bench['period'] == latest_liab] if not df_liab_bench.empty else None
        
        # Summary
        base_liab_latest = df_llat[df_llat['name'] == base_bank_name].iloc[0] if not df_llat[df_llat['name'] == base_bank_name].empty else None
        if base_liab_latest is not None:
            c_hdr = st.columns(4)
            c_hdr[0].metric("Total Equity & Liab", f"{base_liab_latest['total_eq_liab']/1000:.1f}B")
            c_hdr[1].metric("Equity", f"{base_liab_latest['equity']/1000:.1f}B")
            c_hdr[2].metric("Customer Deposit Ratio", f"{base_liab_latest['Customer Deposit Ratio']:.1%}")
            c_hdr[3].metric("Wholesale Funding Ratio", f"{base_liab_latest['Wholesale Funding Ratio']:.1%}")
            st.divider()

        # Row 1: Composition
        st.markdown("### 📊 Liability Composition")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_liability_composition(df_llat, base_bank_name, df_liab_bench), width='stretch')
        with c2:
            st.plotly_chart(plot_liability_composition_percent(df_llat, base_bank_name, df_liab_bench), width='stretch')
            
        # Row 2: Funding Mix & Trends
        st.markdown("### 📈 Funding Structure")
        c3, c4 = st.columns(2)
        with c3:
            df_mix = df_llat[['name', 'Customer Deposit Ratio']].copy()
            if df_lbench_lat is not None:
                df_mix = pd.concat([df_mix, df_lbench_lat[['name', 'Customer Deposit Ratio']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_mix, 'Customer Deposit Ratio', "Customer Deposit Ratio (Latest)", base_bank_name, format_pct=True), width='stretch')
        with c4:
            st.plotly_chart(plot_solvency_trend(df_liab, df_liab_bench, 'total_liabilities', "Total Liabilities Growth Trend", base_bank_name), width='stretch')
            
        # Row 3: Trends
        c5, c6 = st.columns(2)
        with c5:
            st.plotly_chart(plot_solvency_trend(df_liab, df_liab_bench, 'Customer Deposit Ratio', "Customer Deposit Ratio Trend", base_bank_name), width='stretch')
        with c6:
            st.plotly_chart(plot_solvency_trend(df_liab, df_liab_bench, 'Wholesale Funding Ratio', "Wholesale Funding Trend", base_bank_name), width='stretch')
        
        # Row 4: Deposit Beta Analysis (Rate Sensitivity)
        st.markdown("### 🎯 Deposit Beta Analysis (Rate Sensitivity)")
        st.caption("Deposit Beta measures how much of ECB rate changes are passed through to depositors. Beta < 1 is favorable (preserves NIM).")
        
        df_beta = get_deposit_beta(selected_leis)
        if not df_beta.empty:
            c7, c8 = st.columns(2)
            with c7:
                st.plotly_chart(plot_deposit_beta(df_beta, base_bank_name), width='stretch')
            with c8:
                st.plotly_chart(plot_cumulative_beta(df_beta, base_bank_name), width='stretch')
        else:
            st.info("Deposit Beta data requires NII analysis data and ECB base rates history.")
            
        # Download
        st.markdown("### 📥 Download Liabilities Dataset")
        df_liab_exp = pd.concat([df_liab, df_liab_bench], ignore_index=True)
        csv = df_liab_exp.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full Liabilities Data (CSV)", data=csv, file_name='eba_benchmarking_liabilities.csv', mime='text/csv', key="dl_liab_custom")
    else:
        st.warning("No liability data found.")

