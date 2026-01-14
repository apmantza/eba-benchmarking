import plotly.graph_objects as go
import pandas as pd
from eba_benchmarking.config import CHART_COLORS
from .basic import sort_with_base_first, apply_standard_layout, format_amount, get_color_sequence

def plot_asset_composition(df, base_bank_name, benchmarks_df=None):
    """Stacked Bar for Asset Categories (Amounts)."""
    fig = go.Figure()
    cats = ['Cash', 'Loans and advances', 'Securities', 'Other Assets']
    cols = get_color_sequence(len(cats))
    
    df_plot = sort_with_base_first(df, base_bank_name, 'Total Assets')
    if benchmarks_df is not None and not benchmarks_df.empty:
        latest = benchmarks_df['period'].max()
        df_b = benchmarks_df[benchmarks_df['period'] == latest].copy()
        df_plot = pd.concat([df_plot, df_b], ignore_index=True)
        
    # Scale to Billions
    for cat in cats:
        if cat in df_plot.columns:
            df_plot[cat] = df_plot[cat] / 1000.0
    df_plot['Total Assets'] = df_plot['Total Assets'] / 1000.0

    for i, cat in enumerate(cats):
        pattern = ["/" if "Avg" in name or "Average" in name else "" for name in df_plot['name']]
        # Use fillna(0) for safety
        val = df_plot[cat] if cat in df_plot.columns else 0
        fig.add_trace(go.Bar(
            name=cat, x=df_plot['name'], y=val, 
            marker_color=cols[i], marker_pattern_shape=pattern
        ))
        
    # Add Total annotation on top
    for i, row in df_plot.iterrows():
        fig.add_annotation(
            x=row['name'], y=row['Total Assets'],
            text=f"<b>{row['Total Assets']:,.1f}B</b>",
            showarrow=False,
            yshift=15,
            font=dict(color='black')
        )
    fig.update_layout(barmode='stack', yaxis_title="Amount (€B)")
    return apply_standard_layout(fig, "Asset Composition (Amounts)", 450)

def plot_asset_composition_percent(df, base_bank_name, benchmarks_df=None):
    """Stacked Bar for Asset Composition (%)."""
    fig = go.Figure()
    cats = ['Cash', 'Loans and advances', 'Securities', 'Other Assets']
    cols = get_color_sequence(len(cats))
    
    df_plot = sort_with_base_first(df, base_bank_name, 'Total Assets')
    if benchmarks_df is not None and not benchmarks_df.empty:
        latest = benchmarks_df['period'].max()
        df_b = benchmarks_df[benchmarks_df['period'] == latest].copy()
        df_plot = pd.concat([df_plot, df_b], ignore_index=True)
        
    for i, cat in enumerate(cats):
        share = df_plot[cat] / df_plot['Total Assets']
        pattern = ["/" if "Avg" in name or "Average" in name else "" for name in df_plot['name']]
        text_colors = ["black" if "Avg" in name or "Average" in name else "white" for name in df_plot['name']]
        text_vals = [f"{v:.1%}" if v >= 0.05 else "" for v in share]
        fig.add_trace(go.Bar(
            name=cat, x=df_plot['name'], y=share, 
            marker_color=cols[i], marker_pattern_shape=pattern, 
            text=text_vals, textposition='inside',
            textfont=dict(color=text_colors)
        ))
        
    fig.update_layout(barmode='stack', yaxis_tickformat='.0%')
    return apply_standard_layout(fig, "Asset Composition (%)", 450, yaxis_tickformat='.0%')

def plot_liability_composition(df, base_bank_name, benchmarks_df=None):
    """Stacked Bar for Liability & Equity Categories (Amounts)."""
    fig = go.Figure()
    cats = ['Equity', 'Customer Deposits', 'Interbank Deposits', 'Central Bank Funding', 'Debt Securities Issued', 'Other Liabilities']
    # Use generic cat colors cycling if needed
    cols = get_color_sequence(len(cats))
    
    if 'equity' in df.columns: df['Equity'] = df['equity']
    
    df_plot = sort_with_base_first(df, base_bank_name, 'total_eq_liab')
    
    if benchmarks_df is not None and not benchmarks_df.empty:
        latest = benchmarks_df['period'].max()
        df_b = benchmarks_df[benchmarks_df['period'] == latest].copy()
        if 'equity' in df_b.columns: df_b['Equity'] = df_b['equity']
        df_plot = pd.concat([df_plot, df_b], ignore_index=True)
        
    # Scale to Billions
    for cat in cats:
        if cat in df_plot.columns:
            df_plot[cat] = df_plot[cat] / 1000.0
    df_plot['total_eq_liab'] = df_plot['total_eq_liab'] / 1000.0

    for i, cat in enumerate(cats):
        pattern = ["/" if "Avg" in name or "Average" in name else "" for name in df_plot['name']]
        val = df_plot[cat] if cat in df_plot.columns else 0
        fig.add_trace(go.Bar(
            name=cat, x=df_plot['name'], y=val, 
            marker_color=cols[i], marker_pattern_shape=pattern
        ))
        
    # Add Total annotation on top
    for i, row in df_plot.iterrows():
        fig.add_annotation(
            x=row['name'], y=row['total_eq_liab'],
            text=f"<b>{row['total_eq_liab']:,.1f}B</b>",
            showarrow=False,
            yshift=15,
            font=dict(color='black')
        )
    fig.update_layout(barmode='stack', yaxis_title="Amount (€B)")
    return apply_standard_layout(fig, "Funding Composition (Liabilities & Equity)", 450)

def plot_liability_composition_percent(df, base_bank_name, benchmarks_df=None):
    """Stacked Bar for Liability & Equity Composition (%)."""
    fig = go.Figure()
    cats = ['Equity', 'Customer Deposits', 'Interbank Deposits', 'Central Bank Funding', 'Debt Securities Issued', 'Other Liabilities']
    cols = get_color_sequence(len(cats))
    
    if 'equity' in df.columns: df['Equity'] = df['equity']
    
    df_plot = sort_with_base_first(df, base_bank_name, 'total_eq_liab')
    if benchmarks_df is not None and not benchmarks_df.empty:
        latest = benchmarks_df['period'].max()
        df_b = benchmarks_df[benchmarks_df['period'] == latest].copy()
        if 'equity' in df_b.columns: df_b['Equity'] = df_b['equity']
        df_plot = pd.concat([df_plot, df_b], ignore_index=True)
        
    for i, cat in enumerate(cats):
        val = df_plot[cat] if cat in df_plot.columns else 0
        share = val / df_plot['total_eq_liab']
        pattern = ["/" if "Avg" in name or "Average" in name else "" for name in df_plot['name']]
        text_colors = ["black" if "Avg" in name or "Average" in name else "white" for name in df_plot['name']]
        text_vals = [f"{v:.1%}" if v >= 0.05 else "" for v in share]
        fig.add_trace(go.Bar(
            name=cat, x=df_plot['name'], y=share, 
            marker_color=cols[i], marker_pattern_shape=pattern, 
            text=text_vals, textposition='inside',
            textfont=dict(color=text_colors)
        ))
        
    fig.update_layout(barmode='stack', yaxis_tickformat='.0%')
    return apply_standard_layout(fig, "Funding Structure (%)", 450, yaxis_tickformat='.0%')

def plot_deposit_beta(df_beta, base_bank_name):
    """
    Plots Deposit Beta Analysis:
    1. Implied Deposit Cost over time vs ECB Deposit Facility Rate
    2. Cumulative Beta (pass-through rate)
    """
    if df_beta.empty:
        return go.Figure().update_layout(title="Deposit Beta (No Data)")
    
    fig = go.Figure()
    
    # Sort by period
    df_beta['period_dt'] = pd.to_datetime(df_beta['period'])
    df_beta = df_beta.sort_values('period_dt')
    
    # 1. Plot ECB Rate (shared baseline)
    ecb_data = df_beta[['period_dt', 'ecb_rate']].drop_duplicates().dropna()
    if not ecb_data.empty:
        fig.add_trace(go.Scatter(
            x=ecb_data['period_dt'], 
            y=ecb_data['ecb_rate'],
            name="ECB Deposit Facility Rate",
            line=dict(color='#2F4F4F', width=3, dash='dash'),
            yaxis='y1'
        ))
    
    # 2. Plot Base Bank Implied Deposit Cost
    d_base = df_beta[df_beta['name'] == base_bank_name].copy()
    if not d_base.empty:
        fig.add_trace(go.Scatter(
            x=d_base['period_dt'],
            y=d_base['Implied Deposit Cost'],
            name=f"{base_bank_name} Deposit Cost",
            line=dict(color=CHART_COLORS['base_bank'], width=3),
            yaxis='y1'
        ))
    
    # 3. Plot Peers (thin lines)
    peers = df_beta[df_beta['name'] != base_bank_name]['name'].unique()
    peer_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']
    
    for i, peer in enumerate(peers):
        d = df_beta[df_beta['name'] == peer].copy()
        color = peer_palette[i % len(peer_palette)]
        fig.add_trace(go.Scatter(
            x=d['period_dt'],
            y=d['Implied Deposit Cost'],
            name=peer,
            line=dict(color=color, width=1.5),
            opacity=0.7,
            yaxis='y1'
        ))
    
    fig.update_layout(
        yaxis=dict(title="Rate (%)", tickformat='.2%'),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return apply_standard_layout(fig, "Deposit Cost vs ECB Rate", 450, xaxis_type='date', periods=d_base['period'] if not d_base.empty else None)

def plot_cumulative_beta(df_beta, base_bank_name):
    """
    Bar chart showing cumulative deposit beta for each bank.
    Beta < 1 is favorable (lower pass-through to depositors).
    """
    if df_beta.empty or 'cumulative_beta' not in df_beta.columns:
        return go.Figure().update_layout(title="Cumulative Deposit Beta (No Data)")
    
    # Get latest period beta
    latest = df_beta['period'].max()
    df_lat = df_beta[df_beta['period'] == latest].copy()
    
    if df_lat.empty or df_lat['cumulative_beta'].isna().all():
        return go.Figure().update_layout(title="Cumulative Deposit Beta (Insufficient Data)")
    
    # Sort: base bank first, then by beta ascending (lower is better)
    df_base = df_lat[df_lat['name'] == base_bank_name]
    df_peers = df_lat[df_lat['name'] != base_bank_name].sort_values('cumulative_beta')
    df_plot = pd.concat([df_base, df_peers], ignore_index=True)
    
    # Color: Base bank red, peers by beta (green < 1, red > 1)
    colors = []
    for i, row in df_plot.iterrows():
        if row['name'] == base_bank_name:
            colors.append(CHART_COLORS['base_bank'])
        elif pd.notna(row['cumulative_beta']) and row['cumulative_beta'] < 1:
            colors.append('#2ecc71')  # Green (favorable)
        else:
            colors.append('#e74c3c')  # Red (unfavorable)
    
    fig = go.Figure(data=[go.Bar(
        x=df_plot['name'],
        y=df_plot['cumulative_beta'],
        marker_color=colors,
        text=df_plot['cumulative_beta'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"),
        textposition='auto'
    )])
    
    # Add reference line at 1.0 (100% pass-through)
    fig.add_hline(y=1.0, line_dash="dash", line_color="black", 
                  annotation_text="100% Pass-Through", annotation_position="right")
    
    fig.update_layout(
        yaxis_title="Deposit Beta",
        yaxis=dict(range=[0, max(2, df_plot['cumulative_beta'].max() * 1.2 if pd.notna(df_plot['cumulative_beta'].max()) else 2)])
    )
    
    return apply_standard_layout(fig, "Cumulative Deposit Beta (Since 2021)", 400)

