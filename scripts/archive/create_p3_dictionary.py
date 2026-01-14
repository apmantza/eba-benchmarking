import sqlite3

conn = sqlite3.connect('eba_data.db')
cur = conn.cursor()

print("=== Creating pillar3_dictionary Table ===\n")

# First check if table exists and its structure
cur.execute("PRAGMA table_info(pillar3_dictionary)")
existing = cur.fetchall()
print(f"Existing table info: {existing}")

# Drop and recreate with proper structure
cur.execute("DROP TABLE IF EXISTS pillar3_dictionary")

cur.execute("""
    CREATE TABLE pillar3_dictionary (
        p3_item_id TEXT PRIMARY KEY,  -- e.g. 'KM1.1', 'CC1.29'
        template_code TEXT NOT NULL,
        row_id TEXT NOT NULL,
        p3_label TEXT,
        eba_item_id TEXT,             -- Reference to dictionary.item_id
        notes TEXT,
        UNIQUE(template_code, row_id)
    )
""")
print("Created pillar3_dictionary table")

# Get existing mappings from TEMPLATE_ROWS in the parser
mappings = [
    # KM1 - Key Metrics
    ('KM1.1', 'KM1', '1', 'CET1 Capital', '2520102'),
    ('KM1.2', 'KM1', '2', 'Tier 1 Capital', '2520133'),
    ('KM1.3', 'KM1', '3', 'Total Capital', '2520101'),
    ('KM1.4', 'KM1', '4', 'Total RWA', '2520138'),
    ('KM1.4a', 'KM1', '4a', 'Total RWA pre-floor', '2520154'),
    ('KM1.5', 'KM1', '5', 'CET1 Ratio', '2520146'),
    ('KM1.5b', 'KM1', '5b', 'CET1 Ratio (unfloored)', '2520146'),
    ('KM1.6', 'KM1', '6', 'Tier 1 Ratio', '2520141'),
    ('KM1.6b', 'KM1', '6b', 'Tier 1 Ratio (unfloored)', '2520141'),
    ('KM1.7', 'KM1', '7', 'Total Capital Ratio', '2520142'),
    ('KM1.7b', 'KM1', '7b', 'Total Capital Ratio (unfloored)', '2520142'),
    ('KM1.8', 'KM1', '8', 'Capital Conservation Buffer', None),
    ('KM1.9', 'KM1', '9', 'Countercyclical Buffer', None),
    ('KM1.11', 'KM1', '11', 'Combined Buffer Requirement', None),
    ('KM1.13', 'KM1', '13', 'Leverage Ratio Exposure', '2520903'),
    ('KM1.14', 'KM1', '14', 'Leverage Ratio', '2520905'),
    ('KM1.15', 'KM1', '15', 'Total HQLA', None),
    ('KM1.17', 'KM1', '17', 'LCR Ratio', None),
    ('KM1.18', 'KM1', '18', 'Available Stable Funding', None),
    ('KM1.20', 'KM1', '20', 'NSFR Ratio', None),
    
    # CC1 - Capital Composition
    ('CC1.1', 'CC1', '1', 'Capital Instruments', '2520103'),
    ('CC1.2', 'CC1', '2', 'Retained Earnings', '2520104'),
    ('CC1.3', 'CC1', '3', 'AOCI', '2520105'),
    ('CC1.4', 'CC1', '4', 'Other Reserves', '2520106'),
    ('CC1.EU-3a', 'CC1', 'EU-3a', 'Funds for general banking risk', '2520107'),
    ('CC1.5', 'CC1', '5', 'Minority Interests in CET1', '2520108'),
    ('CC1.7', 'CC1', '7', 'Prudent Valuation Adjustments', '2520109'),
    ('CC1.8', 'CC1', '8', 'Intangible assets', '2520110'),
    ('CC1.10', 'CC1', '10', 'DTAs future profitability', '2520111'),
    ('CC1.15', 'CC1', '15', 'Defined-benefit pension fund assets', '2520112'),
    ('CC1.16', 'CC1', '16', 'Holdings of CET1 of fin sector entities', '2520113'),
    ('CC1.17', 'CC1', '17', 'Cross holdings in CET1', '2520114'),
    ('CC1.18', 'CC1', '18', 'Excess deduction from AT1', '2520115'),
    ('CC1.21', 'CC1', '21', 'DTAs from temporary differences', '2520116'),
    ('CC1.22', 'CC1', '22', 'Amount exceeding 17.65% threshold', '2520121'),
    ('CC1.27a', 'CC1', '27a', 'Other regulatory adjustments CET1', '2520123'),
    ('CC1.29', 'CC1', '29', 'CET1 Capital', '2520102'),
    ('CC1.30', 'CC1', '30', 'AT1 Capital instruments', '2520129'),
    ('CC1.41', 'CC1', '41', 'Excess deduction from T2', '2520130'),
    ('CC1.44', 'CC1', '44', 'Tier 1 Capital', '2520133'),
    ('CC1.45', 'CC1', '45', 'Tier 2 instruments', '2520135'),
    ('CC1.56', 'CC1', '56', 'Other T2 adjustments', '2520136'),
    ('CC1.58', 'CC1', '58', 'Total Capital', '2520101'),
    ('CC1.59', 'CC1', '59', 'Total RWA', '2520138'),
    ('CC1.60', 'CC1', '60', 'CET1 Ratio', '2520140'),
    ('CC1.61', 'CC1', '61', 'Tier 1 Ratio', '2520141'),
    ('CC1.62', 'CC1', '62', 'Total Capital Ratio', '2520142'),
    
    # OV1 - RWA Overview
    ('OV1.1', 'OV1', '1', 'Credit Risk excl CCR', '2520201'),
    ('OV1.2', 'OV1', '2', 'Of which SA', '2520202'),
    ('OV1.3', 'OV1', '3', 'Of which FIRB', '2520203'),
    ('OV1.4', 'OV1', '4', 'Of which Slotting', '2520204'),
    ('OV1.5', 'OV1', '5', 'Of which Equities IRB', '2520205'),
    ('OV1.6', 'OV1', '6', 'Counterparty Credit Risk', '2520206'),
    ('OV1.10', 'OV1', '10', 'CVA Risk', '2520207'),
    ('OV1.15', 'OV1', '15', 'Settlement Risk', '2520208'),
    ('OV1.16', 'OV1', '16', 'Securitisation Banking Book', '2520209'),
    ('OV1.20', 'OV1', '20', 'Position FX Commodities Risk', '2520210'),
    ('OV1.21', 'OV1', '21', 'Market Risk SA', '2520211'),
    ('OV1.22', 'OV1', '22', 'Market Risk IMA', '2520212'),
    ('OV1.24', 'OV1', '24', 'Operational Risk', '2520215'),
    ('OV1.25', 'OV1', '25', 'Operational Risk SA', '2520217'),
    ('OV1.29', 'OV1', '29', 'Total RWA', '2520220'),
    
    # CR1 - Credit Risk
    ('CR1.1', 'CR1', '1', 'Loans and advances', '2520603'),
    ('CR1.2', 'CR1', '2', 'Debt securities', '2520602'),
    ('CR1.3', 'CR1', '3', 'Off-balance sheet', '2520606'),
    ('CR1.Total', 'CR1', 'Total', 'Total gross carrying amount', '2520601'),
    
    # LR - Leverage Ratio
    ('LR1.13', 'LR1', '13', 'Leverage Ratio Exposure', '2520903'),
    ('LR2.20', 'LR2', '20', 'Leverage Ratio', '2520905'),
    ('LR3.13', 'LR3', '13', 'Leverage Ratio Exposure', '2520903'),
    
    # KM2 - MREL
    ('KM2.EU-1a', 'KM2', 'EU-1a', 'Own Funds', '2520101'),
    ('KM2.2', 'KM2', '2', 'Total RWA', '2520138'),
    ('KM2.4', 'KM2', '4', 'Total exposure measure', '2520903'),
]

cur.executemany("""
    INSERT OR REPLACE INTO pillar3_dictionary 
    (p3_item_id, template_code, row_id, p3_label, eba_item_id)
    VALUES (?, ?, ?, ?, ?)
""", mappings)

conn.commit()
print(f"Inserted {len(mappings)} mappings into pillar3_dictionary")

# Show summary
print("\n=== pillar3_dictionary Contents ===")
cur.execute("""
    SELECT p.p3_item_id, p.p3_label, p.eba_item_id, d.label as eba_label
    FROM pillar3_dictionary p
    LEFT JOIN dictionary d ON p.eba_item_id = d.item_id
    ORDER BY p.template_code, 
        CASE WHEN p.row_id GLOB '[0-9]*' THEN CAST(p.row_id AS INTEGER) ELSE 999 END,
        p.row_id
""")
for r in cur.fetchall():
    eba_label = r[3][:40] if r[3] else 'N/A'
    print(f"  {r[0]:15} | {r[1][:30]:30} | {r[2] or '-':10} | {eba_label}")

conn.close()
