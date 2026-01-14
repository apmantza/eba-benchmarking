"""
Benchmarking Dashboard UI Tab

Renders a tabular comparison report similar to the Excel template,
showing base bank metrics vs. peer group averages with percentile rankings.
"""

import streamlit as st
import pandas as pd
import io
from ...data.benchmarking import (
    get_benchmarking_report,
    get_underlying_bank_data,
    get_available_metrics_for_explorer,
    get_custom_metric_data,
    get_benchmarking_peer_groups,
    calculate_percentiles,
    BENCHMARKING_METRICS
)
import numpy as np


def format_value(val, is_ratio=True, is_amount=False):
    """Format a value for display."""
    if val is None or pd.isna(val):
        return "-"
    
    if is_amount:
        # Format as millions with 1 decimal
        return f"{val/1e6:,.1f}"
    elif is_ratio:
        # Format as percentage
        return f"{val*100:.2f}%"
    else:
        return f"{val:.2f}"



def get_percentile_color(val):
    """
    Return a color for the percentile value.
    0-33: Red
    33-66: Orange
    66-100: Green
    """
    if pd.isna(val) or isinstance(val, str):
        return None
    try:
        val = float(val)
    except:
        return None
        
    if val < 33:
        return 'background-color: #ffcdd2; color: #b71c1c' # Light Red
    elif val < 66:
        return 'background-color: #ffe0b2; color: #e65100' # Light Orange
    else:
        return 'background-color: #c8e6c9; color: #1b5e20' # Light Green


def render_benchmarking_dashboard_tab(
    base_lei, 
    base_bank_name, 
    base_country, 
    base_region, 
    base_systemic_importance,
    size_category
):
    """
    Render the Benchmarking Dashboard tab.
    """
    st.header("📊 Benchmarking Dashboard")
    
    # Get report data
    with st.spinner("Calculating benchmarking metrics..."):
        result = get_benchmarking_report(
            base_lei, 
            base_country, 
            base_region, 
            base_systemic_importance,
            size_category
        )
    
    if len(result) == 3:
        report_df, latest_period, base_name = result
    else:
        st.error("Unable to generate benchmarking report. Please check data availability.")
        return
    
    if report_df.empty:
        st.warning("No data available for benchmarking report.")
        return
    
    # Display period info
    st.caption(f"**Period:** {latest_period} | **Base Bank:** {base_bank_name} | **Size:** {size_category}")
    
    # Build and display the report table using Streamlit's native dataframe
    display_df = build_display_dataframe(report_df, base_bank_name)
    
    # Use styled dataframe
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=800,
        column_config={
            f"{base_bank_name[:12]}": st.column_config.Column(
                f"{base_bank_name}",
                help="Base Bank Performance"
            )
        }
    )
    
    # Download section
    st.markdown("---")
    st.subheader("📥 Download Underlying Data")
    
    st.markdown("""
    Download the raw metric data for all banks included in the peer group calculations.
    This includes all Domestic, Regional, EU, and EU Large banks.
    """)
    
    # Generate the data upfront for download
    with st.spinner("Preparing download data..."):
        df_download = get_underlying_bank_data(
            base_country, 
            base_region, 
            base_systemic_importance,
            size_category
        )
    
    if not df_download.empty:
        # Convert to CSV
        csv_data = df_download.to_csv(index=False)
        
        st.success(f"✅ {len(df_download)} banks available for download")
        
        st.download_button(
            label="📥 Download CSV File",
            data=csv_data,
            file_name=f"benchmarking_data_{latest_period}.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.warning("No data available for download.")

    # Custom Explorer Section - MOVED TO SEPARATE TAB
    pass


def build_display_dataframe(report_df, base_bank_name):
    """
    Build a formatted DataFrame for display.
    """
    # Determine which metrics are amounts vs ratios
    amount_metrics = ['Gains / Losses (€M)']
    
    # Define peer group mapping for display
    # (Key in report_df, Short name for Column, Pctl Key in report_df)
    peer_groups = [
        ('Domestic Avg', 'Dom', 'Dom Pctl'),
        ('Regional (Same Size)', 'Reg (Size)', 'Reg Pctl'),
        ('EU (Same Size)', 'EU (Size)', 'EU Pctl'),
        ('EU Large', 'EU Large', 'EU Large Pctl')
    ]
    
    rows = []
    
    for _, row in report_df.iterrows():
        is_header = row.get('is_header', False)
        metric = row['Metric']
        
        if is_header:
            # Section header - create a row with the section name
            header_row = {
                'Metric': f"**{metric.replace('**', '')}**",
                base_bank_name[:12]: '',
            }
            # Initialize empty strings for all peer columns
            for _, short, _ in peer_groups:
                header_row[f'{short} Avg'] = ''
                header_row[f'{short} %ile'] = ''
            rows.append(header_row)
        else:
            # Data row
            is_amount = metric in amount_metrics
            
            base_val = row.get('Base Value', 0)
            base_formatted = format_value(base_val, is_ratio=not is_amount, is_amount=is_amount)
            
            row_data = {
                'Metric': metric,
                base_bank_name[:12]: base_formatted,
            }
            
            # Peer group columns
            for group_key, short, pctl_key in peer_groups:
                avg_val = row.get(group_key)
                pctl = row.get(pctl_key)
                
                avg_formatted = format_value(avg_val, is_ratio=not is_amount, is_amount=is_amount)
                # Keep percentile raw for styling, handle formatting in Styler or later step if needed
                # But Styler is applied on the whole df. 
                # To simplify, we keep values separate and apply style function.
                
                row_data[f'{short} Avg'] = avg_formatted
                row_data[f'{short} %ile'] = pctl # Keep numeric!
            
            rows.append(row_data)
    
    df = pd.DataFrame(rows)
    
    # Define style function for headers
    def style_headers(row):
        is_header_row = row['Metric'].startswith('**')
        if is_header_row:
            return ['background-color: #f0f2f6; font-weight: bold; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc'] * len(row)
        return [''] * len(row)

    # Apply styling
    styler = df.style.apply(style_headers, axis=1)
    
    # Format percentile columns
    pctl_cols = [f'{short} %ile' for _, short, _ in peer_groups]
    for col in pctl_cols:
        if col in df.columns:
            styler.map(get_percentile_color, subset=[col])
            styler.format(lambda x: f"{x:.0f}" if isinstance(x, (int, float)) and not pd.isna(x) else ("" if pd.isna(x) else str(x)), subset=[col])

    return styler


def render_custom_explorer(base_lei, base_name, country_iso, region, systemic_importance, size_category):
    """
    Render the Custom Metric Explorer section with multi-select and download.
    """
    st.subheader("🔎 Deep-Dive Explorer")
    st.markdown("Select specific metrics from the database to benchmark.")
    
    # 1. Metric Selection (Updated for cross-category selection)
    
    # Get available metrics
    df_metrics = get_available_metrics_for_explorer()
    
    # Initialize session state for saved presets
    if 'saved_explorer_presets' not in st.session_state:
        st.session_state.saved_explorer_presets = {}
        
    # Preset management
    with st.expander("💾 Saved Presets", expanded=False):
        c1, c2 = st.columns([3, 1])
        with c1:
             preset_name = st.text_input("New Preset Name", placeholder="e.g. Credit Risk Deep Dive")
        with c2:
            if st.button("Save Current Selection"):
                if preset_name and 'explorer_selection_cache' in st.session_state:
                    st.session_state.saved_explorer_presets[preset_name] = st.session_state.explorer_selection_cache
                    st.success(f"Saved '{preset_name}'!")
                elif not 'explorer_selection_cache' in st.session_state:
                    st.warning("Select metrics first!")
                    
        if st.session_state.saved_explorer_presets:
            st.divider()
            st.markdown("**Load Preset:**")
            cols = st.columns(4)
            for i, (name, metrics) in enumerate(st.session_state.saved_explorer_presets.items()):
                with cols[i % 4]:
                    if st.button(name, key=f"load_{name}"):
                        st.session_state.explorer_selection_override = metrics
                        st.rerun()

    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Category Filter
        available_categories = sorted(df_metrics['category'].unique().tolist())
        selected_categories = st.multiselect("Filter by Category", available_categories, key="explorer_category_filter")
    
    # Pre-process metrics
    all_metrics_map = {}
    
    # Filter DataFrame based on selected categories
    if selected_categories:
        df_filtered = df_metrics[df_metrics['category'].isin(selected_categories)]
    else:
        df_filtered = df_metrics
        
    for _, row in df_filtered.iterrows():
        key = f"{row['label']} ({row['item_id']})"
        all_metrics_map[key] = row['category']
        
    all_options = sorted(list(all_metrics_map.keys()))
    
    # Determine default value (from update or empty)
    default_selection = st.session_state.get('explorer_selection_override', [])
    
    # Clear override after reading
    if 'explorer_selection_override' in st.session_state:
        del st.session_state.explorer_selection_override
        
    with col2:
        selected_metric_strs = st.multiselect("Select Metrics", all_options, default=default_selection, key="explorer_metric_select")
        
    # Cache selection for saving
    st.session_state.explorer_selection_cache = selected_metric_strs
    
    if not selected_metric_strs:
        return
        
    # Extract IDs and Labels
    selected_ids = []
    selected_labels = []
    for s in selected_metric_strs:
        # We use the full string 'Label (ID)' as the column name to ensure uniqueness
        # Otherwise if two metrics have same label (different IDs), we get duplicate cols and crash
        selected_ids.append(s.split('(')[-1].replace(')', ''))
        selected_labels.append(s)
    
    # Options
    normalize = st.checkbox("Show as % of Total Assets", value=False)
    
    # 2. Get Data
    if st.button("Analyze Metrics"):
        # Get peer groups
        groups = get_benchmarking_peer_groups(country_iso, region, systemic_importance, size_category)
        
        # Get all LEIs
        all_leis = set([base_lei])
        for leis in groups.values():
            all_leis.update(leis)
            
        # Fetch Data
        with st.spinner("Fetching granular data..."):
            # Pass lists of IDs and Labels
            df = get_custom_metric_data(selected_ids, selected_labels, list(all_leis))
            
        if df.empty:
            st.warning("No data found for these metrics.")
            return
            
        latest_period = df['period'].max()
        df_latest = df[df['period'] == latest_period].copy()
        
        # Add peer group info for download
        for group_name, group_leis in groups.items():
            df[f'In {group_name}'] = df['lei'].isin(group_leis)

        st.markdown("### Results")
        st.caption(f"Period: {latest_period} | Units: {'% of Assets' if normalize else 'EUR Millions'}")
        
        # Display stats for EACH selected metric
        for idx, label in enumerate(selected_labels):
            item_id = selected_ids[idx]
            
            # Calculate derived value if normalized
            val_col = label
            dataset = df_latest.copy()
            
            if normalize:
                col_name = f"{label} (% Assets)"
                dataset[col_name] = dataset[label] / dataset['Total Assets (Normalization)']
                val_col = col_name
            else:
                # Just formatting
                pass

            # Base value
            base_row = dataset[dataset['lei'] == base_lei]
            base_val = 0
            if not base_row.empty:
                base_val = base_row.iloc[0][val_col]
            
            # Build comparison table
            stats_data = []
            for group_name, group_leis in groups.items():
                if not group_leis: continue
                
                df_peers = dataset[dataset['lei'].isin(group_leis)]
                if df_peers.empty: continue
                
                peer_vals = df_peers[val_col].dropna()
                if peer_vals.empty: continue
                
                avg_val = peer_vals.mean()
                pctl = calculate_percentiles(base_val, peer_vals.tolist(), higher_is_better=None)
                
                stats_data.append({
                    'Peer Group': group_name,
                    'Average': avg_val,
                    'Percentile': pctl,
                    'N': len(peer_vals)
                })
            
            # Metric Card
            with st.expander(f"📊 {label}", expanded=True):
                c1, c2 = st.columns([1, 2])
                fmt = "{:.2%}" if normalize else "{:,.1f}"
                
                with c1:
                    st.metric(base_name, fmt.format(base_val))
                
                with c2:
                    st.table(pd.DataFrame(stats_data).style.format({
                        'Average': fmt.format,
                        'Percentile': "{:.0f}th"
                    }))

        # 3. Download Options
        st.markdown("---")
        st.subheader("📤 Export Report")
        
        c1, c2 = st.columns(2)
        
        # CSV Export
        csv_data = df.to_csv(index=False)
        c1.download_button(
            label="📥 Download Data (CSV)",
            data=csv_data,
            file_name=f"custom_metrics_{latest_period}.csv",
            mime="text/csv"
        )
        
        # EXCEL Export (using pandas Styler if we want formatting, but raw is safer for now)
        # Create an Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Raw Data', index=False)
            
            # Create a summary sheet
            summary_rows = []
            for idx, label in enumerate(selected_labels):
                 col = label if not normalize else f"{label} (% Assets)"
                 # Simple summary
                 summary_rows.append({'Metric': label, 'Base Value': df_latest[df_latest['lei']==base_lei][col].iloc[0] if not df_latest[df_latest['lei']==base_lei].empty else 0})
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name='Summary', index=False)
            
        excel_data = output.getvalue()
        c2.download_button(
            label="📥 Download Report (Excel)",
            data=excel_data,
            file_name=f"custom_report_{latest_period}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


