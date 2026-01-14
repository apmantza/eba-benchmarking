import pytest
from unittest.mock import patch
import pandas as pd
import sqlite3
from eba_benchmarking.data import get_master_data, get_financial_data
from eba_benchmarking.data.generic import get_tab_data

def test_get_master_data(temp_db):
    """Test fetching the master list of banks."""
    
    # Patch the DB_NAME in the module to point to our temp DB
    with patch('eba_benchmarking.data.base.DB_NAME', temp_db):
        df = get_master_data()
        
    assert not df.empty
    assert len(df) == 2
    assert 'Bank A' in df['name'].values
    assert 'Bank B' in df['name'].values
    assert 'Universal' in df[df['name'] == 'Bank A']['business_model'].values[0]

def test_get_financial_data(temp_db):
    """Test fetching financial data (CET1 Ratio)."""
    
    leis = ['LEI1', 'LEI2']
    
    with patch('eba_benchmarking.data.generic.DB_NAME', temp_db):
        df = get_financial_data(leis)
        
    assert not df.empty
    # Pivot logic in get_financial_data creates columns for KPIs
    assert 'CET1 Ratio' in df.columns
    
    # Check values
    row_a = df[df['lei'] == 'LEI1'].iloc[0]
    assert row_a['CET1 Ratio'] == 0.15
    
    row_b = df[df['lei'] == 'LEI2'].iloc[0]
    assert row_b['CET1 Ratio'] == 0.12

def test_get_financial_data_empty(temp_db):
    """Test fetching with empty list."""
    with patch('eba_benchmarking.data.generic.DB_NAME', temp_db):
        df = get_financial_data([])
    assert df.empty

def test_get_tab_data(temp_db):
    """Test fetching tab data with the optimized query logic."""
    
    # Setup specific data for this test in the temp DB
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # 1. Populate Dictionary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dictionary (
            item_id TEXT, label TEXT, template TEXT, category TEXT, tab_name TEXT
        )
    ''')
    cursor.execute("INSERT INTO dictionary VALUES ('2520140', 'CET1 Ratio', 'Capital', 'Capital', 'Solvency')")
    cursor.execute("INSERT INTO dictionary VALUES ('9999999', 'Fake Item', 'Capital', 'Capital', 'Solvency')") # Missing in facts
    
    conn.commit()
    conn.close()
    
    leis = ['LEI1']
    
    with patch('eba_benchmarking.data.generic.DB_NAME', temp_db):
        # 'Solvency' tab maps to 'Capital' template -> 'facts_oth'
        df = get_tab_data('Solvency', leis)
        
    assert not df.empty
    assert 'CET1 Ratio' in df['label'].values
    assert '2520140' in df['item_id'].values
    # Check that we joined correctly
    row = df[df['item_id'] == '2520140'].iloc[0]
    assert row['amount'] == 0.15