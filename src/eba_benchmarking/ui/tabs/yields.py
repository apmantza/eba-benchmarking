import streamlit as st
import pandas as pd
from eba_benchmarking.data import (
    get_nii_analysis, get_nii_averages
)
from eba_benchmarking.plotting import (
    plot_implied_rates, plot_peer_comparison_trend
)

def render_yields_tab(selected_leis, base_bank_name, base_country, base_size, base_region, base_sys):
    """
    Renders the Implied Yields & Funding Costs Analysis tab.
    """
    st.subheader("Implied Yields & Funding Costs Analysis")
    
    # 1. Fetch Data for ALL Peers + Base
    df_nii_all = get_nii_analysis(selected_leis)
    df_nii_avg = get_nii_averages(base_country, base_region, base_sys, base_size)
    
    # Combine for plotting (if needed by plot functions or for unified view)
    df_plot_rates = df_nii_all.copy()
    if not df_nii_avg.empty:
        df_plot_rates = pd.concat([df_plot_rates, df_nii_avg], ignore_index=True)
    
    if not df_plot_rates.empty:
        # 2. Base Bank Overview (REMOVED as per request)
        # st.markdown(f"### 🏦 {base_bank_name} Overview")
        # st.plotly_chart(plot_implied_rates(df_nii_all, base_bank_name), width='stretch')
        
        st.divider()
        
        # 3. Peer Comparison - Yields
        st.markdown("### 📈 Asset Yields Comparison")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_peer_comparison_trend(
                df_plot_rates, 'Implied Loan Yield', 
                "Implied Loan Yield (%)", base_bank_name, format_pct=True
            ), width='stretch')
        with c2:
            st.plotly_chart(plot_peer_comparison_trend(
                df_plot_rates, 'Implied Securities Yield', 
                "Implied Securities Yield (%)", base_bank_name, format_pct=True
            ), width='stretch')
            
        # 4. Peer Comparison - Costs
        st.markdown("### 📉 Funding Costs Comparison")
        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(plot_peer_comparison_trend(
                df_plot_rates, 'Implied Deposit Cost', 
                "Implied Deposit Cost (%)", base_bank_name, format_pct=True
            ), width='stretch')
        with c4:
            st.plotly_chart(plot_peer_comparison_trend(
                df_plot_rates, 'Implied Debt Cost', 
                "Implied Debt Cost (%)", base_bank_name, format_pct=True
            ), width='stretch')
            
        c5, c6 = st.columns(2)
        with c5:
            st.plotly_chart(plot_peer_comparison_trend(
                df_plot_rates, 'Implied Interbank Cost', 
                "Implied Interbank/Other Cost (%)", base_bank_name, format_pct=True
            ), width='stretch')
        with c6:
            st.plotly_chart(plot_peer_comparison_trend(
                df_plot_rates, 'Implied Funding Cost', 
                "Total Funding Cost (%)", base_bank_name, format_pct=True
            ), width='stretch')
            
        # 5. Margins (New)
        st.markdown("### 📊 Net Margins over Euribor 3M")
        
        # Row 1: Asset Yield Margins
        cm1, cm2 = st.columns(2)
        with cm1:
            st.plotly_chart(plot_peer_comparison_trend(
                df_plot_rates, 'Margin: Loan Yield', 
                "Margin: Loan Yield (vs Euribor 3M)", base_bank_name, format_pct=True
            ), width='stretch')
        with cm2:
            st.plotly_chart(plot_peer_comparison_trend(
                df_plot_rates, 'Margin: Securities Yield', 
                "Margin: Securities Yield (vs Euribor 3M)", base_bank_name, format_pct=True
            ), width='stretch')
            
        # Row 2: Liability Cost Margins
        cm3, cm4 = st.columns(2)
        with cm3:
             st.plotly_chart(plot_peer_comparison_trend(
                df_plot_rates, 'Margin: Deposit Cost', 
                "Margin: Deposit Cost (vs Euribor 3M)", base_bank_name, format_pct=True
            ), width='stretch')
        with cm4:
             st.plotly_chart(plot_peer_comparison_trend(
                df_plot_rates, 'Margin: Debt Cost', 
                "Margin: Debt Cost (vs Euribor 3M)", base_bank_name, format_pct=True
            ), width='stretch')
            
        # Row 3: Total Funding
        cm5, cm6 = st.columns(2)
        with cm5:
            st.plotly_chart(plot_peer_comparison_trend(
                df_plot_rates, 'Margin: Funding Cost', 
                "Margin: Total Funding Cost (vs Euribor 3M)", base_bank_name, format_pct=True
            ), width='stretch')
        with cm6:
             st.empty() # Placeholder for balance
            
        # Download
        st.markdown("### 📥 Download Rates Dataset")
        csv = df_plot_rates.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Rates Data (CSV)", data=csv, file_name='eba_benchmarking_yields_funding.csv', mime='text/csv')
        
    else:
        st.warning("No data available for yields analysis.")
