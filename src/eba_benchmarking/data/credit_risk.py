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
    Returns a dictionary of column_name -> list of values (as strings).
    Use these IDs to look up labels in the UI.
    """
    if not lei_list or not os.path.exists(DB_NAME):
        return {}

    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    
    # Columns in facts_cre
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
            # Ensure we return strings to match filter keys
            options[col] = [str(x) for x in df_col[col].tolist()]
            
    except Exception as e:
        st.error(f"Error fetching filter options: {e}")
    finally:
        conn.close()
        
    return options

@st.cache_data
def get_dim_maps():
    """
    Fetches all relevant dimension mappings (id -> label).
    Returns a dict of dicts: { 'dim_table': {id: label, ...}, ... }
    Includes 'item_id' from the 'dictionary' table.
    """
    if not os.path.exists(DB_NAME):
        return {}
    
    conn = sqlite3.connect(DB_NAME)
    maps = {}
    
    # Define mapping: fact_column -> (dim_table, id_col, label_col)
    dim_configs = {
        'portfolio': ('dim_portfolio', 'portfolio', 'label'),
        'exposure': ('dim_exposure', 'exposure', 'label'),
        'status': ('dim_status', 'status', 'label'),
        'perf_status': ('dim_perf_status', 'perf_status', 'label'),
        'country': ('dim_country', 'country', 'label'),
        'nace_codes': ('dim_nace_codes', 'nace_codes', 'label'),
        'item_id': ('dictionary', 'item_id', 'label')  # Added dictionary map
    }
    
    try:
        for key, (table, id_col, label_col) in dim_configs.items():
            try:
                # Some tables might not exist or columns might differ slightly, fail gracefully per table
                df = pd.read_sql(f"SELECT {id_col}, {label_col} FROM {table}", conn)
                maps[key] = pd.Series(df[label_col].values, index=df[id_col].astype(str)).to_dict()
            except Exception:
                maps[key] = {}
        
    except Exception as e:
        st.error(f"Error fetching dimension maps: {e}")
    finally:
        conn.close()

    return maps

@st.cache_data
def get_cre_data(lei_list, filters=None):
    """
    Fetches data from facts_cre based on selected LEIs and filters.
    Joins with dimension tables to return human-readable labels where possible.
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
    
    # Updated query to left join 'dictionary' for item labels
    query = f"""
    SELECT 
        f.lei, 
        i.commercial_name as Bank, 
        f.period, 
        
        f.item_id,
        COALESCE(d.label, f.item_id) as "Item Label",
        
        f.portfolio,
        COALESCE(dp.label, f.portfolio) as "Portfolio Label",
        
        f.exposure,
        COALESCE(de.label, f.exposure) as "Exposure Label",
        
        f.status,
        COALESCE(ds.label, f.status) as "Status Label",
        
        f.perf_status,
        COALESCE(dps.label, f.perf_status) as "Perf Status Label",
        
        f.country,
        COALESCE(dc.label, f.country) as "Country Label",
        
        f.nace_codes,
        COALESCE(dn.label, f.nace_codes) as "NACE Label",
        
        f.amount
        
    FROM facts_cre f
    JOIN institutions i ON f.lei = i.lei
    
    LEFT JOIN dictionary d ON f.item_id = d.item_id
    LEFT JOIN dim_portfolio dp ON f.portfolio = dp.portfolio
    LEFT JOIN dim_exposure de ON f.exposure = de.exposure
    LEFT JOIN dim_status ds ON f.status = ds.status
    LEFT JOIN dim_perf_status dps ON f.perf_status = dps.perf_status
    LEFT JOIN dim_country dc ON f.country = dc.country
    LEFT JOIN dim_nace_codes dn ON f.nace_codes = dn.nace_codes
    
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
