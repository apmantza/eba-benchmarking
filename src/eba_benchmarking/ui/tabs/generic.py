import streamlit as st
from eba_benchmarking.data import get_tab_data

def render_generic_tab(tab_name, selected_leis):
    """
    Renders a generic tab that displays raw category data.
    """
    st.subheader(f"{tab_name} Data")
    df_tab = get_tab_data(tab_name, selected_leis)
    
    if df_tab.empty:
        st.warning(f"No data found for {tab_name}.")
        return

    # Show full data table for the category
    latest_tab = df_tab['period'].max()
    st.info(f"Showing raw data for latest period: {latest_tab}")
    
    df_show = df_tab[df_tab['period'] == latest_tab].pivot_table(
        index=['name', 'lei'], columns='label', values='amount', aggfunc='sum'
    ).reset_index()
    
    st.dataframe(df_show, use_container_width=True)
    
    # Download
    csv = df_tab.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Download {tab_name} Data (CSV)", 
        data=csv, 
        file_name=f'eba_{tab_name.lower().replace(" ", "_")}_data.csv', 
        mime='text/csv',
        key=f"dl_{tab_name}"
    )
