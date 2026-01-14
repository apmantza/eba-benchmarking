

@st.cache_data
def get_available_metrics_for_explorer():
    """
    Returns a DataFrame of available metrics from dictionary for the explorer.
    """
    if not os.path.exists(DB_NAME):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT item_id, label, category 
    FROM dictionary 
    WHERE item_id IN (SELECT DISTINCT item_id FROM facts_oth)
    ORDER BY category, label
    """
    try:
        df = pd.read_sql(query, conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df
