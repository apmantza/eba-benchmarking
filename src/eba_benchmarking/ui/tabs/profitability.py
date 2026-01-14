import streamlit as st
import pandas as pd
from eba_benchmarking.data import (
    get_profitability_kpis, get_profitability_averages,
    get_nii_analysis, get_eba_kris
)
from eba_benchmarking.plotting import (
    plot_benchmark_bar, plot_solvency_trend,
    plot_operating_income_composition_percent, plot_non_interest_income_trend,
    plot_nii_evolution, plot_nii_structure_snapshot,
    plot_component_share_trend, plot_pl_waterfall_granular,
    plot_pl_waterfall_yoy, plot_pl_evolution_trend
)

def render_profitability_tab(selected_leis, base_bank_name, base_country, base_size, base_lei, base_region, base_sys):
    """
    Renders the Profitability & Efficiency tab.
    """
    st.subheader("Profitability & Efficiency")
    
    # 1. Fetch Data
    df_prof = get_profitability_kpis(selected_leis)
    df_prof_bench = get_profitability_averages(base_country, base_region, base_sys, base_size)
    df_eu_kris = get_eba_kris(base_country) # Can use Cost-to-Income / RoE kris here if available
    
    # Calculate Jaws (YoY Income Growth - YoY Expense Growth)
    if not df_prof.empty:
        # Sort and Calc
        df_prof = df_prof.sort_values(['name', 'period'])
        df_prof['OpInc Growth'] = df_prof.groupby('name')['Total Operating Income'].pct_change(periods=4) # Assuming quarterly 
        df_prof['OpExp Growth'] = df_prof.groupby('name')['Admin Expenses'].pct_change(periods=4) # Proxy using Admin Exp
        df_prof['Jaws Ratio'] = df_prof['OpInc Growth'] - df_prof['OpExp Growth']
    
    if not df_prof.empty:
        latest_prof = df_prof['period'].max()
        # Calculate Jaws for Benchmarks too if possible?
        # get_profitability_averages might not have all raw components over time to fast calc Jaws.
        # But if it has accumulated OpInc and AdminExp, we can calc growth.
        # Assuming df_prof_bench has similar structure.
        if not df_prof_bench.empty:
             df_prof_bench = df_prof_bench.sort_values(['name', 'period'])
             # Assuming we can group by name (which are 'Aggregate' names)
             df_prof_bench['OpInc Growth'] = df_prof_bench.groupby('name')['Total Operating Income'].pct_change(periods=4)
             df_prof_bench['OpExp Growth'] = df_prof_bench.groupby('name')['Admin Expenses'].pct_change(periods=4)
             df_prof_bench['Jaws Ratio'] = df_prof_bench['OpInc Growth'] - df_prof_bench['OpExp Growth']

        latest_prof = df_prof['period'].max()
        df_p_lat = df_prof[df_prof['period'] == latest_prof].copy()
        df_pb_lat = df_prof_bench[df_prof_bench['period'] == latest_prof] if not df_prof_bench.empty else None
        
        # 2. Summary Metrics for Base Bank
        base_prof_lat = df_p_lat[df_p_lat['name'] == base_bank_name].iloc[0] if not df_p_lat[df_p_lat['name'] == base_bank_name].empty else None
        
        if base_prof_lat is not None:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("RoE (Annualized)", f"{base_prof_lat['RoE (Annualized)']:.1%}")
            c2.metric("RoA (Annualized)", f"{base_prof_lat['RoA (Annualized)']:.2%}")
            c3.metric("RoRWA (Annualized)", f"{base_prof_lat.get('RoRWA (Annualized)', 0):.2%}")
            c4.metric("Cost-to-Income", f"{base_prof_lat['Cost to Income']:.1%}")
            st.divider()

        # 3. Row 1: Return on Equity (RoE) - Annualized
        st.markdown("### 💸 Return on Equity (RoE) - Annualized")
        c1, c2 = st.columns(2)
        with c1:
            df_roe = df_p_lat[['name', 'RoE (Annualized)']].copy()
            if df_pb_lat is not None:
                df_roe = pd.concat([df_roe, df_pb_lat[['name', 'RoE (Annualized)']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_roe, 'RoE (Annualized)', "RoE Annualized (Latest)", base_bank_name, format_pct=True), width='stretch')
        with c2:
            st.plotly_chart(plot_solvency_trend(df_prof, df_prof_bench, 'RoE (Annualized)', "RoE Annualized Trend", base_bank_name, df_eu_kris), width='stretch')

        # 4. Row 2: Return on Assets (RoA) - Annualized
        st.markdown("### 🏦 Return on Assets (RoA) - Annualized")
        c3, c4 = st.columns(2)
        with c3:
            df_roa = df_p_lat[['name', 'RoA (Annualized)']].copy()
            if df_pb_lat is not None:
                df_roa = pd.concat([df_roa, df_pb_lat[['name', 'RoA (Annualized)']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_roa, 'RoA (Annualized)', "RoA Annualized (Latest)", base_bank_name, format_pct=True), width='stretch')
        with c4:
            st.plotly_chart(plot_solvency_trend(df_prof, df_prof_bench, 'RoA (Annualized)', "RoA Annualized Trend", base_bank_name, df_eu_kris), width='stretch')

        # 4b. Row 2b: Return on RWA (RoRWA) - Annualized
        st.markdown("### ⚖️ Return on RWA (RoRWA) - Annualized")
        c_rwa1, c_rwa2 = st.columns(2)
        with c_rwa1:
            df_rorwa = df_p_lat[['name', 'RoRWA (Annualized)']].copy()
            if df_pb_lat is not None and 'RoRWA (Annualized)' in df_pb_lat.columns:
                df_rorwa = pd.concat([df_rorwa, df_pb_lat[['name', 'RoRWA (Annualized)']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_rorwa, 'RoRWA (Annualized)', "RoRWA Annualized (Latest)", base_bank_name, format_pct=True), width='stretch')
        with c_rwa2:
            st.plotly_chart(plot_solvency_trend(df_prof, df_prof_bench, 'RoRWA (Annualized)', "RoRWA Annualized Trend", base_bank_name), width='stretch')

        # 5. Row 3: Efficiency & Asset Productivity
        st.markdown("### ⚙️ Efficiency & Asset Productivity")
        c5, c6 = st.columns(2)
        with c5:
            # Cost to Income Plot
            df_cir = df_p_lat[['name', 'Cost to Income']].copy()
            if df_pb_lat is not None:
                df_cir = pd.concat([df_cir, df_pb_lat[['name', 'Cost to Income']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_cir, 'Cost to Income', "Cost-to-Income Ratio (Latest)", base_bank_name, format_pct=True), width='stretch')
        with c6:
            # Cost to Income Trend
            st.plotly_chart(plot_solvency_trend(df_prof, df_prof_bench, 'Cost to Income', "Cost-to-Income Trend", base_bank_name, df_eu_kris), width='stretch')
        
        c_fee1, c_fee2 = st.columns(2)
        with c_fee1:
            # Net Fees / Assets Plot
            df_fees = df_p_lat[['name', 'Net Fees / Assets (Annualized)']].copy()
            if df_pb_lat is not None:
                df_fees = pd.concat([df_fees, df_pb_lat[['name', 'Net Fees / Assets (Annualized)']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_fees, 'Net Fees / Assets (Annualized)', "Net Fees / Assets (Annualized)", base_bank_name, format_pct=True), width='stretch')
        with c_fee2:
            # Net Fees / Assets Trend
            st.plotly_chart(plot_solvency_trend(df_prof, df_prof_bench, 'Net Fees / Assets (Annualized)', "Net Fees / Assets Trend", base_bank_name), width='stretch')

        # Jaws Ratio as last plot
        st.markdown("### 📈 Operational Leverage (Jaws)")
        st.plotly_chart(plot_solvency_trend(df_prof, df_prof_bench, 'Jaws Ratio', "Jaws Ratio (YoY Income vs Exp Growth)", base_bank_name), width='stretch')

        # 6. Row 4: Risk Cost
        st.markdown("### 🛡️ Cost of Risk")
        c_r1, c_r2 = st.columns(2)
        with c_r1:
            # Cost of Risk Bar
            df_cor = df_p_lat[['name', 'Cost of Risk (Annualized)']].copy()
            if df_pb_lat is not None:
                df_cor = pd.concat([df_cor, df_pb_lat[['name', 'Cost of Risk (Annualized)']]], ignore_index=True)
            st.plotly_chart(plot_benchmark_bar(df_cor, 'Cost of Risk (Annualized)', "Cost of Risk (Annualized)", base_bank_name, format_pct=True), width='stretch')
        with c_r2:
            # Cost of Risk Trend
            st.plotly_chart(plot_solvency_trend(df_prof, df_prof_bench, 'Cost of Risk (Annualized)', "Cost of Risk Trend (Annualized)", base_bank_name, df_eu_kris), width='stretch')


        # Removed NII analysis, Profit Driver Analysis and Historical P&L Evolution as per request
        
        # 2. Interest Income Structure (Snapshot only)
        # st.markdown("#### Interest Income Composition") ...
        # If we remove "NII analysis", do we remove structure snapshots too? 
        # Request: "remove the NII analysis. remove the profit driver analysis and the historical p&l evolution."
        # Assuming removing the whole blocks.
        
        # Row 7: Operating Income Structure - keep? Yes, unrelated to NII analysis block specific.
        
        # 10. Download
        st.markdown("### 📥 Download Profitability Dataset")
        df_exp = pd.concat([df_prof, df_prof_bench], ignore_index=True)
        csv = df_exp.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Profitability Data (CSV)", data=csv, file_name='eba_benchmarking_profitability.csv', mime='text/csv')
    else:
        st.warning("No profitability data found.")
