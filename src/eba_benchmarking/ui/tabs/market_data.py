import streamlit as st
import pandas as pd
from eba_benchmarking.data import get_market_data, get_market_history
from eba_benchmarking.plotting import plot_benchmark_bar, plot_market_history

def render_market_data_tab(selected_leis, base_bank_name):
    """
    Renders the Market Data tab (Yahoo Finance integration).
    """
    st.subheader("📈 Market Data (Yahoo Finance)")
    
    # Fetch market data
    df_market = get_market_data(selected_leis)
    
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
            c6.metric("52W High", f"€{base_mkt.get('week_52_high', 0):.2f}" if pd.notna(base_mkt.get('week_52_high')) else "N/A")
            c7.metric("52W Low", f"€{base_mkt.get('week_52_low', 0):.2f}" if pd.notna(base_mkt.get('week_52_low')) else "N/A")
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
            if not df_pb.empty:
                st.plotly_chart(plot_benchmark_bar(df_pb, 'price_to_book', "Price-to-Book Ratio", base_bank_name, format_pct=False, scale_amounts=False), width='stretch', key='mkt_pb')
        
        with col2:
            df_pe = df_market[['name', 'pe_trailing']].dropna().copy()
            if not df_pe.empty:
                st.plotly_chart(plot_benchmark_bar(df_pe, 'pe_trailing', "P/E Ratio (Trailing)", base_bank_name, format_pct=False, scale_amounts=False), width='stretch', key='mkt_pe')
        
        # Market Cap & Dividend
        col3, col4 = st.columns(2)
        with col3:
            df_mcap = df_market[['name', 'market_cap']].dropna().copy()
            df_mcap['market_cap_B'] = df_mcap['market_cap'] / 1e9
            if not df_mcap.empty:
                st.plotly_chart(plot_benchmark_bar(df_mcap, 'market_cap_B', "Market Cap (€B)", base_bank_name, format_pct=False, scale_amounts=False), width='stretch', key='mkt_cap')
        
        with col4:
            df_div = df_market[['name', 'dividend_yield']].dropna().copy()
            if not df_div.empty:
                st.plotly_chart(plot_benchmark_bar(df_div, 'dividend_yield', "Dividend Yield", base_bank_name, format_pct=True), width='stretch', key='mkt_div')
        
        # Risk Metrics
        st.markdown("### ⚠️ Risk & Performance")
        col5, col6 = st.columns(2)
        with col5:
            df_beta = df_market[['name', 'beta']].dropna().copy()
            if not df_beta.empty:
                st.plotly_chart(plot_benchmark_bar(df_beta, 'beta', "Beta (Systematic Risk)", base_bank_name, format_pct=False, scale_amounts=False), width='stretch', key='mkt_beta')
        
        with col6:
            df_ret = df_market[['name', 'return_1y']].dropna().copy()
            if not df_ret.empty:
                st.plotly_chart(plot_benchmark_bar(df_ret, 'return_1y', "1-Year Return", base_bank_name, format_pct=True), width='stretch', key='mkt_1y')
        
        # Analyst Target
        st.markdown("### 🎯 Analyst Targets")
        col7, col8 = st.columns(2)
        with col7:
            # Target Price vs Current
            df_target = df_market[df_market['target_mean'].notna()][['name', 'current_price', 'target_mean']].copy()
            if not df_target.empty:
                df_target['Upside (%)'] = (df_target['target_mean'] - df_target['current_price']) / df_target['current_price']
                st.plotly_chart(plot_benchmark_bar(df_target, 'Upside (%)', "Analyst Target Upside (%)", base_bank_name, format_pct=True), width='stretch', key='mkt_upside')
        
        with col8:
            # Number of analysts
            df_analysts = df_market[['name', 'num_analysts']].dropna().copy()
            if not df_analysts.empty:
                st.plotly_chart(plot_benchmark_bar(df_analysts, 'num_analysts', "# of Covering Analysts", base_bank_name, format_pct=False, scale_amounts=False), width='stretch', key='mkt_analysts')
        
        # Historical Trends Section
        st.divider()
        st.markdown("### 📈 Historical Trends (5-Year)")
        
        # Fetch historical data
        df_history = get_market_history(selected_leis)
        
        if not df_history.empty:
            col_h1, col_h2 = st.columns(2)
            
            with col_h1:
                # Stock Price Trend
                st.plotly_chart(
                    plot_market_history(df_history, 'close', "Stock Price (€)", base_bank_name, format_pct=False),
                    use_container_width=True, key='mkt_hist_price'
                )
            
            with col_h2:
                # Dividend Yield Trend
                st.plotly_chart(
                    plot_market_history(df_history, 'dividend_yield', "Trailing Dividend Yield", base_bank_name, format_pct=True),
                    use_container_width=True, key='mkt_hist_divyield'
                )
            
            # Market Cap Trend (if available)
            df_hist_mcap = df_history[df_history['market_cap'].notna()]
            if not df_hist_mcap.empty:
                col_h3, col_h4 = st.columns(2)
                with col_h3:
                    # Convert to billions for readability
                    df_hist_mcap_plot = df_hist_mcap.copy()
                    df_hist_mcap_plot['market_cap_B'] = df_hist_mcap_plot['market_cap'] / 1e9
                    st.plotly_chart(
                        plot_market_history(df_hist_mcap_plot, 'market_cap_B', "Market Cap (€B)", base_bank_name, format_pct=False),
                        use_container_width=True, key='mkt_hist_mcap'
                    )
                with col_h4:
                    st.empty()
        else:
            st.info("Historical data not available. Run `python scripts/refresh_market_data.py --history` to fetch.")
        
        # Full Data Table
        with st.expander("📋 View Full Market Data"):
            display_cols = ['name', 'ticker', 'current_price', 'market_cap', 'pe_trailing', 'price_to_book', 
                          'dividend_yield', 'beta', 'ytd_return', 'return_1y', 'target_mean', 'recommendation']
            df_display = df_market[[c for c in display_cols if c in df_market.columns]].copy()
            st.dataframe(df_display, use_container_width=True)
        
        # Download
        st.markdown("### 📥 Download Market Data")
        csv = df_market.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Market Data (CSV)", data=csv, file_name='eba_benchmarking_market_data.csv', mime='text/csv')
        
    else:
        st.warning("No market data available. Run `python scripts/refresh_market_data.py` to fetch data.")
        st.info("Note: Only publicly traded banks with configured tickers have market data.")
