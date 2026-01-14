import plotly.graph_objects as go
import pandas as pd
from eba_benchmarking.config import CHART_COLORS
from .basic import apply_standard_layout, get_color_sequence

def plot_market_history(df, metric, title, base_bank_name, format_pct=False, show_legend=True):
    """
    Plots historical market data trends for multiple banks.
    
    Args:
        df: DataFrame with columns [name, date, metric]
        metric: Column name to plot
        title: Chart title
        base_bank_name: Name of the base bank (highlighted)
        format_pct: If True, format as percentage
        show_legend: Show legend
    """
    if df.empty or metric not in df.columns:
        return go.Figure()
    
    fig = go.Figure()
    
    # Get unique banks
    banks = df['name'].unique()
    
    # Color mapping
    # Color mapping
    colors = get_color_sequence(len(banks))
    
    for i, bank in enumerate(banks):
        df_bank = df[df['name'] == bank].sort_values('date')
        
        is_base = bank == base_bank_name
        color = CHART_COLORS['base_bank'] if is_base else colors[i % len(colors)]
        width = 3 if is_base else 1.5
        opacity = 1.0 if is_base else 0.6
        
        # Format values for hover
        if format_pct:
            hovertemplate = f"<b>{bank}</b><br>%{{x}}<br>{metric}: %{{y:.2%}}<extra></extra>"
        else:
            hovertemplate = f"<b>{bank}</b><br>%{{x}}<br>{metric}: %{{y:,.2f}}<extra></extra>"
        
        fig.add_trace(go.Scatter(
            x=df_bank['date'],
            y=df_bank[metric],
            name=bank,
            mode='lines',
            line=dict(color=color, width=width),
            opacity=opacity,
            hovertemplate=hovertemplate
        ))
    
    # Format y-axis
    if format_pct:
        fig.update_yaxes(tickformat='.1%')
    
    fig.update_layout(
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return apply_standard_layout(fig, title, xaxis_type='date')
