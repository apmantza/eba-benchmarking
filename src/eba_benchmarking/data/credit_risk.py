import pandas as pd
import sqlite3
import os
import streamlit as st
from ..config import DB_NAME
from .base import MIN_PERIOD

@st.cache_data
def get_cre_filter_options(lei_list):
    """
    Fetches distinct values for filterable columns in facts_cre for the selected LEIs.
    Returns a dictionary of column_name -> list of values.
    """
    if not lei_list or not os.path.exists(DB_NAME):
        return {}

    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    
    # Columns we want distinct values for
    filter_cols = [
        'portfolio', 
        'exposure_class', 
        'counterparty_sector', 
        'status', 
        'perf_status', 
        'residence', 
        'nace_codes',
        'item_id' 
    ]
    
    options = {}
    
    try:
        # We can do this in one pass or multiple. 
        # Multiple queries is likely safer/easier to map.
        for col in filter_cols:
            query = f"""
            SELECT DISTINCT {col} 
            FROM facts_cre 
            WHERE lei IN ({leis_str}) 
            AND {col} IS NOT NULL 
            ORDER BY {col}
            """
            df_col = pd.read_sql(query, conn)
            options[col] = df_col[col].tolist()
            
    except Exception as e:
        st.error(f"Error fetching filter options: {e}")
    finally:
        conn.close()
        
    return options

@st.cache_data
def get_cre_data(lei_list, filters=None):
    """
    Fetches data from facts_cre based on selected LEIs and filters.
    filters: dict of col_name -> list of selected values (or empty for all).
    """
    if not lei_list or not os.path.exists(DB_NAME):
        return pd.DataFrame()

    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    
    where_clauses = [f"f.lei IN ({leis_str})"]
    where_clauses.append(f"f.period >= '{MIN_PERIOD}'")
    
    params = []
    
    if filters:
        for col, values in filters.items():
            if values:
                # Handle potentially large lists or lists needing escaping
                # Using parameter substitution is safest but variable list length is tricky in raw SQL string
                # We'll construct the IN clause string carefully
                
                # Filter out None/Empty if any
                valid_vals = [str(v) for v in values if v is not None]
                if not valid_vals:
                    continue
                    
                val_list_str = "'" + "','".join(valid_vals) + "'"
                where_clauses.append(f"f.{col} IN ({val_list_str})")
    
    where_sql = " AND ".join(where_clauses)
    
    query = f"""
    SELECT 
        f.lei, 
        i.commercial_name as Bank, 
        f.period, 
        f.item_id, 
        f.portfolio, 
        f.exposure_class, 
        f.counterparty_sector, 
        f.status, 
        f.perf_status, 
        f.residence, 
        f.nace_codes,
        f.amount
    FROM facts_cre f
    JOIN institutions i ON f.lei = i.lei
    WHERE {where_sql}
    ORDER BY f.period DESC, i.commercial_name
    """
    
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error fetching Credit Risk data: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
        
    return df
