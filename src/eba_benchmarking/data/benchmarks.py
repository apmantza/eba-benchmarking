import pandas as pd
import sqlite3
import streamlit as st
import os
from ..config import DB_NAME
from .base import MIN_PERIOD

@st.cache_data
def get_macro_data(country_iso):
    """Fetches macroeconomic indicators."""
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    try:
        df_m = pd.read_sql(f"SELECT period, indicator, value, source FROM macro_economics WHERE country = '{country_iso}'", conn)
        if country_iso == 'GR': df_m = pd.concat([df_m, pd.read_sql("SELECT date as period, metric as indicator, value, 'Bank of Greece' as source FROM bog_macro", conn)], ignore_index=True)
        return df_m
    except: return pd.DataFrame()
    finally: conn.close()

@st.cache_data
def get_ecb_benchmarks(country_iso, business_model):
    """Fetches ECB supervisory statistics."""
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    try:
        return pd.read_sql(f"SELECT period, variable, group_type, group_name, value FROM ecb_stats WHERE (group_type = 'Country' AND group_name = '{country_iso}') OR (group_type = 'Business Model')", conn)
    except: return pd.DataFrame()
    finally: conn.close()

@st.cache_data
def get_eba_kris(country_iso):
    """Fetches EBA country-level Key Risk Indicators."""
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    try:
        return pd.read_sql(f"SELECT period, kri_name, value, country FROM eba_kris WHERE country IN ('{country_iso}', 'EU') AND period >= '{MIN_PERIOD}'", conn)
    except: return pd.DataFrame()
    finally: conn.close()
