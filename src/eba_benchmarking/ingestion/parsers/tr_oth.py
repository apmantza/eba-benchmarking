from eba_benchmarking.ingestion.parsers.base import BaseParser

def main():
    col_mapping_rules = {
        'lei': ['LEI_code', 'LEI_Code', 'lei'],
        'period': ['Period', 'period'],
        'item_id': ['Item', 'item'],
        'amount': ['Amount', 'amount'],
        'nsa': ['NSA', 'nsa'],
        'assets_fv': ['ASSETS_FV', 'assets_fv'],
        'assets_stages': ['ASSETS_Stages', 'assets_stages'],
        'exposure': ['Exposure', 'exposure'],
        'financial_instruments': ['Financial_instruments', 'financial_instruments']
    }

    create_sql = '''
    CREATE TABLE IF NOT EXISTS facts_oth (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lei TEXT,
        period TEXT,
        item_id TEXT,
        nsa TEXT,
        assets_fv INTEGER,
        assets_stages INTEGER,
        exposure INTEGER,
        financial_instruments INTEGER,
        amount REAL,
        FOREIGN KEY(lei) REFERENCES institutions(lei),
        FOREIGN KEY(item_id) REFERENCES dictionary(item_id)
    )
    '''

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_oth_lei ON facts_oth(lei)",
        "CREATE INDEX IF NOT EXISTS idx_oth_item ON facts_oth(item_id)",
        "CREATE INDEX IF NOT EXISTS idx_oth_instrument ON facts_oth(financial_instruments)",
        "CREATE INDEX IF NOT EXISTS idx_oth_period ON facts_oth(period)"
    ]

    # Note: 'exposure', 'assets_fv' etc are integers in OTH too, but base parser handles them if in 'int' list
    dtype_conversions = {
        'int': ['assets_fv', 'assets_stages', 'exposure', 'financial_instruments']
    }

    parser = BaseParser(
        table_name='facts_oth',
        file_pattern_prefix='tr_oth',
        col_mapping_rules=col_mapping_rules,
        create_table_sql=create_sql,
        index_sqls=indexes,
        dtype_conversions=dtype_conversions
    )
    
    parser.run()

if __name__ == '__main__':
    main()
