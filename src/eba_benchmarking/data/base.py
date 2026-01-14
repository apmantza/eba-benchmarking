import pandas as pd
import sqlite3
import streamlit as st
import os
from ..config import DB_NAME

MIN_PERIOD = '2020-01-01'

@st.cache_data
def get_master_data():
    """Load the master list of banks with their metadata."""
    if not os.path.exists(DB_NAME):
        st.error(f"Database file '{DB_NAME}' not found.")
        return pd.DataFrame()
        
    conn = sqlite3.connect(DB_NAME)
    try:
        query = """
        SELECT 
            i.lei, 
            i.name, 
            i.commercial_name,
            i.short_name,
            i.country_iso, 
            i.country_name,
            i.region,
            i.Systemic_Importance,
            COALESCE(b.business_model, 'Unclassified') as business_model,
            COALESCE(b.size_category, 'Unknown') as size_category,
            COALESCE(b.total_assets, 0) as total_assets
        FROM institutions i
        LEFT JOIN bank_models b ON i.lei = b.lei
        ORDER BY i.commercial_name
        """
        df = pd.read_sql(query, conn)
        df = df[df['commercial_name'].notna()].copy()
    except Exception as e:
        st.warning(f"Note: Could not load business models ({e}). Defaulting to basic list.")
        df = pd.read_sql("SELECT lei, name, commercial_name, short_name, country_iso, country_name, region, 'Other' as Systemic_Importance, 'Unknown' as business_model FROM institutions WHERE commercial_name IS NOT NULL ORDER BY commercial_name", conn)
    finally:
        conn.close()
    return df

@st.cache_data
def get_benchmark_leis(country_iso, region, systemic_importance, size_category=None):
    """
    Returns dict of peer group LEI lists based on size classification.
    
    Groups:
    - Domestic Avg: Same country banks (incl. Bank of Cyprus for GR)
    - Regional (Same Size): Same region, same size category
    - EU (Same Size): All EU banks with same size category
    - EU Large: All EU banks with Large + Huge size categories
    
    Excludes banks with no size_category data.
    """
    # Bank of Cyprus LEI (ATHEX-listed, treated as domestic for Greek banks)
    ATHEX_PEER_LEIS = ['635400L14KNHZXPUZM19']
    
    if not os.path.exists(DB_NAME):
        return {}
    
    conn = sqlite3.connect(DB_NAME)
    try:
        query = """
            SELECT lei, country_iso, region, Systemic_Importance, size_category
            FROM institutions
            WHERE size_category IS NOT NULL
        """
        df = pd.read_sql(query, conn)
    except:
        conn.close()
        return {}
    conn.close()
    
    if df.empty:
        return {}
    
    # Domestic: Same country OR Bank of Cyprus for Greek banks
    if country_iso == 'GR':
        dom = df[
            (df['country_iso'] == country_iso) | 
            (df['lei'].isin(ATHEX_PEER_LEIS))
        ]['lei'].tolist()
    else:
        dom = df[
            df['country_iso'] == country_iso
        ]['lei'].tolist()
    
    # Regional (Same Size): Same region, different country, same size
    if size_category:
        reg_same_size = df[
            (df['region'] == region) & 
            (df['country_iso'] != country_iso) &
            (df['size_category'] == size_category)
        ]['lei'].tolist()
    else:
        reg_same_size = []
    
    # EU (Same Size): All EU with same size category
    if size_category:
        eu_same_size = df[
            df['size_category'] == size_category
        ]['lei'].tolist()
    else:
        eu_same_size = []
    
    # EU Large: All Large + Huge banks
    eu_large = df[
        df['size_category'].isin(['Large (200-500bn)', 'Huge (>500bn)'])
    ]['lei'].tolist()
    
    return {
        "Domestic Avg": dom,
        "Regional (Same Size)": reg_same_size,
        "EU (Same Size)": eu_same_size,
        "EU Large": eu_large
    }

