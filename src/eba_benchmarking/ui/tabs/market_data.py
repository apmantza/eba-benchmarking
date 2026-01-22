import streamlit as st
import pandas as pd
from eba_benchmarking.data import (
    get_market_data, get_market_history, get_market_financial_years,
    get_market_benchmarking_stats, get_market_fy_averages
)
from eba_benchmarking.plotting import plot_benchmark_bar, plot_market_history

def render_market_data_tab(selected_leis, base_bank_name, base_country, base_region, base_size):
    """
    Renders the Market Data tab (Yahoo Finance integration) with peer benchmarking.
    """
    st.subheader("📈 Market Data (Yahoo Finance)")
    
    # Fetch market data
    df_market = get_market_data(selected_leis)
    df_mkt_bench = get_market_benchmarking_stats(base_country, base_region, base_size)
    
    if not df_market.empty:
        # Filter to base bank for KPIs
        df_base_mkt = df_market[df_market['name'] == base_bank_name]
        
        if not df_base_mkt.empty:
            base_mkt = df_base_mkt.iloc[0]
            
            # Summary KPIs
            st.markdown(f"### 💹 {base_bank_name} Market Snapshot")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Stock Price", f"€{base_mkt.get('current_price', 0):.2f}" if pd.notna(base_mkt.get('current_price')) else "N/A")
            c2.metric("Market Cap", f"€{base_mkt.get('market_cap', 0)/1e9:.1f}B" if pd.notna(base_mkt.get('market_cap')) else "N/A")
            c3.metric("P/B Ratio", f"{base_mkt.get('price_to_book', 0):.2f}" if pd.notna(base_mkt.get('price_to_book')) else "N/A")
            c4.metric("P/E Ratio", f"{base_mkt.get('pe_trailing', 0):.1f}" if pd.notna(base_mkt.get('pe_trailing')) else "N/A")
            c5.metric("Dividend Yield", f"{base_mkt.get('dividend_yield', 0)*100:.2f}%" if pd.notna(base_mkt.get('dividend_yield')) else "N/A")
            
            c6, c7, c8, c9, c10 = st.columns(5)
            c6.metric("Buyback Yield", f"{base_mkt.get('buyback_yield', 0)*100:.2f}%" if pd.notna(base_mkt.get('buyback_yield')) else "N/A")
            c7.metric("Payout Yield", f"{base_mkt.get('payout_yield', 0)*100:.2f}%" if pd.notna(base_mkt.get('payout_yield')) else "N/A")
            c8.metric("Beta", f"{base_mkt.get('beta', 0):.2f}" if pd.notna(base_mkt.get('beta')) else "N/A")
            c9.metric("YTD Return", f"{base_mkt.get('ytd_return', 0)*100:.1f}%" if pd.notna(base_mkt.get('ytd_return')) else "N/A")
            c10.metric("Recommendation", base_mkt.get('recommendation', 'N/A').upper() if pd.notna(base_mkt.get('recommendation')) else "N/A")

            st.divider()
        
        # Valuation Comparison
        st.markdown("### 📊 Valuation Metrics Comparison")
        
        # P/B Ratio Chart
        col1, col2 = st.columns(2)
        with col1:
            df_pb = df_market[['name', 'price_to_book']].dropna().copy()
            if not df_mkt_bench.empty:
                df_pb = pd.concat([df_pb, df_mkt_bench[['name', 'price_to_book']].dropna()], ignore_index=True)
            if not df_pb.empty:
                st.plotly_chart(plot_benchmark_bar(df_pb, 'price_to_book', "Price-to-Book Ratio", base_bank_name, format_pct=False, scale_amounts=False), width='stretch', key='mkt_pb')
        
        with col2:
            df_pe = df_market[['name', 'pe_trailing']].dropna().copy()
            if not df_mkt_bench.empty:
                df_pe = pd.concat([df_pe, df_mkt_bench[['name', 'pe_trailing']].dropna()], ignore_index=True)
            if not df_pe.empty:
                st.plotly_chart(plot_benchmark_bar(df_pe, 'pe_trailing', "P/E Ratio (Trailing)", base_bank_name, format_pct=False, scale_amounts=False), width='stretch', key='mkt_pe')
        
        # Market Cap Comparison
        col3, col4 = st.columns(2)
        with col3:
            df_mcap = df_market[['name', 'market_cap']].dropna().copy()
            df_mcap['market_cap_B'] = df_mcap['market_cap'] / 1e9
            # Market Cap benchmarking might not be meaningful as group average, but keeping for consistency
            if not df_mkt_bench.empty:
                df_mcap_b = df_mkt_bench[['name', 'market_cap']].dropna().copy()
                df_mcap_b['market_cap_B'] = df_mcap_b['market_cap'] / 1e9
                df_mcap = pd.concat([df_mcap, df_mcap_b], ignore_index=True)
            if not df_mcap.empty:
                st.plotly_chart(plot_benchmark_bar(df_mcap, 'market_cap_B', "Market Cap (€B)", base_bank_name, format_pct=False, scale_amounts=False), width='stretch', key='mkt_cap')
        
        with col4:
            st.empty() # Placeholder for balance
        
        # Shareholder Returns (Trailing 12m)
        st.markdown("### 💰 Shareholder Returns (Trailing 12m)")
        
        col_sr1, col_sr2 = st.columns(2)
        with col_sr1:
            df_div = df_market[['name', 'dividend_yield']].dropna().copy()
            if not df_mkt_bench.empty:
                df_div = pd.concat([df_div, df_mkt_bench[['name', 'dividend_yield']].dropna()], ignore_index=True)
            if not df_div.empty:
                st.plotly_chart(plot_benchmark_bar(df_div, 'dividend_yield', "Dividend Yield (Trailing 12m)", base_bank_name, format_pct=True), width='stretch', key='mkt_div_sr')
        
        with col_sr2:
            df_buyback = df_market[['name', 'buyback_yield']].dropna().copy()
            if not df_mkt_bench.empty:
                df_buyback = pd.concat([df_buyback, df_mkt_bench[['name', 'buyback_yield']].dropna()], ignore_index=True)
            if not df_buyback.empty and df_buyback['buyback_yield'].sum() > 0:
                st.plotly_chart(plot_benchmark_bar(df_buyback, 'buyback_yield', "Buyback Yield (Trailing 12m)", base_bank_name, format_pct=True), width='stretch', key='mkt_buyback_sr')
            
        col_sr3, col_sr4 = st.columns(2)
        with col_sr3:
            df_payout = df_market[['name', 'payout_yield']].dropna().copy()
            if not df_mkt_bench.empty:
                df_payout = pd.concat([df_payout, df_mkt_bench[['name', 'payout_yield']].dropna()], ignore_index=True)
            if not df_payout.empty and df_payout['payout_yield'].sum() > 0:
                st.plotly_chart(plot_benchmark_bar(df_payout, 'payout_yield', "Total Payout Yield (Trailing 12m)", base_bank_name, format_pct=True), width='stretch', key='mkt_payout_sr')
        with col_sr4:
             st.empty() # Placeholder

        # EPS and DPS Plots
        col_eps, col_dps = st.columns(2)
        with col_eps:
            df_eps = df_market[['name', 'eps_trailing']].dropna().copy()
            if not df_mkt_bench.empty:
                df_eps = pd.concat([df_eps, df_mkt_bench[['name', 'eps_trailing']].dropna()], ignore_index=True)
            if not df_eps.empty:
                st.plotly_chart(plot_benchmark_bar(df_eps, 'eps_trailing', "EPS (Trailing 12m)", base_bank_name, format_pct=False, scale_amounts=False), width='stretch', key='mkt_eps_sr')
        with col_dps:
            df_dps = df_market[['name', 'dps_trailing']].dropna().copy()
            if not df_mkt_bench.empty:
                df_dps = pd.concat([df_dps, df_mkt_bench[['name', 'dps_trailing']].dropna()], ignore_index=True)
            if not df_dps.empty:
                st.plotly_chart(plot_benchmark_bar(df_dps, 'dps_trailing', "DPS (Trailing 12m)", base_bank_name, format_pct=False, scale_amounts=False), width='stretch', key='mkt_dps_sr')

        # Risk Metrics
        st.markdown("### ⚠️ Risk & Performance")
        col5, col6 = st.columns(2)
        with col5:
            df_beta = df_market[['name', 'beta']].dropna().copy()
            if not df_mkt_bench.empty:
                df_beta = pd.concat([df_beta, df_mkt_bench[['name', 'beta']].dropna()], ignore_index=True)
            if not df_beta.empty:
                st.plotly_chart(plot_benchmark_bar(df_beta, 'beta', "Beta (Systematic Risk)", base_bank_name, format_pct=False, scale_amounts=False), width='stretch', key='mkt_beta')
        
        with col6:
            df_ret = df_market[['name', 'return_1y', 'return_3y', 'return_5y']].dropna(subset=['return_1y']).copy()
            # 1Y return also benchmarks
            df_ret_1y = df_ret[['name', 'return_1y']].copy()
            if not df_mkt_bench.empty:
                df_ret_1y = pd.concat([df_ret_1y, df_mkt_bench[['name', 'return_1y']].dropna()], ignore_index=True)
            if not df_ret_1y.empty:
                st.plotly_chart(plot_benchmark_bar(df_ret_1y, 'return_1y', "1-Year Return", base_bank_name, format_pct=True), width='stretch', key='mkt_perf_1y')
        
        # Long-term returns in a new row
        col7, col8 = st.columns(2)
        with col7:
             if not df_ret.empty and 'return_3y' in df_ret.columns:
                 df_ret_3y = df_ret[['name', 'return_3y']].copy()
                 if not df_mkt_bench.empty:
                     df_ret_3y = pd.concat([df_ret_3y, df_mkt_bench[['name', 'return_3y']].dropna()], ignore_index=True)
                 st.plotly_chart(plot_benchmark_bar(df_ret_3y, 'return_3y', "3-Year Return", base_bank_name, format_pct=True), width='stretch', key='mkt_perf_3y')
        with col8:
             if not df_ret.empty and 'return_5y' in df_ret.columns:
                 df_ret_5y = df_ret[['name', 'return_5y']].copy()
                 if not df_mkt_bench.empty:
                     df_ret_5y = pd.concat([df_ret_5y, df_mkt_bench[['name', 'return_5y']].dropna()], ignore_index=True)
                 st.plotly_chart(plot_benchmark_bar(df_ret_5y, 'return_5y', "5-Year Return", base_bank_name, format_pct=True), width='stretch', key='mkt_perf_5y')
        
        st.divider()

        # Financial Year (Strategic) Analysis
        st.markdown("### 🏛️ Strategic Financial Year (FY) Analysis")
        st.caption("Yields attributed to the year profits were earned (Interim + Final + Execution Lag Adjustments)")
        
        df_fy = get_market_financial_years(selected_leis)
        df_fy_bench = get_market_fy_averages(base_country, base_region, base_size)
        
        if not df_fy.empty:
            def get_fy_pivot(df, val_col, bench_df=None):
                if bench_df is not None and not bench_df.empty:
                    # Combine bank data with benchmark averages
                    df_combined = pd.concat([df[['fy', 'name', val_col]], bench_df[['fy', 'name', val_col]]], ignore_index=True)
                else:
                    df_combined = df
                pivot = df_combined.pivot(index='fy', columns='name', values=val_col)
                pivot = pivot.sort_index(ascending=False)
                return pivot

            tab_fy1, tab_fy2, tab_fy3, tab_fy4 = st.tabs(["📊 Yields (FY)", "📈 Payout Ratio (FY)", "🪙 Per Share & EY (FY)", "💰 Absolutes (FY)"])
            
            with tab_fy1:
                st.write("**Total Strategic Yield (%)**")
                st.dataframe(get_fy_pivot(df_fy, 'total_yield_fy', df_fy_bench).style.format("{:.2%}"), use_container_width=True)
                st.write("**Dividend Yield (FY)**")
                st.dataframe(get_fy_pivot(df_fy, 'dividend_yield_fy', df_fy_bench).style.format("{:.2%}"), use_container_width=True)
                st.write("**Buyback Yield (FY)**")
                st.dataframe(get_fy_pivot(df_fy, 'buyback_yield_fy', df_fy_bench).style.format("{:.2%}"), use_container_width=True)

            with tab_fy2:
                st.write("**Total Payout Ratio (Div + Buyback / Net Income)**")
                st.dataframe(get_fy_pivot(df_fy, 'payout_ratio_fy', df_fy_bench).style.format("{:.1%}"), use_container_width=True)
                st.write("**Dividend Payout Ratio (Div / Net Income)**")
                st.dataframe(get_fy_pivot(df_fy, 'dividend_payout_ratio_fy', df_fy_bench).style.format("{:.1%}"), use_container_width=True)
            
            with tab_fy3:
                st.write("**Earnings Yield (FY)**")
                st.dataframe(get_fy_pivot(df_fy, 'earnings_yield_fy', df_fy_bench).style.format("{:.2%}"), use_container_width=True)
                st.write("**Earnings Per Share (FY)**")
                st.dataframe(get_fy_pivot(df_fy, 'eps_fy', df_fy_bench).style.format("€{:.2f}"), use_container_width=True)
                st.write("**Dividends Per Share (FY)**")
                st.dataframe(get_fy_pivot(df_fy, 'dps_fy', df_fy_bench).style.format("€{:.2f}"), use_container_width=True)

            with tab_fy4:
                st.write("**Net Income (€M)**")
                df_fy_m = df_fy.copy()
                df_fy_m['net_income_M'] = df_fy_m['net_income'] / 1e6
                st.dataframe(get_fy_pivot(df_fy_m, 'net_income_M').style.format("{:,.0f}"), use_container_width=True)
                
                df_fy_m['dividend_amt_M'] = df_fy_m['dividend_amt'] / 1e6
                df_fy_m['buyback_amt_M'] = df_fy_m['buyback_amt'] / 1e6
                
                st.write("**Total Dividend Amount (€M)**")
                st.dataframe(get_fy_pivot(df_fy_m, 'dividend_amt_M').style.format("{:,.1f}"), use_container_width=True)
                st.write("**Total Buyback Amount (€M)**")
                st.dataframe(get_fy_pivot(df_fy_m, 'buyback_amt_M').style.format("{:,.1f}"), use_container_width=True)
        else:
            st.info("Financial Year data not yet calculated. Run history refresh to populate.")

        st.divider()

        # Historical Trends Section
        st.markdown("### 📈 Historical Trends (5-Year)")
        
        # Fetch historical data
        df_history = get_market_history(selected_leis)
        
        if not df_history.empty:
            # Helper to pivot for tables
            def get_pivot_table(df, val_col):
                pivot = df.pivot(index='date', columns='name', values=val_col)
                pivot = pivot.sort_index(ascending=False) # Recent first
                return pivot

            # 1. Stock Price & Dividend Yield
            st.markdown("#### Stock Price & Dividend Yield")
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                st.write("**Stock Price (€)**")
                st.dataframe(get_pivot_table(df_history, 'close'), use_container_width=True, height=300)
            
            with col_h2:
                st.write("**Dividend Yield**")
                div_yield_table = get_pivot_table(df_history, 'dividend_yield')
                st.dataframe(div_yield_table.style.format("{:.2%}"), use_container_width=True, height=300)
            
            # 2. Market Cap
            st.markdown("#### Market Cap (€B)")
            df_h_mcap = df_history.copy()
            df_h_mcap['market_cap_B'] = df_h_mcap['market_cap'] / 1e9
            st.dataframe(get_pivot_table(df_h_mcap, 'market_cap_B').style.format("{:.1f}"), use_container_width=True, height=300)
        else:
            st.info("Historical data not available. Run `python scripts/refresh_market_data.py --history` to fetch.")

        # Full Data Table
        with st.expander("📋 View Full Market Data"):
            display_cols = ['name', 'ticker', 'current_price', 'market_cap', 'pe_trailing', 'price_to_book',
                          'dividend_yield', 'buyback_yield', 'payout_yield', 'beta', 'ytd_return', 'return_1y',
                          'target_mean', 'recommendation']
            df_display = df_market[[c for c in display_cols if c in df_market.columns]].copy()
            st.dataframe(df_display, use_container_width=True)
        
        # Download
        st.markdown("### 📥 Download Market Data")
        csv = df_market.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Market Data (CSV)", data=csv, file_name='eba_benchmarking_market_data.csv', mime='text/csv')
        
    else:
        st.warning("No market data available. Run `python scripts/refresh_market_data.py` to fetch data.")
        st.info("Note: Only publicly traded banks with configured tickers have market data.")
