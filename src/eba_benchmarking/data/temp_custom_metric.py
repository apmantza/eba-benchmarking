
def get_custom_metric_data(item_id, item_label, lei_list):
    """
    Fetches a specific item for a list of LEIs from facts_oth.
    Returns a DataFrame with aggregated amounts (summing over dimensions).
    """
    if not lei_list or not os.path.exists(DB_NAME):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    
    # We aggregate (SUM) over all dimensions for simplicity in this explorer
    query = f"""
    SELECT lei, period, SUM(amount) as value
    FROM facts_oth
    WHERE lei IN ({leis_str})
      AND item_id = '{item_id}'
      AND period >= '{MIN_PERIOD}'
    GROUP BY lei, period
    """
    
    try:
        df = pd.read_sql(query, conn)
    except:
        conn.close()
        return pd.DataFrame()

    # Also fetch Total Assets for normalization
    query_assets = f"""
    SELECT lei, period, SUM(amount) as assets
    FROM facts_oth
    WHERE lei IN ({leis_str})
      AND item_id = '2521010'
      AND period >= '{MIN_PERIOD}'
    GROUP BY lei, period
    """
    try:
        df_assets = pd.read_sql(query_assets, conn)
        df = pd.merge(df, df_assets, on=['lei', 'period'], how='left')
    except:
        df['assets'] = 1
        
    conn.close()
    return df
