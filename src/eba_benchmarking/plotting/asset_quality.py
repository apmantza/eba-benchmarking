import plotly.graph_objects as go
import pandas as pd
from eba_benchmarking.config import CHART_COLORS
from .basic import sort_with_base_first, apply_standard_layout, format_amount

def plot_aq_breakdown(df, base_bank_name):
    """Stacked Bar for Asset Quality Components."""
    fig = go.Figure()
    cols = [
        ('Performing Stage 1', CHART_COLORS['asset_quality']['stage1']), 
        ('Performing Stage 2', CHART_COLORS['asset_quality']['stage2']), 
        ('Performing In Arrears', CHART_COLORS['asset_quality']['arrears']), 
        ('Non-Performing', CHART_COLORS['asset_quality']['npl'])
    ]
    
    df['total'] = df['Performing Stage 1'] + df['Performing Stage 2'] + df['Performing In Arrears'] + df['Non-Performing']
    df_plot = sort_with_base_first(df, base_bank_name, 'total')
    
    # Scale to Billions
    for col, _ in cols:
        if col in df_plot.columns:
            df_plot[col] = df_plot[col] / 1000.0
    df_plot['total'] = df_plot['total'] / 1000.0

    for col, color in cols:
        if col in df_plot.columns: 
            fig.add_trace(go.Bar(name=col, x=df_plot['name'], y=df_plot[col], marker_color=color))
            
    fig.add_trace(go.Scatter(
        x=df_plot['name'], y=df_plot['total'], 
        text=df_plot['total'].apply(lambda x: f"{x:,.1f}B"), 
        mode='text', textposition='top center', showlegend=False
    ))
    
    fig.update_layout(barmode='stack', yaxis_title="Amount (€B)")
    return apply_standard_layout(fig, "Loan Portfolio Breakdown (Amounts)", 450)

def plot_aq_breakdown_trend(df, base_bank_name):
    """Line chart for AQ breakdown trend."""
    df_base = df[df['name'] == base_bank_name].copy()
    if df_base.empty: return go.Figure().update_layout(title="No Data for AQ Evolution")
    
    df_base['period_dt'] = pd.to_datetime(df_base['period'])
    df_base = df_base.sort_values('period_dt')
    min_date = df_base['period_dt'].min()
    
    fig = go.Figure()
    cols = [
        ('Performing Stage 1', CHART_COLORS['asset_quality']['stage1']), 
        ('Performing Stage 2', CHART_COLORS['asset_quality']['stage2']), 
        ('Performing In Arrears', CHART_COLORS['asset_quality']['arrears']), 
        ('Non-Performing', CHART_COLORS['asset_quality']['npl'])
    ]
    
    for col, color in cols:
        if col in df_base.columns: 
            fig.add_trace(go.Scatter(
                x=df_base['period_dt'], y=df_base[col], 
                name=col, mode='lines+markers', line=dict(color=color)
            ))
            
    fig.update_layout(hovermode="x unified")
    return apply_standard_layout(fig, "Asset Quality Evolution", 450, xaxis_type='date', periods=df_base['period'])
