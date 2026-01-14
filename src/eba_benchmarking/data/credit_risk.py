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
    
    # Updated columns based on actual schema: 
    # id, lei, period, item_id, portfolio, country, exposure, status, perf_status, nace_codes, amount
    filter_cols = [
        'portfolio', 
        'exposure', 
        'status', 
        'perf_status', 
        'country', 
        'nace_codes',
        'item_id' 
    ]
    
    options = {}
    
    try:
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
    
    if filters:
        for col, values in filters.items():
            if values:
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
        f.exposure, 
        f.status, 
        f.perf_status, 
        f.country, 
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
