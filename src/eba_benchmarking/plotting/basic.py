import plotly.graph_objects as go
import pandas as pd
from eba_benchmarking.config import CHART_COLORS

# --- HELPER FUNCTIONS ---

def sort_with_base_first(df, base_bank_name, metric_col, ascending=False):
    """Ensures the base bank is first, then sorts peers by value, and places benchmarks at end."""
    if df.empty: return df
    is_avg = df['name'].str.contains('Avg|Average', case=False, na=False)
    base_df = df[(df['name'] == base_bank_name) & (~is_avg)].copy()
    bench_df = df[is_avg].copy()
    peers_df = df[(df['name'] != base_bank_name) & (~is_avg)].copy()
    peers_df = peers_df.sort_values(metric_col, ascending=ascending)
    return pd.concat([base_df, peers_df, bench_df], ignore_index=True)

def apply_standard_layout(fig, title, height=450, xaxis_type='category', periods=None, yaxis_tickformat=None):
    """
    Standardizes chart layout:
    - White background
    - Top legend with spacing to prevent title overlap
    - Responsive margins
    - Accessible titles
    """
    fig.update_layout(
        title=dict(text=title, font=dict(size=16), y=0.95),
        height=height, 
        margin=dict(l=20, r=20, t=160, b=40), # Significantly increased top margin for legend and labels
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.15,  # Place legend higher up to avoid overlap with top labels
            xanchor="right", 
            x=1
        ),
        paper_bgcolor='white',
        plot_bgcolor='white',
        uniformtext_minsize=8, 
        uniformtext_mode='hide', # Hides text if it doesn't fit
        autosize=True,
        xaxis=dict(type=xaxis_type, tickangle=45, showgrid=False) if xaxis_type else dict(tickangle=45, showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0', tickformat=yaxis_tickformat)
    )
    
    # Handle implicit quarterly formatting for date axes
    if xaxis_type == 'date' and periods is not None:
        try:
            # Ensure unique sorted dates
            p_dt = pd.to_datetime(periods).dropna().unique()
            p_dt = sorted(p_dt)
            
            # Create Q labels
            tickvals = p_dt
            ticktext = [f"Q{(d.month-1)//3 + 1} {d.year}" for d in p_dt]
            
            fig.update_xaxes(
                tickmode='array',
                tickvals=tickvals,
                ticktext=ticktext,
                tickangle=45
            )
        except Exception:
            pass # Fallback to default if date parsing fails

    # Ensure title doesn't get cut off and text on bars is handled nicely
    fig.update_traces(cliponaxis=False)
    
    # Generic settings for avoiding overlap
    fig.update_layout(
        font=dict(family="Inter, sans-serif")
    )
    return fig

def format_amount(x):
    """Formats values for chart labels (assumes input in Millions, converts to Billions)."""
    return f"{x/1000:,.1f}B"

# --- PLOTTING FUNCTIONS ---

def get_color_sequence(n=None):
    """
    Returns a consistent sequence of categorical colors from config.
    If n is provided, returns a list of length n (cycling if necessary).
    """
    # Base sequence from cat1 to cat10
    base_seq = [CHART_COLORS[f'cat{i+1}'] for i in range(10)]
    
    if n is None:
        return base_seq
        
    # Cycle if n > len(base_seq)
    full_seq = []
    for i in range(n):
        full_seq.append(base_seq[i % len(base_seq)])
    return full_seq

def plot_benchmark_bar(df, metric_col, title, base_bank_name, format_pct=True, height=400, scale_amounts=True):
    """Standard Benchmark Bar Chart with Base Bank First"""
    if metric_col not in df.columns or df[metric_col].isna().all():
        return go.Figure().update_layout(title=f"{title} (No Data)", xaxis={'visible':False}, yaxis={'visible':False})
    
    df_plot = sort_with_base_first(df, base_bank_name, metric_col)
    
    # Color Logic: Base Bank = Red, Peers = Grey, Averages = Specific Colors
    colors = []
    for x in df_plot['name']:
        if x == base_bank_name:
            colors.append(CHART_COLORS['base_bank'])
        elif "Domestic" in x:
            colors.append(CHART_COLORS['domestic_avg'])
        elif "EU" in x:
            colors.append(CHART_COLORS['eu_avg'])
        elif "Avg" in x or "Average" in x:
            colors.append(CHART_COLORS['average']) # Fallback
        else:
            colors.append(CHART_COLORS['peer'])

    # Scale to Billions if Amount
    if not format_pct and scale_amounts:
        df_plot[metric_col] = df_plot[metric_col] / 1000.0

    fig = go.Figure(data=[go.Bar(
        x=df_plot['name'], 
        y=df_plot[metric_col], 
        marker_color=colors,
        text=df_plot[metric_col], 
        texttemplate='%{y:.1%}' if format_pct else ('%{y:,.1f}B' if scale_amounts else '%{y:,.2f}'), 
        textposition='auto',
        hovertemplate='%{x}: %{y:.2%}' if format_pct else ('%{x}: %{y:,.1f}B<extra></extra>' if scale_amounts else '%{x}: %{y:,.2f}<extra></extra>')
    )])
    
    y_fmt = None if format_pct else (',.0f' if scale_amounts else ',.2f') 
    y_title = None if format_pct else ('Amount (€B)' if scale_amounts else 'Value')
    fig.update_layout(yaxis_title=y_title)
    return apply_standard_layout(fig, title, height, yaxis_tickformat=y_fmt)

def plot_trend_line(df, metric_col, title, base_bank_name):
    """Line Chart: Base Bank vs Peer Average over time."""
    if metric_col not in df.columns: return go.Figure().update_layout(title=f"{title} (No Data)")
    
    # Dynamic Filtering based on Base Bank
    df_base = df[df['name'] == base_bank_name].copy()
    if df_base.empty: return go.Figure().update_layout(title=f"{title} (No Data)")
    
    df_base['period_dt'] = pd.to_datetime(df_base['period'])
    df_base = df_base.sort_values('period_dt')
    min_date = df_base['period_dt'].min()

    df_peers = df[df['name'] != base_bank_name]
    
    fig = go.Figure()
    
    # Peer Average Line
    if not df_peers.empty:
        df_avg = df_peers.groupby('period')[metric_col].mean().reset_index()
        df_avg['period_dt'] = pd.to_datetime(df_avg['period'])
        df_avg = df_avg.sort_values('period_dt')
        # Filter
        df_avg = df_avg[df_avg['period_dt'] >= min_date]

        fig.add_trace(go.Scatter(
            x=df_avg['period_dt'], 
            y=df_avg[metric_col], 
            name="Peer Average", 
            line=dict(color=CHART_COLORS['average'], width=2, dash='dot')
        ))
    
    # Base Bank Line
    fig.add_trace(go.Scatter(
        x=df_base['period_dt'], 
        y=df_base[metric_col], 
        name=base_bank_name, 
        mode='lines+markers', 
        line=dict(color=CHART_COLORS['base_bank'], width=3)
    ))
    
    fig.update_layout(hovermode="x unified")
    return apply_standard_layout(fig, title, 400, xaxis_type='date', periods=df_base['period'])

def plot_peer_comparison_trend(df, metric_col, title, base_bank_name, format_pct=False):
    """
    Line chart comparing a specific metric across all banks in the dataframe.
    Base bank is bold, averages are dashed, other peers are thin lines.
    """
    if metric_col not in df.columns: return go.Figure().update_layout(title=f"{title} (No Data)")
    
    fig = go.Figure()
    
    hovertemplate = '%{y:.2%}' if format_pct else '%{y}'

    # 3. Plot Base Bank (bold)
    d_base = df[df['name'] == base_bank_name].copy()
    min_date = pd.to_datetime('2000-01-01')
    if not d_base.empty:
        d_base['period_dt'] = pd.to_datetime(d_base['period'])
        d_base = d_base.sort_values('period_dt')
        min_date = d_base['period_dt'].min()
        
        fig.add_trace(go.Scatter(
            x=d_base['period_dt'], y=d_base[metric_col],
            name=base_bank_name,
            mode='lines+markers',
            line=dict(width=4, color=CHART_COLORS['base_bank']),
            hovertemplate=hovertemplate
        ))

    # 1. Plot Peers (thin lines, unique colors)
    peers = df[(df['name'] != base_bank_name) & (~df['name'].str.contains('Avg|Average', case=False, na=False))]['name'].unique()
    
    # Palette for peers (cycling)
    peer_palette = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd', '#8c564b', 
        '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#aec7e8', 
        '#ffbb78', '#98df8a', '#c5b0d5', '#c49c94', '#f7b6d2'
    ]
    
    for i, peer in enumerate(peers):
        d = df[df['name'] == peer].copy()
        d['period_dt'] = pd.to_datetime(d['period'])
        d = d.sort_values('period_dt')
        # Filter
        d = d[d['period_dt'] >= min_date]
        color = peer_palette[i % len(peer_palette)]
        
        fig.add_trace(go.Scatter(
            x=d['period_dt'], y=d[metric_col],
            name=peer,
            line=dict(width=1.5, color=color),
            opacity=0.8,
            hovertemplate=hovertemplate
        ))
        
    # 2. Plot Averages (dashed)
    avgs = df[df['name'].str.contains('Avg|Average', case=False, na=False)]['name'].unique()
    for avg in avgs:
        d = df[df['name'] == avg].copy()
        d['period_dt'] = pd.to_datetime(d['period'])
        d = d.sort_values('period_dt')
        # Filter
        d = d[d['period_dt'] >= min_date]
        c = CHART_COLORS['average']
        if "Domestic" in avg: c = CHART_COLORS['domestic_avg']
        elif "EU" in avg: c = CHART_COLORS['eu_avg']
        
        fig.add_trace(go.Scatter(
            x=d['period_dt'], y=d[metric_col],
            name=avg,
            line=dict(width=2, dash='dash', color=c),
            hovertemplate=hovertemplate
        ))
        
    if format_pct:
        fig.update_layout(yaxis_tickformat='.2%')
        
    fig.update_layout(hovermode="x unified")
    return apply_standard_layout(fig, title, 450, xaxis_type='date', periods=d_base['period'] if not d_base.empty else None)
