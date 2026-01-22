import plotly.graph_objects as go
import pandas as pd
from eba_benchmarking.config import CHART_COLORS, RWA_CATEGORY_COLORS, RWA_CATEGORY_ORDER
from .basic import sort_with_base_first, apply_standard_layout, format_amount

def plot_solvency_trend(df_bank, df_benchmarks, metric_col, title, base_bank_name, df_eu_kri=None):
    """Advanced Trend Chart comparing Base Bank vs Benchmarks & EU Average."""
    fig = go.Figure()

    # Determine if metric is an amount (needs scaling) or ratio
    is_amount = 'Amount' in title or ('Capital' in metric_col and 'Ratio' not in metric_col)
    hovertemplate = '%{y:,.1f}B' if is_amount else None

    # 1. Base Bank
    d_bank = df_bank[df_bank['name'] == base_bank_name].copy()
    if d_bank.empty:
        # Fallback if base bank data is missing entirely
        min_date = pd.to_datetime('2000-01-01')
    else:
        d_bank['period_dt'] = pd.to_datetime(d_bank['period'])
        d_bank = d_bank.sort_values('period_dt')
        min_date = d_bank['period_dt'].min()

        y_vec = d_bank[metric_col] / 1000.0 if is_amount else d_bank[metric_col]

        fig.add_trace(go.Scatter(
            x=d_bank['period_dt'], y=y_vec,
            name=base_bank_name,
            line=dict(color=CHART_COLORS['base_bank'], width=4),
            hovertemplate=hovertemplate
        ))
    
    # 2. Benchmarks (Domestic/Size Avg)
    if df_benchmarks is not None and not df_benchmarks.empty:
        # Robust Sort
        df_benchmarks = df_benchmarks.copy()
        df_benchmarks['period_dt'] = pd.to_datetime(df_benchmarks['period'])
        # Filter
        df_benchmarks = df_benchmarks[df_benchmarks['period_dt'] >= min_date]
        
        for name in sorted(df_benchmarks['name'].unique()):
            d = df_benchmarks[df_benchmarks['name'] == name].sort_values('period_dt')
            if not d.empty:
                # Determine color
                if "Domestic" in name:
                    c = CHART_COLORS['domestic_avg']
                elif "EU" in name:
                    c = CHART_COLORS['eu_avg']
                else:
                    c = CHART_COLORS['average']
                    
                y_vec = d[metric_col] / 1000.0 if is_amount else d[metric_col]
                fig.add_trace(go.Scatter(
                    x=d['period_dt'], y=y_vec, 
                    name=name, 
                    line=dict(color=c, dash='dash', width=2),
                    hovertemplate=hovertemplate
                ))
    
    # 3. EU KRI Baseline
    if df_eu_kri is not None and not df_eu_kri.empty:
        kri_map = {
            'Total Capital Ratio': 'Total capital ratio', 
            'Leverage Ratio': 'Leverage ratio', 
            'CET1 Ratio': 'CET 1 capital ratio', 
            'npl_ratio': 'Share of non‐performing loans and advances (NPL ratio)',
            'Cost to Income': 'Cost to income ratio'
        }
        target = kri_map.get(metric_col, metric_col) # Fallback to col name
        
        # Try finding exact or partial match
        possible_kris = df_eu_kri['kri_name'].unique()
        if target not in possible_kris:
             # Logic to find closest match could go here, but relying on explicit map first
             pass

        d_eu = df_eu_kri[(df_eu_kri['country'] == 'EU') & (df_eu_kri['kri_name'] == target)].copy()
        
    # 3. EU KRI Baseline - REMOVED as per request for most charts, or specific request?
    # Request: "remove the EBA eu averages" from solvency tab. 
    # But usually we keep KRI for ratios. "remove the EBA eu averages. remove the rwa density from this tab."
    # Let's assume removing the KRI lines (the dotted green ones) completely for Solvency Tab trends.
    # So I will comment out or remove this block for now.
    
    # if df_eu_kri is not None and not df_eu_kri.empty:
    #    ... (Logic removed)
            
    fig.update_layout(hovermode="x unified")
    
    # Re-collect periods from what we actually filtered
    filtered_periods = []
    if not d_bank.empty: filtered_periods.append(d_bank['period'])
    if df_benchmarks is not None and not df_benchmarks.empty: filtered_periods.append(df_benchmarks['period'])
    
    all_periods = pd.concat(filtered_periods) if filtered_periods else pd.Series([], dtype='object')
    
    if is_amount:
        fig.update_layout(yaxis_title="Amount (€B)", yaxis_tickformat=',.1f')
    else:
        # Heuristic for percentage formatting
        is_pct = any(x in metric_col.lower() or x in title.lower() for x in ['ratio', '%', 'roe', 'roa', 'margin', 'share', 'yield', 'cost'])
        # Exception: 'Texas Ratio' sometimes > 100%, but still %, usually displayed as %.
        if is_pct:
            fig.update_layout(yaxis_tickformat='.1%')
        
    return apply_standard_layout(fig, title, 400, xaxis_type='date', periods=all_periods)

def plot_capital_components(df, base_bank_name, benchmarks_df=None):
    """Stacked Bar for Capital Amounts."""
    cols = [
        ('CET1 Capital', CHART_COLORS['capital']['cet1']), 
        ('AT1 Capital', CHART_COLORS['capital']['at1']), 
        ('Tier 2 Capital', CHART_COLORS['capital']['t2'])
    ]
    
    df['total'] = df['CET1 Capital'] + df['AT1 Capital'] + df['Tier 2 Capital']
    df_plot = sort_with_base_first(df, base_bank_name, 'total')
    
    if benchmarks_df is not None and not benchmarks_df.empty:
        df_b = benchmarks_df.copy()
        df_b['total'] = df_b['CET1 Capital'] + df_b['AT1 Capital'] + df_b['Tier 2 Capital']
        df_plot = pd.concat([df_plot, df_b], ignore_index=True)
        
    # Scale to Billions
    cols_to_scale = ['CET1 Capital', 'AT1 Capital', 'Tier 2 Capital', 'total']
    for c in cols_to_scale:
        if c in df_plot.columns:
            df_plot[c] = df_plot[c] / 1000.0

    fig = go.Figure()
    for col, color in cols:
        if col in df_plot.columns:
            # Pattern logic: 'x' for averages
            pattern = ["/" if "Avg" in name or "Average" in name else "" for name in df_plot['name']]
            fig.add_trace(go.Bar(
                name=col, x=df_plot['name'], y=df_plot[col], 
                marker_color=color, marker_pattern_shape=pattern
            ))
            
    # Total Text Label
    # Total Text Label using Annotations for better control
    for i, row in df_plot.iterrows():
        fig.add_annotation(
            x=row['name'], y=row['total'],
            text=f"<b>{row['total']:,.1f}B</b>",
            showarrow=False,
            yshift=15, # Shift up to avoid overlap
            font=dict(color='black')
        )
    
    fig.update_layout(barmode='stack', yaxis_title="Amount (€B)")
    return apply_standard_layout(fig, "Capital Components (Amounts)", 450)

def plot_capital_ratios(df, base_bank_name, benchmarks_df=None):
    """Stacked Bar for Capital Ratios."""
    cols = [
        ('CET1 Ratio', 'CET1 Ratio', CHART_COLORS['capital']['cet1']), 
        ('AT1 %', 'AT1 Ratio (calc)', CHART_COLORS['capital']['at1']), 
        ('Tier 2 %', 'Tier 2 Ratio (calc)', CHART_COLORS['capital']['t2'])
    ]
    
    df_plot = sort_with_base_first(df, base_bank_name, 'Total Capital Ratio')
    if benchmarks_df is not None and not benchmarks_df.empty:
        df_plot = pd.concat([df_plot, benchmarks_df], ignore_index=True)
        
    fig = go.Figure()
    for label, col, color in cols:
        if col in df_plot.columns:
            # Pattern logic: hatch for averages
            pattern = ["/" if "Avg" in name or "Average" in name else "" for name in df_plot['name']]
            # Text color logic: Black for averages (light background), White for banks (dark background)
            text_colors = ["black" if "Avg" in name or "Average" in name else "white" for name in df_plot['name']]
            
            # Conditional text labeling: hide if < 1.5% (reverted)
            # df_plot[col] is ratio (0.02 etc)
            text_vals = [f"{v:.1%}" if v >= 0.015 else "" for v in df_plot[col]]
            
            fig.add_trace(go.Bar(
                name=label, x=df_plot['name'], y=df_plot[col], 
                marker_color=color, marker_pattern_shape=pattern,
                text=text_vals, textposition='auto',
                hovertemplate=f"<b>{label}</b>: %{{y:.2%}}<extra></extra>",
                textfont=dict(color=text_colors)
            ))
            
    # Add Total Sum Annotation on top
    # Use 'Total Capital Ratio' if available, otherwise sum components
    if 'Total Capital Ratio' in df_plot.columns:
        total_vals = df_plot['Total Capital Ratio']
    else:
        # Fallback sum
        total_vals = df_plot[['CET1 Ratio', 'AT1 %', 'Tier 2 %']].sum(axis=1) # Note: assumes columns present
        
    # Add Total Sum Annotation on top using Annotations
    for i, name in enumerate(df_plot['name']):
        val = total_vals.iloc[i]
        fig.add_annotation(
            x=name, y=val,
            text=f"<b>{val:.1%}</b>",
            showarrow=False,
            yshift=40, # Shift up significantly (40px) to clear any outside labels from top segment
            font=dict(color='black')
        )
            
    fig.update_layout(barmode='stack')
    return apply_standard_layout(fig, "Capital Ratios (% of TREA)", 450, yaxis_tickformat='.0%')

def plot_rwa_composition(df_raw, base_bank_name, show_pct=False):
    """
    Stacked bar chart for RWA composition by category.
    """
    if df_raw.empty: 
        return go.Figure()
    
    # 1. Map labels to main categories
    def map_category(label):
        l = label.lower()
        if 'total' in l: return 'Exclude'
        if 'of which' in l: return 'Exclude'
        
        if 'credit risk' in l and 'counterparty' not in l: return 'Credit Risk'
        if 'operational risk' in l: return 'Operational Risk'
        if 'market risk' in l or 'trading book' in l or 'foreign exchange' in l or 'position risk' in l or 'commodities' in l: return 'Market Risk'
        if 'settlement' in l: return 'Settlement Risk'
        if 'counterparty' in l or 'ccr' in l or 'cva' in l: return 'Counterparty Risk'
        if 'securitisation' in l: return 'Securitisation'
        return 'Other'

    df = df_raw.copy()
    df['MainCategory'] = df['label'].apply(map_category)
    df = df[df['MainCategory'] != 'Exclude']
    
    # 2. Pivot & Aggregate
    df_piv = df.pivot_table(index='name', columns='MainCategory', values='amount', aggfunc='sum').fillna(0)
    
    # Sort: base bank first, then peers, then averages last
    is_avg = lambda n: 'Avg' in n or 'Average' in n
    base_banks = [n for n in df_piv.index if n == base_bank_name]
    peer_banks = [n for n in df_piv.index if n != base_bank_name and not is_avg(n)]
    avg_banks = [n for n in df_piv.index if is_avg(n)]
    bank_order = base_banks + peer_banks + avg_banks
    df_piv = df_piv.reindex([n for n in bank_order if n in df_piv.index])
    
    # Calculate totals for percentage
    df_piv['Total'] = df_piv.sum(axis=1)
    
    # Use centralized config for colors and order
    categories = [c for c in RWA_CATEGORY_ORDER if c in df_piv.columns]
    
    fig = go.Figure()
    
    for cat in categories:
        color = RWA_CATEGORY_COLORS.get(cat, '#7f7f7f')
        
        if show_pct:
            values = df_piv[cat] / df_piv['Total'] * 100
            text = [f"{v:.1f}%" if v >= 1.5 else "" for v in values]
            hovertemplate = f"<b>{cat}</b><br>Share: %{{y:.1f}}%<extra></extra>"
        else:
            # Scale to Billions
            values = df_piv[cat] / 1000.0 
            text = [f"€{v:,.1f}B" for v in values]
            hovertemplate = f"<b>{cat}</b><br>Amount: €%{{y:,.1f}}B<extra></extra>"
        
        fig.add_trace(go.Bar(
            x=df_piv.index,
            y=values,
            name=cat,
            text=text,
            textposition='auto', 
            customdata=df_piv[cat], # Original values (M)
            hovertemplate=hovertemplate,
            marker_color=color
        ))
    
    fig.update_layout(barmode='stack')
    
    if show_pct:
        fig.update_layout(yaxis_tickformat='.0f', yaxis_title='Share (%)')
    else:
        # Values are now in Billions
        fig.update_layout(yaxis_tickformat=',.0f', yaxis_title='Amount (€B)')
        # Add Total annotation on top
        for i, name in enumerate(df_piv.index):
            total_val = df_piv.loc[name, 'Total'] / 1000.0 # Scale to B
            fig.add_annotation(
                x=name, y=total_val,
                text=f"<b>€{total_val:,.1f}B</b>",
                showarrow=False,
                yshift=15
            )
    
    title = "RWA Composition (% Share)" if show_pct else "RWA Composition (Amount)"
    return apply_standard_layout(fig, title)

def plot_texas_ratio(df, benchmarks_df, title, base_bank_name):
    """Trend chart for Texas Ratio."""
    return plot_solvency_trend(df, benchmarks_df, 'Texas Ratio', title, base_bank_name)
