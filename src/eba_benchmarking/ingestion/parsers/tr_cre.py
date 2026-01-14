from eba_benchmarking.ingestion.parsers.base import BaseParser

def main():
    col_mapping_rules = {
        'lei': ['LEI_code', 'LEI_Code', 'lei_code', 'LEI'],
        'period': ['Period', 'period', 'PERIOD'],
        'item_id': ['Item', 'item', 'ITEM'],
        'portfolio': ['Portfolio', 'portfolio', 'PORTFOLIO'],
        'country': ['Country', 'country', 'COUNTRY'],
        'exposure': ['Exposure', 'exposure', 'EXPOSURE'],
        'status': ['Status', 'status', 'STATUS'],
        'perf_status': ['Perf_Status', 'Perf_status', 'perf_status'],
        'nace_codes': ['NACE_codes', 'NACE_Codes', 'nace_codes'],
        'amount': ['Amount', 'amount', 'AMOUNT']
    }

    create_sql = '''
    CREATE TABLE IF NOT EXISTS facts_cre (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lei TEXT,
        period INTEGER,
        item_id TEXT,
        portfolio INTEGER,
        country TEXT,
        exposure INTEGER,
        status INTEGER,
        perf_status INTEGER,
        nace_codes INTEGER,
        amount REAL,
        FOREIGN KEY(lei) REFERENCES institutions(lei),
        FOREIGN KEY(item_id) REFERENCES dictionary(item_id)
    )
    '''

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_cre_lei ON facts_cre(lei)",
        "CREATE INDEX IF NOT EXISTS idx_cre_item ON facts_cre(item_id)",
        "CREATE INDEX IF NOT EXISTS idx_cre_period ON facts_cre(period)"
    ]

    dtype_conversions = {
        'int': ['portfolio', 'exposure', 'status', 'perf_status', 'nace_codes']
    }

    parser = BaseParser(
        table_name='facts_cre',
        file_pattern_prefix='tr_cre',
        col_mapping_rules=col_mapping_rules,
        create_table_sql=create_sql,
        index_sqls=indexes,
        dtype_conversions=dtype_conversions
    )
    
    parser.run()

if __name__ == '__main__':
    main()
