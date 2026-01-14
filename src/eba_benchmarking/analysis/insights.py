import pandas as pd

def generate_insights(df_std, base_bank_name, df_market=None):
    """
    Generates rule-based insights comparing base bank to peers.
    Returns a list of strings (markdown formatted with icons).
    """
    insights = []
    
    if df_std.empty: return ["No financial data available for analysis."]
    
    # 1. Prepare Data
    latest = df_std['period'].max()
    df_lat = df_std[df_std['period'] == latest]
    
    base = df_lat[df_lat['name'] == base_bank_name]
    if base.empty: return ["Base bank data missing for latest period."]
    base = base.iloc[0]
    
    peers = df_lat[(df_lat['name'] != base_bank_name) & (~df_lat['name'].str.contains('Avg|Average', case=False, na=False))]
    
    if peers.empty:
        return ["Not enough peer data for comparative analysis."]

    peer_roe = peers['RoE (Annualized)'].median() if 'RoE (Annualized)' in peers.columns else None
    peer_npl = peers['npl_ratio'].median() if 'npl_ratio' in peers.columns else None
    peer_cet1 = peers['CET1 Ratio'].median() if 'CET1 Ratio' in peers.columns else None
    peer_ci = peers['Cost to Income'].median() if 'Cost to Income' in peers.columns else None
    peer_ldr = peers['LDR'].median() if 'LDR' in peers.columns else None
    
    # 2. Profitability Insight (RoE)
    roe = base.get('RoE (Annualized)', 0)
    if pd.notna(roe) and pd.notna(peer_roe):
        diff_roe = roe - peer_roe
        if abs(diff_roe) > 0.005: # 0.5% threshold
            perf = "outperforms" if diff_roe > 0 else "underperforms"
            icon = "🚀" if diff_roe > 0 else "📉"
            insights.append(f"{icon} **Profitability**: {base_bank_name} {perf} peers with an RoE of **{roe:.1%}** vs median **{peer_roe:.1%}**.")
            
    # Efficiency Insight (Cost to Income)
    ci = base.get('Cost to Income', 0)
    if pd.notna(ci) and pd.notna(peer_ci):
        diff_ci = ci - peer_ci
        # Lower is better
        if abs(diff_ci) > 0.01:
            perf = "more efficient" if diff_ci < 0 else "less efficient"
            icon = "⚙️" if diff_ci < 0 else "🐌"
            insights.append(f"{icon} **Efficiency**: {base_bank_name} is {perf}, with a Cost-to-Income ratio of **{ci:.1%}** (Peer Median: {peer_ci:.1%}).")
    
    # 3. Asset Quality Insight (NPL)
    npl = base.get('npl_ratio', 0)
    if pd.notna(npl) and pd.notna(peer_npl):
        diff_npl = npl - peer_npl
        # Lower NPL is better
        if abs(diff_npl) > 0.002: # 0.2% threshold
            perf = "stronger" if diff_npl < 0 else "weaker"
            icon = "🛡️" if diff_npl < 0 else "⚠️"
            insights.append(f"{icon} **Asset Quality**: {perf.title()} low-risk profile; NPL Ratio of **{npl:.1%}** is {'lower' if diff_npl < 0 else 'higher'} than peer median (**{peer_npl:.1%}**).")
        
    # 4. Solvency Insight (CET1)
    cet1 = base.get('CET1 Ratio', 0)
    if pd.notna(cet1) and pd.notna(peer_cet1):
        diff_cet1 = cet1 - peer_cet1
        if abs(diff_cet1) > 0.005:
            perf = "Robust" if diff_cet1 > 0 else "Tighter"
            icon = "🏛️" if diff_cet1 > 0 else "💸"
            insights.append(f"{icon} **Capital**: {perf} capital buffer with CET1 at **{cet1:.1%}** vs peer median of **{peer_cet1:.1%}**.")

    # 5. Liquidity (LDR)
    ldr = base.get('LDR', 0)
    if pd.notna(ldr) and pd.notna(peer_ldr):
        diff_ldr = ldr - peer_ldr
        if abs(diff_ldr) > 0.05:
            state = "higher" if diff_ldr > 0 else "lower"
            # LDR interpretation depends on model, but generally high LDR = tight liquidity
            icon = "💧"
            insights.append(f"{icon} **Liquidity**: Loan-to-Deposit Ratio is {state} than peers (**{ldr:.1%}** vs **{peer_ldr:.1%}**).")

    # 5. Market Valuation (P/B)
    if df_market is not None and not df_market.empty:
        m_base = df_market[df_market['name'] == base_bank_name]
        if not m_base.empty:
            pb = m_base.iloc[0].get('price_to_book')
            
            m_peers = df_market[df_market['name'] != base_bank_name]
            if pd.notna(pb) and not m_peers.empty:
                peer_pb = m_peers['price_to_book'].median()
                if pd.notna(peer_pb):
                    diff_pb = pb - peer_pb
                    if abs(diff_pb) > 0.05:
                        val_state = "premium" if diff_pb > 0 else "discount"
                        icon = "💎" if diff_pb > 0 else "🏷️"
                        insights.append(f"{icon} **Valuation**: Trading at a {val_state} to peers (P/B **{pb:.2f}x** vs **{peer_pb:.2f}x**).")

    return insights
