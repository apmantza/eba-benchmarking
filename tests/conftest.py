import pytest
import sys
import os
import sqlite3

# Add 'src' to sys.path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

@pytest.fixture
def temp_db(tmp_path):
    """
    Creates a temporary database file and returns its path.
    Also initializes the basic schema needed for testing.
    """
    db_file = tmp_path / "test_eba_data.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create 'institutions' table matching ebadb.py
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS institutions (
        lei TEXT PRIMARY KEY,
        name TEXT,
        country_iso TEXT,
        country_name TEXT,
        commercial_name TEXT,
        short_name TEXT,
        ticker TEXT
    )
    ''')
    
    # Create 'bank_models' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bank_models (
        lei TEXT,
        business_model TEXT,
        size_category TEXT,
        total_assets REAL
    )
    ''')

    # Create 'facts_oth' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS facts_oth (
        lei TEXT,
        period TEXT,
        item_id TEXT,
        amount REAL
    )
    ''')
    
    # Create 'facts_cre' table (needed for get_financial_data joins)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS facts_cre (
        lei TEXT,
        period TEXT,
        item_id TEXT,
        amount REAL,
        perf_status INTEGER
    )
    ''')

    # Insert Dummy Data with commercial_name populated
    cursor.execute("INSERT INTO institutions (lei, name, country_iso, commercial_name, short_name) VALUES ('LEI1', 'Bank A', 'DE', 'Bank A Commercial', 'Bank A')")
    cursor.execute("INSERT INTO institutions (lei, name, country_iso, commercial_name, short_name) VALUES ('LEI2', 'Bank B', 'FR', 'Bank B Commercial', 'Bank B')")
    
    cursor.execute("INSERT INTO bank_models (lei, business_model, size_category, total_assets) VALUES ('LEI1', 'Universal', 'Large', 100000)")
    cursor.execute("INSERT INTO bank_models (lei, business_model, size_category, total_assets) VALUES ('LEI2', 'Retail', 'Small', 50000)")
    
    # Insert Dummy Financials (CET1 Ratio item_id = '2520140')
    # Use string format for period to match likely usage
    cursor.execute("INSERT INTO facts_oth (lei, period, item_id, amount) VALUES ('LEI1', '202312', '2520140', 0.15)")
    cursor.execute("INSERT INTO facts_oth (lei, period, item_id, amount) VALUES ('LEI2', '202312', '2520140', 0.12)")

    conn.commit()
    conn.close()
    
    return str(db_file)