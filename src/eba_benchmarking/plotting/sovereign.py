import plotly.graph_objects as go
import pandas as pd
from eba_benchmarking.config import CHART_COLORS
from .basic import sort_with_base_first, apply_standard_layout, get_color_sequence

def plot_sov_portfolios(df, base_bank_name, benchmarks_df=None):
    """Stacked Bar for Sovereign Portfolios."""
    fig = go.Figure()
    ports = ['Held for trading', 'Designated at FV', 'FVOCI', 'Amortised Cost']
    cols = get_color_sequence(len(ports))
    
    df_sum = df.groupby(['name', 'portfolio'])['amount'].sum().reset_index()
    df_totals = df_sum.groupby('name')['amount'].sum().reset_index()
    df_plot_order = sort_with_base_first(df_totals, base_bank_name, 'amount')
    
    if benchmarks_df is not None and not benchmarks_df.empty:
        latest = benchmarks_df['period'].max()
        df_b = benchmarks_df[benchmarks_df['period'] == latest].copy()
        df_sum = pd.concat([df_sum, df_b[['name', 'portfolio', 'amount']]], ignore_index=True)
        # Re-sort including benchmarks
        df_b_totals = df_b.groupby('name')['amount'].sum().reset_index()
        df_plot_order = pd.concat([df_plot_order, df_b_totals], ignore_index=True)
        # Note: sort_with_base_first was called before merging benchmarks, so peers are sorted. benchmarks appended.
        
    # Scale to Billions
    df_sum['amount'] = df_sum['amount'] / 1000.0
    df_plot_order['amount'] = df_plot_order['amount'] / 1000.0
    
    for i, p in enumerate(ports):
        d = df_sum[df_sum['portfolio'] == p]
        pattern = ["/" if "Avg" in name or "Average" in name else "" for name in df_plot_order['name']]
        # Text color smart logic: if 'Avg' or value is small, black. If dark bar, white.
        # But 'cat' colors vary. Let's force 'auto' textposition with black generally or smart contrast.
        # Usually black text stands out on lighter colors, white on dark.
        # Let's use 'auto' and hope Plotly handles it, or force black for Avgs which have patterns.
        
        # Actually user said "currently we have white values which are not showing". 
        # This implies we had text set to something causing white on white? 
        # In previous code (not showing text here), maybe default template.
        # I will add text labels.
        
        # Prepare text labels, hiding small values to avoid clutter
        # We need relative size of this bar vs total for that bank.
        # df_plot_order contains totals. 
        # Map total to d['name'] to compare.
        totals_map = df_plot_order.set_index('name')['amount']
        
        def get_label(row):
            tot = totals_map.get(row['name'])
            val = row['amount']
            if val == 0 or tot == 0: return ""
            if (val / tot) < 0.05: return "" # Hide if < 5% of height
            return f"{val:,.1f}B"

        d_vals = df_plot_order['name'].map(d.groupby('name')['amount'].sum()).fillna(0)
        # Reconstruct frame to apply lambda
        temp_df = pd.DataFrame({'name': df_plot_order['name'], 'amount': d_vals})
        text_vals = temp_df.apply(get_label, axis=1)

        fig.add_trace(go.Bar(
            name=p, x=df_plot_order['name'], 
            y=d_vals, 
            marker_color=cols[i],
            marker_pattern_shape=pattern,
            text=text_vals, textposition='inside'
        ))
        
    # Add Total annotation on top
    for i, row in df_plot_order.iterrows():
        fig.add_annotation(
            x=row['name'], y=row['amount'],
            text=f"<b>{row['amount']:,.1f}B</b>",
            showarrow=False,
            yshift=15, # Shift up to avoid overlap
            font=dict(color='black')
        )
        
    fig.update_layout(barmode='stack', yaxis_title="Amount (€B)")
    return apply_standard_layout(fig, "Sovereign Exposures by Portfolio", 450)

def plot_sov_portfolios_percent(df, base_bank_name, benchmarks_df=None):
    """Stacked Bar for Sovereign Portfolios (%)."""
    fig = go.Figure()
    ports = ['Held for trading', 'Designated at FV', 'FVOCI', 'Amortised Cost']
    cols = get_color_sequence(len(ports))
    
    df_sum = df.groupby(['name', 'portfolio'])['amount'].sum().reset_index()
    df_totals = df_sum.groupby('name')['amount'].sum().reset_index()
    df_sum = pd.merge(df_sum, df_totals, on='name', suffixes=('', '_total'))
    df_sum['pct'] = df_sum['amount'] / df_sum['amount_total']
    
    df_plot_order = sort_with_base_first(df_totals, base_bank_name, 'amount')
    
    if benchmarks_df is not None and not benchmarks_df.empty:
        latest = benchmarks_df['period'].max()
        df_b = benchmarks_df[benchmarks_df['period'] == latest].copy()
        df_b_totals = df_b.groupby('name')['amount'].sum().reset_index()
        # Benchmark DF structure for portfolios? 
        # Assuming df_b has columns: name, portfolio, amount (or pct logic handled outside?)
        # Standard benchmark fetch returns aggregated metrics usually. 
        # If df_b comes from get_sovereign_averages, it has portfolio detail.
        df_b = pd.merge(df_b, df_b_totals, on='name', suffixes=('', '_total'))
        df_b['pct'] = df_b['amount'] / df_b['amount_total']
        df_sum = pd.concat([df_sum, df_b], ignore_index=True)
        df_plot_order = pd.concat([df_plot_order, df_b_totals], ignore_index=True)
        
    for i, p in enumerate(ports):
        d = df_sum[df_sum['portfolio'] == p]
        pattern = ["/" if "Avg" in name or "Average" in name else "" for name in df_plot_order['name']]
        vals = df_plot_order['name'].map(d.groupby('name')['pct'].sum()).fillna(0)
        text_vals = [f"{v:.1%}" if v >= 0.05 else "" for v in vals]
        
        fig.add_trace(go.Bar(
            name=p, x=df_plot_order['name'], 
            y=vals, 
            marker_color=cols[i],
            marker_pattern_shape=pattern,
            text=text_vals, textposition='inside'
        ))
    fig.update_layout(barmode='stack', yaxis_tickformat='.0%')
    return apply_standard_layout(fig, "Portfolio Composition (% of Total Sovereign)", 450)

def plot_sov_composition(df, title, base_bank_name, dim='country'):
    """Stacked Bar showing Total Portfolio composition."""
    fig = go.Figure()
    col = 'country_name' if dim == 'country' else 'maturity_label'
    df_sum = df.groupby(['name', col])['amount'].sum().reset_index()
    df_totals = df_sum.groupby('name')['amount'].sum().reset_index()
    df_totals.columns = ['name', 'bank_total']
    df_sum = pd.merge(df_sum, df_totals, on='name')
    df_sum['share'] = df_sum['amount'] / df_sum['bank_total']
    
    df_material = df_sum[df_sum['share'] >= 0.05].copy()
    df_other = df_sum[df_sum['share'] < 0.05].groupby('name').agg({'amount': 'sum', 'share': 'sum'}).reset_index()
    df_other[col] = 'Other'
    df_final = pd.concat([df_material, df_other], ignore_index=True)
    
    labels = sorted([l for l in df_final[col].unique() if l != 'Other'])
    labels.append('Other')
    df_plot_order = sort_with_base_first(df_totals, base_bank_name, 'bank_total')
    
    colors = get_color_sequence(len(labels))
    
    # Scale to Billions
    df_final['amount'] = df_final['amount'] / 1000.0
    df_plot_order['bank_total'] = df_plot_order['bank_total'] / 1000.0
    
    for i, label in enumerate(labels):
        d = df_final[df_final[col] == label]
        vals = df_plot_order['name'].map(d.groupby('name')['amount'].sum()).fillna(0)
        
        # Hide text labels for small amounts (<5%)
        totals_map = df_plot_order.set_index('name')['bank_total']
        text_vals = []
        for nm, v in zip(df_plot_order['name'], vals):
             tot = totals_map.get(nm, 0)
             if tot > 0 and (v/tot) >= 0.05:
                 text_vals.append(f"{v:,.1f}B") 
             else:
                 text_vals.append("")

        fig.add_trace(go.Bar(
            name=label, x=df_plot_order['name'], 
            y=vals,
            text=text_vals, textposition='inside',
            marker_color=colors[i % len(colors)]
        ))
        
    # Add Total annotation on top
    for i, row in df_plot_order.iterrows():
        fig.add_annotation(
            x=row['name'], y=row['bank_total'],
            text=f"<b>{row['bank_total']:,.1f}B</b>",
            showarrow=False,
            yshift=15,
            font=dict(color='black')
        )

    fig.update_layout(barmode='stack', yaxis_title="Amount (€B)")
    return apply_standard_layout(fig, title, 450)

def plot_sov_composition_percent(df, title, base_bank_name, dim='country'):
    """Stacked Bar showing Total Portfolio composition as Percentages."""
    fig = go.Figure()
    col = 'country_name' if dim == 'country' else 'maturity_label'
    df_sum = df.groupby(['name', col])['amount'].sum().reset_index()
    df_totals = df_sum.groupby('name')['amount'].sum().reset_index()
    df_totals.columns = ['name', 'bank_total']
    df_sum = pd.merge(df_sum, df_totals, on='name')
    df_sum['share'] = df_sum['amount'] / df_sum['bank_total']
    
    df_material = df_sum[df_sum['share'] >= 0.05].copy()
    df_other = df_sum[df_sum['share'] < 0.05].groupby('name').agg({'amount': 'sum', 'share': 'sum'}).reset_index()
    df_other[col] = 'Other'
    df_final = pd.concat([df_material, df_other], ignore_index=True)
    
    labels = sorted([l for l in df_final[col].unique() if l != 'Other'])
    labels.append('Other')
    df_plot_order = sort_with_base_first(df_totals, base_bank_name, 'bank_total')
    
    colors = get_color_sequence(len(labels))
    
    for i, label in enumerate(labels):
        d = df_final[df_final[col] == label]
        vals = df_plot_order['name'].map(d.groupby('name')['share'].sum()).fillna(0)
        text_vals = [f"{v:.1%}" if v >= 0.05 else "" for v in vals]

        fig.add_trace(go.Bar(
            name=label, x=df_plot_order['name'], 
            y=vals, 
            text=text_vals, textposition='inside',
            marker_color=colors[i % len(colors)]
        ))
    fig.update_layout(barmode='stack', yaxis_tickformat='.0%')
    return apply_standard_layout(fig, title, 450)

def plot_country_exposure_trend(df, country_name, base_bank_name):
    """Line chart for exposure trend to a specific country."""
    df_c = df[df['country_name'] == country_name].groupby(['name', 'period'])['amount'].sum().reset_index()
    fig = go.Figure()
    d_base = df_c[df_c['name'] == base_bank_name].copy()
    min_date = pd.to_datetime('2000-01-01')
    
    if not d_base.empty:
        d_base['period_dt'] = pd.to_datetime(d_base['period'])
        d_base = d_base.sort_values('period_dt')
        min_date = d_base['period_dt'].min()
        
        fig.add_trace(go.Scatter(
            x=d_base['period_dt'], y=d_base['amount'], 
            name=base_bank_name, 
            line=dict(color=CHART_COLORS['base_bank'], width=4)
        ))
        
    latest = df_c['period'].max()
    top_peers = df_c[(df_c['period'] == latest) & (df_c['name'] != base_bank_name)].sort_values('amount', ascending=False).head(5)['name']
    
    for peer in top_peers:
        d = df_c[df_c['name'] == peer].copy()
        d['period_dt'] = pd.to_datetime(d['period'])
        d = d.sort_values('period_dt')
        # Filter
        d = d[d['period_dt'] >= min_date]
        fig.add_trace(go.Scatter(x=d['period_dt'], y=d['amount'], name=peer, line=dict(dash='dot', width=1)))
        
    return apply_standard_layout(fig, f"Exposure Trend: {country_name}", 450, xaxis_type='date', periods=d_base['period'] if not d_base.empty else None)

def plot_home_bias_vs_cet1(df, base_bank_name, base_country, benchmarks_df=None):
    """Home Bias (Domestic Sovereign Exp) as % of CET1."""
    if 'cet1' not in df.columns:
        return go.Figure().update_layout(title="Missing CET1 Data")
    
    # Filter for Domestic Country
    # Each bank has its own home country? Or we use Base Bank's country for everyone? 
    # Usually Home Bias means Bank A -> Country A.
    # But we might not have 'home_country' column for peers easily available here.
    # In EBA data, 'country_name' is the exposure country.
    # We need to know the bank's home country.
    # Typically in this dataset, 'name' -> 'country' mapping is needed.
    # However, user request says "amend... to display the home bias". 
    # If we struggle with peer home countries, we can default to Base Bank's Home Country (Domestic Bias for that market).
    # But Home Bias usually implies "Own Sovereign".
    # Let's assume for peers we use the Base Country (Domestic Peers). For EU peers it's tricky.
    # User Request: "making sure to apply global styling... in home bias historical trend add domestic avg, eu peers avg and regional avg."
    # If we assume 'Domestic' exposure is what matters for Systemic Risk in that market, maybe filtering by `base_country` is enough?
    # NO: Home Bias is exposure to *Issuer of Origin*.
    # Let's use `base_country` for now as a proxy for "Domestic Sovereign Exposure" which is the main concern in stress tests usually (loops).
    
    # Calculate Home Bias for each bank (Exp to Own Country / CET1)
    # df should have 'bank_country_iso' if strictly queried, or we map it. 
    # get_sovereign_kpis now returns bank_country_iso.
    
    # Filter where Exposure ISO == Bank Home ISO
    # Fallback to country_name if ISO missing (though we added it)
    
    if 'bank_country_iso' in df.columns and 'country_iso' in df.columns:
        df_dom = df[df['country_iso'] == df['bank_country_iso']].groupby(['name', 'period', 'cet1'])['amount'].sum().reset_index()
    else:
        # Fallback to base_country filter if metadata missing (shouldn't happen with new query)
        target_col = 'country_iso' if 'country_iso' in df.columns else 'country_name'
        df_dom = df[df[target_col] == base_country].groupby(['name', 'period', 'cet1'])['amount'].sum().reset_index()

    df_dom['ratio'] = df_dom.apply(lambda x: x['amount'] / x['cet1'] if x['cet1'] > 0 else 0, axis=1)
    
    if df_dom.empty:
        return go.Figure().update_layout(title=f"No Sovereign Data for {target_country}")

    latest = df_dom['period'].max()
    df_lat = df_dom[df_dom['period'] == latest].copy()
    
    # Add Benchmarks (which should have pre-calc ratios or similar logic)
    if benchmarks_df is not None and not benchmarks_df.empty:
        latest_b = benchmarks_df['period'].max()
        # Ensure benchmark has ratio
        if 'home_bias_ratio' in benchmarks_df.columns:
             df_b_unique = benchmarks_df[benchmarks_df['period'] == latest_b][['name', 'home_bias_ratio']].drop_duplicates()
             bench_data = [{'name': r['name'], 'ratio': r['home_bias_ratio']} for _, r in df_b_unique.iterrows()]
             if bench_data: df_lat = pd.concat([df_lat, pd.DataFrame(bench_data)], ignore_index=True)
             
    df_plot = sort_with_base_first(df_lat, base_bank_name, 'ratio')
    
    colors = []
    text_colors = []
    for x in df_plot['name']:
        if x == base_bank_name: colors.append(CHART_COLORS['base_bank'])
        elif "Avg" in x or "Average" in x: colors.append(CHART_COLORS['average'])
        else: colors.append(CHART_COLORS['peer'])
        
        # Black text for lighter bars/averages
        if "Avg" in x or "Average" in x: text_colors.append("white")
        elif x == base_bank_name: text_colors.append("white")
        else: text_colors.append("black") # Peers are light grey

    patterns = ["/" if "Avg" in name or "Average" in name else "" for name in df_plot['name']]
    
    fig = go.Figure(go.Bar(
        x=df_plot['name'], y=df_plot['ratio'], 
        marker_color=colors, marker_pattern_shape=patterns,
        text=df_plot['ratio'], texttemplate='%{y:.1%}', textposition='auto',
        textfont=dict(color=text_colors) # Ensure visibility
    ))
    fig.update_layout(yaxis_tickformat='.1%', yaxis_title="Home Bias Ratio")
    return apply_standard_layout(fig, f"Home Bias (Domestic Sovereign Exposure / CET1)", 450)

def plot_home_bias_trend(df, base_bank_name, base_country, benchmarks_df=None):
    """Trend of Home Bias (Exposure to Base Country / CET1)."""
    # Filter for base country
    # Filter for base country
    # Filter where Exposure ISO == Bank Home ISO
    if 'bank_country_iso' in df.columns and 'country_iso' in df.columns:
        df_dom = df[df['country_iso'] == df['bank_country_iso']].groupby(['name', 'period', 'cet1'])['amount'].sum().reset_index()
    else:
        target_col = 'country_iso' if 'country_iso' in df.columns else 'country_name'
        df_dom = df[df[target_col] == base_country].groupby(['name', 'period', 'cet1'])['amount'].sum().reset_index()

    df_dom['ratio'] = df_dom.apply(lambda x: x['amount'] / x['cet1'] if x['cet1'] > 0 else 0, axis=1)
    
    fig = go.Figure()
    
    # Base Bank
    d_base = df_dom[df_dom['name'] == base_bank_name].copy()
    min_date = pd.to_datetime('2000-01-01')
    
    if not d_base.empty:
        d_base['period_dt'] = pd.to_datetime(d_base['period'])
        d_base = d_base.sort_values('period_dt')
        min_date = d_base['period_dt'].min()
        
        fig.add_trace(go.Scatter(
            x=d_base['period_dt'], y=d_base['ratio'], 
            name=base_bank_name, 
            line=dict(color=CHART_COLORS['base_bank'], width=4)
        ))
        
    # Peers
    peers = df_dom[df_dom['name'] != base_bank_name]['name'].unique()
    for peer in peers:
         d = df_dom[df_dom['name'] == peer].copy()
         d['period_dt'] = pd.to_datetime(d['period'])
         d = d.sort_values('period_dt')
         d = d[d['period_dt'] >= min_date]
         fig.add_trace(go.Scatter(
             x=d['period_dt'], y=d['ratio'], 
             name=peer, 
             line=dict(color=CHART_COLORS['peer'], dash='dot', width=1)
         ))
        
    # Benchmarks
    if benchmarks_df is not None and not benchmarks_df.empty:
        benchmarks_df['period_dt'] = pd.to_datetime(benchmarks_df['period'])
        benchmarks_df = benchmarks_df[benchmarks_df['period_dt'] >= min_date]
        
        for name in benchmarks_df['name'].unique():
            d = benchmarks_df[benchmarks_df['name'] == name].sort_values('period_dt')
            # Look for pre-calculated ratio
            if 'home_bias_ratio' in d.columns:
                 y_val = d['home_bias_ratio']
            elif 'cet1' in d.columns and 'amount' in d.columns:
                 y_val = d['amount'] / d['cet1']
            else:
                 y_val = [0] * len(d) # Fallback if data missing
            
            # Determine color
            c = CHART_COLORS['average']
            if "Domestic" in name: c = CHART_COLORS['domestic_avg']
            elif "EU" in name: c = CHART_COLORS['eu_avg']
            elif "G-SIB" in name or "O-SII" in name: c = CHART_COLORS['cat1'] # Regional?
            
            if 'home_bias_ratio' in d.columns:
                fig.add_trace(go.Scatter(
                    x=d['period_dt'], y=y_val, 
                    name=name, line=dict(color=c, dash='dash', width=2)
                ))

    fig.update_layout(yaxis_tickformat='.1%', hovermode="x unified")
    fig.update_layout(yaxis_tickformat='.1%', hovermode="x unified")
    return apply_standard_layout(fig, f"Home Bias Evolution (Domestic Exp / CET1)", 450, xaxis_type='date', periods=d_base['period'])
