import pandas as pd
import sqlite3
import os
import streamlit as st
from ..config import DB_NAME
from .base import MIN_PERIOD

@st.cache_data
def get_mrk_filter_options(lei_list):
    """
    Fetches distinct values for filterable columns in facts_mrk for the selected LEIs.
    Returns a dictionary of column_name -> list of values (as strings).
    """
    if not lei_list or not os.path.exists(DB_NAME):
        return {}

    conn = sqlite3.connect(DB_NAME)
    leis_str = "'" + "','".join([str(lei) for lei in lei_list]) + "'"
    
    filter_cols = [
        'portfolio', 
        'mkt_prod', 
        'mkt_risk', 
        'item_id'
    ]
    
    options = {}
    
    try:
        for col in filter_cols:
            query = f"""
            SELECT DISTINCT {col} 
            FROM facts_mrk 
            WHERE lei IN ({leis_str}) 
            AND {col} IS NOT NULL 
            ORDER BY {col}
            """
            df_col = pd.read_sql(query, conn)
            options[col] = [str(x) for x in df_col[col].tolist()]
            
    except Exception as e:
        st.error(f"Error fetching filter options: {e}")
    finally:
        conn.close()
        
    return options

@st.cache_data
def get_mrk_dim_maps():
    """
    Fetches all relevant dimension mappings (id -> label) for Market Risk.
    """
    if not os.path.exists(DB_NAME):
        return {}
    
    conn = sqlite3.connect(DB_NAME)
    maps = {}
    
    # Mapping: filter_key -> (dim_table, id_col, label_col)
    # facts_mrk.mkt_prod -> dim_mkt_modprod.mkt_modprod (assuming column name is mkt_modprod or similar)
    # facts_mrk.mkt_risk -> dim_mkt_risk.mkt_risk
    
    # We should verify column names in dim tables first if guessing.
    # Assuming standard pattern: table dim_X has column X.
    # dim_mkt_modprod likely has `mkt_modprod` column.
    
    dim_configs = {
        'portfolio': ('dim_portfolio', 'portfolio', 'label'),
        'mkt_prod': ('dim_mkt_modprod', 'mkt_modprod', 'label'),
        'mkt_risk': ('dim_mkt_risk', 'mkt_risk', 'label')
    }
    
    try:
        for key, (table, id_col, label_col) in dim_configs.items():
            try:
                df = pd.read_sql(f"SELECT {id_col}, {label_col} FROM {table}", conn)
                maps[key] = pd.Series(df[label_col].values, index=df[id_col].astype(str)).to_dict()
            except Exception:
                maps[key] = {} # Fail gracefully
                
    except Exception as e:
        st.error(f"Error fetching dimension maps: {e}")
    finally:
        conn.close()

    return maps

@st.cache_data
def get_mrk_data(lei_list, filters=None):
    """
    Fetches data from facts_mrk based on selected LEIs and filters.
    Joins with dimension tables.
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
        COALESCE(dp.label, f.portfolio) as "Portfolio Label",
        
        f.mkt_prod,
        COALESCE(dmp.label, f.mkt_prod) as "Product Label",
        
        f.mkt_risk,
        COALESCE(dmr.label, f.mkt_risk) as "Risk Label",
        
        f.amount
        
    FROM facts_mrk f
    JOIN institutions i ON f.lei = i.lei
    
    LEFT JOIN dim_portfolio dp ON f.portfolio = dp.portfolio
    LEFT JOIN dim_mkt_modprod dmp ON f.mkt_prod = dmp.mkt_modprod
    LEFT JOIN dim_mkt_risk dmr ON f.mkt_risk = dmr.mkt_risk
    
    WHERE {where_sql}
    ORDER BY f.period DESC, i.commercial_name
    """
    
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error fetching Market Risk data: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
        
    return df
