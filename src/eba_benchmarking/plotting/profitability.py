import plotly.graph_objects as go
import pandas as pd
from eba_benchmarking.config import CHART_COLORS
from .basic import sort_with_base_first, apply_standard_layout, format_amount

def plot_operating_income_composition_percent(df, base_bank_name, benchmarks_df=None):
    """100% Stacked Bar for Operating Income Structure."""
    fig = go.Figure()
    cols = [
        ('Net Interest Income', CHART_COLORS['income'][0]), 
        ('Net Fee & Commission Income', CHART_COLORS['income'][1]),
        ('Net Trading Income', CHART_COLORS['income'][2]),
        ('Dividend Income', CHART_COLORS['income'][3]),
        ('Other Operating Income', CHART_COLORS['income'][4])
    ]
    
    df_plot = sort_with_base_first(df, base_bank_name, 'Total Operating Income')
    if benchmarks_df is not None and not benchmarks_df.empty:
        df_plot = pd.concat([df_plot, benchmarks_df], ignore_index=True)
    
    for col, color in cols:
        if col in df_plot.columns:
            share = df_plot[col] / df_plot['Total Operating Income']
            pattern = ["/" if "Avg" in name or "Average" in name else "" for name in df_plot['name']]
            text_vals = [f"{v:.1%}" if v >= 0.05 else "" for v in share]
            fig.add_trace(go.Bar(
                name=col, x=df_plot['name'], y=share, 
                marker_color=color, marker_pattern_shape=pattern,
                text=text_vals, textposition='inside'
            ))
            
    fig.update_layout(barmode='stack', yaxis_tickformat='.0%')
    return apply_standard_layout(fig, "Operating Income Structure (%)", 450, yaxis_tickformat='.0%')

def plot_non_interest_income_trend(df, base_bank_name, benchmarks_df=None):
    """Trend chart for Non-Interest Income share."""
    df_chart = df.copy()
    df_chart['Non-II %'] = df_chart['Non-Interest Income'] / df_chart['Total Operating Income']
    
    fig = go.Figure()
    d_base = df_chart[df_chart['name'] == base_bank_name].copy()
    min_date = pd.to_datetime('2000-01-01')
    
    if not d_base.empty:
        d_base['period_dt'] = pd.to_datetime(d_base['period'])
        d_base = d_base.sort_values('period_dt')
        min_date = d_base['period_dt'].min()
        
        fig.add_trace(go.Scatter(
            x=d_base['period_dt'], y=d_base['Non-II %'], 
            name=base_bank_name, line=dict(color=CHART_COLORS['base_bank'], width=4)
        ))
        
    filtered_periods = [d_base['period']] if not d_base.empty else []

    if benchmarks_df is not None and not benchmarks_df.empty:
        filtered_periods.append(benchmarks_df['period'])
        benchmarks_df = benchmarks_df.copy()
        benchmarks_df['Non-II %'] = benchmarks_df['Non-Interest Income'] / benchmarks_df['Total Operating Income']
        benchmarks_df['period_dt'] = pd.to_datetime(benchmarks_df['period'])
        # Filter
        benchmarks_df = benchmarks_df[benchmarks_df['period_dt'] >= min_date]
        
        for name in benchmarks_df['name'].unique():
            d = benchmarks_df[benchmarks_df['name'] == name].sort_values('period_dt')
            fig.add_trace(go.Scatter(
                x=d['period_dt'], y=d['Non-II %'], 
                name=name, line=dict(dash='dot', width=2)
            ))
            
    fig.update_layout(yaxis_tickformat='.1%', hovermode="x unified")
    
    all_periods = pd.concat(filtered_periods) if filtered_periods else pd.Series([], dtype='object')
    return apply_standard_layout(fig, "Non-Interest Income Share Trend", 450, xaxis_type='date', periods=all_periods, yaxis_tickformat='.1%')

def plot_pl_evolution_trend(df, base_bank_name):
    """Historical Trend of P&L Components (Stacked Bar) + Net Profit (Line).
    Filters for Year-over-Year comparison based on the latest available cut-off month.
    """
    d_base = df[df['name'] == base_bank_name].copy()
    if d_base.empty: return go.Figure().update_layout(title="No Data for P&L Evolution")

    # Filter for same month as latest period
    d_base['period_dt'] = pd.to_datetime(d_base['period'])
    latest_date = d_base['period_dt'].max()
    target_month = latest_date.month
    d_base = d_base[d_base['period_dt'].dt.month == target_month].sort_values('period')

    fig = go.Figure()
    
    # Income (Positive)
    incomes = [
        ('Net Interest Income', CHART_COLORS['income'][0]), 
        ('Net Fee & Commission Income', CHART_COLORS['income'][1]),
        ('Net Trading Income', CHART_COLORS['income'][2]),
        ('Dividend Income', CHART_COLORS['income'][3]),
        ('Other Operating Income', CHART_COLORS['income'][4])
    ]
    
    # Expense (Negative)
    expenses = [
        ('Admin Expenses', CHART_COLORS['expense'][0]),
        ('Depreciation', CHART_COLORS['expense'][1]),
        ('Provisions', CHART_COLORS['expense'][2]),
        ('Impairment Cost', CHART_COLORS['expense'][3]),
        ('Tax Expenses', CHART_COLORS['expense'][4])
    ]
    
    for col, color in incomes:
        if col in d_base.columns:
            fig.add_trace(go.Bar(name=col, x=d_base['period_dt'], y=d_base[col], marker_color=color, offsetgroup=0))
            
    for col, color in expenses:
        if col in d_base.columns:
            fig.add_trace(go.Bar(name=col, x=d_base['period_dt'], y=d_base[col] * -1, marker_color=color, offsetgroup=0))

    if 'Net Profit' in d_base.columns:
        fig.add_trace(go.Scatter(
            name='Net Profit', x=d_base['period_dt'], y=d_base['Net Profit'], 
            mode='lines+markers+text', 
            line=dict(color='black', width=3),
            text=d_base['Net Profit'].apply(format_amount),
            textposition='top center'
        ))

    fig.update_layout(barmode='relative', yaxis_title="Amount", hovermode="x unified")
    return apply_standard_layout(fig, f"Historical P&L Evolution (YoY Comparison - Month {target_month})", 500, xaxis_type='date', periods=d_base['period'])

def plot_pl_waterfall_granular(df, base_bank_name, period):
    """Detailed Waterfall Chart for P&L Decomposition."""
    row = df[(df['name'] == base_bank_name) & (df['period'] == period)]
    if row.empty: return go.Figure().update_layout(title="No Data for Waterfall")
    row = row.iloc[0]

    # Values
    nii = row.get('Net Interest Income', 0)
    fees = row.get('Net Fee & Commission Income', 0)
    trading = row.get('Net Trading Income', 0)
    divs = row.get('Dividend Income', 0)
    other_inc = row.get('Other Operating Income', 0)
    
    admin = row.get('Admin Expenses', 0) * -1
    depr = row.get('Depreciation', 0) * -1
    prov = row.get('Provisions', 0) * -1
    imp = row.get('Impairment Cost', 0) * -1
    tax = row.get('Tax Expenses', 0) * -1
    net_profit = row.get('Net Profit', 0)

    fig = go.Figure(go.Waterfall(
        name = "P&L", orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "relative", "total", 
                   "relative", "relative", "relative", "relative", "relative", "total"],
        x = ["NII", "Fees", "Trading", "Dividends", "Other Inc", "Op Income", 
             "Admin", "Depr", "Provisions", "Impairment", "Tax", "Net Profit"],
        textposition = "outside",
        text = [format_amount(x) for x in [nii, fees, trading, divs, other_inc, row.get('Total Operating Income'), admin, depr, prov, imp, tax, net_profit]],
        y = [nii, fees, trading, divs, other_inc, 0, admin, depr, prov, imp, tax, 0],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))

    return apply_standard_layout(fig, f"P&L Waterfall ({period})", 500)

def plot_pl_waterfall_yoy(df, base_bank_name, current_period):
    """YoY Bridge Chart."""
    d_bank = df[df['name'] == base_bank_name]
    
    # Find Previous Year Period
    curr_dt = pd.to_datetime(current_period)
    prev_year_dt = curr_dt - pd.DateOffset(years=1)
    # We need string match YYYY-MM
    prev_period = prev_year_dt.strftime('%Y-%m')
    
    row_curr = d_bank[d_bank['period'] == current_period]
    row_prev = d_bank[d_bank['period'] == prev_period]
    
    if row_curr.empty or row_prev.empty:
        return go.Figure().update_layout(title="No Data for YoY Bridge (Missing Periods)")
        
    rc = row_curr.iloc[0]
    rp = row_prev.iloc[0]
    
    # Deltas
    d_nii = rc.get('Net Interest Income', 0) - rp.get('Net Interest Income', 0)
    d_fees = rc.get('Net Fee & Commission Income', 0) - rp.get('Net Fee & Commission Income', 0)
    d_trading = rc.get('Net Trading Income', 0) - rp.get('Net Trading Income', 0)
    d_other_inc = (rc.get('Other Operating Income', 0) + rc.get('Dividend Income', 0)) - (rp.get('Other Operating Income', 0) + rp.get('Dividend Income', 0))
    d_exp = (rc.get('Total Operating Expenses', 0) * -1) - (rp.get('Total Operating Expenses', 0) * -1) # Exp is usually positive in DB, so we negate for P&L impact. If Total Op Exp increased, impact is negative.
    d_risk = (rc.get('Impairment Cost', 0) * -1 + rc.get('Provisions', 0) * -1) - (rp.get('Impairment Cost', 0) * -1 + rp.get('Provisions', 0) * -1)
    d_tax = (rc.get('Tax Expenses', 0) * -1) - (rp.get('Tax Expenses', 0) * -1)
    
    start_profit = rp.get('Net Profit', 0)
    end_profit = rc.get('Net Profit', 0)
    
    fig = go.Figure(go.Waterfall(
        measure=["absolute", "relative", "relative", "relative", "relative", "relative", "relative", "relative", "total"],
        x=[prev_period, "NII", "Fees", "Trading", "Other Inc", "Expenses", "Risk Cost", "Tax", current_period],
        y=[start_profit, d_nii, d_fees, d_trading, d_other_inc, d_exp, d_risk, d_tax, 0], # Waterfall calcs final automatically? No, we set y values, let Plotly compute total if 'total' measure. But for 'absolute', key is y.
        # Actually for 'total', y is ignored or set to 0? 
        # Standard Waterfall: relative adds up. absolute sets new baseline.
        # Start is absolute. End is total (computed).
        text=[format_amount(x) for x in [start_profit, d_nii, d_fees, d_trading, d_other_inc, d_exp, d_risk, d_tax, end_profit]],
        connector={"line":{"color":"rgb(63, 63, 63)"}},
    ))
    
    return apply_standard_layout(fig, f"Net Profit Bridge: {prev_period} to {current_period}", 500)

def plot_nii_evolution(df, base_bank_name):
    """Evolution of NII components (Interest Income vs Expense) for Base Bank."""
    d_base = df[df['name'] == base_bank_name].copy()
    if d_base.empty: return go.Figure().update_layout(title="No Data for NII Evolution")
    
    d_base['period_dt'] = pd.to_datetime(d_base['period'])
    d_base = d_base.sort_values('period_dt')

    fig = go.Figure()
    
    # Interest Income (Positive)
    fig.add_trace(go.Bar(
        name='Interest Income', x=d_base['period_dt'], y=d_base['Interest Income'],
        marker_color=CHART_COLORS['income'][0]
    ))
    
    # Interest Expenses (Negative) - Ensure they are negative for visualization
    fig.add_trace(go.Bar(
        name='Interest Expenses', x=d_base['period_dt'], 
        y=d_base['Interest Expenses'] * -1,
        marker_color=CHART_COLORS['expense'][0]
    ))
    
    # Net Line
    fig.add_trace(go.Scatter(
        name='Net Interest Income', x=d_base['period_dt'], y=d_base['Net Interest Income'],
        mode='lines+markers', line=dict(color='black', width=3)
    ))
    
    fig.update_layout(barmode='relative', yaxis_title="Amount", hovermode="x unified")
    return apply_standard_layout(fig, "NII Evolution (Base Bank)", 450, xaxis_type='date', periods=d_base['period'])

def plot_nii_structure_snapshot(df, base_bank_name, kind='income', benchmarks_df=None):
    """
    100% Stacked Bar for Interest Income or Expense Composition (Snapshot vs Peers).
    kind: 'income' or 'expense'
    """
    fig = go.Figure()
    
    if kind == 'income':
        cols = [
            ('Int Inc: Loans', CHART_COLORS['income'][0]), 
            ('Int Inc: Debt Securities', CHART_COLORS['income'][1])
        ]
        total_col = 'Interest Income'
        title = "Interest Income Structure (%)"
    else:
        cols = [
            ('Int Exp: Deposits', CHART_COLORS['expense'][0]), 
            ('Int Exp: Debt Securities', CHART_COLORS['expense'][1])
        ]
        total_col = 'Interest Expenses'
        title = "Interest Expense Structure (%)"

    df_plot = sort_with_base_first(df, base_bank_name, total_col)
    if benchmarks_df is not None and not benchmarks_df.empty:
        df_plot = pd.concat([df_plot, benchmarks_df], ignore_index=True)

    # Calculate 'Other' residual
    # Fix for sum of series: initialize with 0
    comp_sum = 0
    for c, _ in cols:
        if c in df_plot.columns:
            comp_sum = comp_sum + df_plot[c].fillna(0)
    
    other_label = 'Other (Derivatives, Cash)' if kind == 'income' else 'Other (Derivatives, Repos)'
    
    df_plot[other_label] = df_plot[total_col] - comp_sum
    df_plot[other_label] = df_plot[other_label].clip(lower=0)
    
    all_cols = cols + [(other_label, '#999999')]

    for col, color in all_cols:
        if col in df_plot.columns:
            # Handle potential zeros to avoid div/0
            share = df_plot.apply(lambda x: x[col] / x[total_col] if x[total_col] > 0 else 0, axis=1)
            pattern = ["/" if "Avg" in name or "Average" in name else "" for name in df_plot['name']]
            
            text_vals = [f"{v:.1%}" if v >= 0.05 else "" for v in share]
            fig.add_trace(go.Bar(
                name=col, x=df_plot['name'], y=share,
                marker_color=color, marker_pattern_shape=pattern,
                text=text_vals, textposition='inside'
            ))

    fig.update_layout(barmode='stack', yaxis_tickformat='.0%')
    return apply_standard_layout(fig, title, 450, yaxis_tickformat='.0%')

def plot_component_share_trend(df, base_bank_name, numerator_col, denominator_col, title, benchmarks_df=None):
    """
    Line chart showing the trend of a specific component's share (e.g., Loan Income % of Total Int Income).
    """
    # Calculate Share for Banks
    df = df.copy()
    df['share'] = df.apply(lambda x: x[numerator_col] / x[denominator_col] if x[denominator_col] > 0 else 0, axis=1)
    
    fig = go.Figure()
    
    # Base Bank
    d_base = df[df['name'] == base_bank_name].copy()
    min_date = pd.to_datetime('2000-01-01')

    if not d_base.empty:
        d_base['period_dt'] = pd.to_datetime(d_base['period'])
        d_base = d_base.sort_values('period_dt')
        min_date = d_base['period_dt'].min()
        
        fig.add_trace(go.Scatter(
            x=d_base['period_dt'], y=d_base['share'], 
            name=base_bank_name, 
            line=dict(color=CHART_COLORS['base_bank'], width=4)
        ))
        
    # Benchmarks
    filtered_periods = [d_base['period']] if not d_base.empty else []

    if benchmarks_df is not None and not benchmarks_df.empty:
        filtered_periods.append(benchmarks_df['period'])
        df_b = benchmarks_df.copy()
        df_b['share'] = df_b.apply(lambda x: x[numerator_col] / x[denominator_col] if x[denominator_col] > 0 else 0, axis=1)
        df_b['period_dt'] = pd.to_datetime(df_b['period'])
        # Filter
        df_b = df_b[df_b['period_dt'] >= min_date]
        
        for name in df_b['name'].unique():
            d = df_b[df_b['name'] == name].sort_values('period_dt')
            # Color logic
            c = CHART_COLORS['average']
            if "Domestic" in name: c = CHART_COLORS['domestic_avg']
            elif "EU" in name: c = CHART_COLORS['eu_avg']
            
            fig.add_trace(go.Scatter(
                x=d['period_dt'], y=d['share'], 
                name=name, line=dict(color=c, dash='dot', width=2)
            ))
            
    fig.update_layout(yaxis_tickformat='.1%', hovermode="x unified")
    
    all_periods = pd.concat(filtered_periods) if filtered_periods else pd.Series([], dtype='object')
    return apply_standard_layout(fig, title, 450, xaxis_type='date', periods=all_periods, yaxis_tickformat='.1%')

def plot_implied_rates(df, base_bank_name):
    """
    Line chart showing the evolution of Implied Yields (Asset side) vs Costs (Liability side).
    """
    d_base = df[df['name'] == base_bank_name].copy()
    if d_base.empty: return go.Figure().update_layout(title="No Data for Rates")
    
    # Explicitly sort by period again just to be safe
    d_base['period_dt'] = pd.to_datetime(d_base['period'])
    d_base = d_base.sort_values('period_dt')
    
    fig = go.Figure()
    
    # Yields (Lines)
    fig.add_trace(go.Scatter(
        name='Loan Yield', x=d_base['period_dt'], y=d_base['Implied Loan Yield'],
        mode='lines+markers', line=dict(color=CHART_COLORS['income'][0], width=3)
    ))
    fig.add_trace(go.Scatter(
        name='Securities Yield', x=d_base['period_dt'], y=d_base['Implied Securities Yield'],
        mode='lines+markers', line=dict(color=CHART_COLORS['income'][1], width=2, dash='dot')
    ))
    
    # Costs (Lines)
    fig.add_trace(go.Scatter(
        name='Deposit Cost', x=d_base['period_dt'], y=d_base['Implied Deposit Cost'],
        mode='lines+markers', line=dict(color=CHART_COLORS['expense'][0], width=3)
    ))
    fig.add_trace(go.Scatter(
        name='Debt Cost', x=d_base['period_dt'], y=d_base['Implied Debt Cost'],
        mode='lines+markers', line=dict(color=CHART_COLORS['expense'][1], width=2, dash='dot')
    ))
    fig.add_trace(go.Scatter(
        name='Interbank Cost', x=d_base['period_dt'], 
        y=d_base['Implied Interbank Cost'] if 'Implied Interbank Cost' in d_base.columns else [0]*len(d_base),
        mode='lines+markers', line=dict(color=CHART_COLORS['expense'][2], width=2, dash='dot')
    ))
    
    # Net Spread (Shaded Area? Or just Funding Cost)
    fig.add_trace(go.Scatter(
        name='Avg Funding Cost', x=d_base['period_dt'], y=d_base['Implied Funding Cost'],
        mode='lines', line=dict(color='black', width=1, dash='dash')
    ))

    fig.update_layout(yaxis_tickformat='.2%', yaxis_title="Annualized Rate", hovermode="x unified")
    return apply_standard_layout(fig, "Implied Yields & Funding Costs", 450, xaxis_type='date', periods=d_base['period'], yaxis_tickformat='.2%')
