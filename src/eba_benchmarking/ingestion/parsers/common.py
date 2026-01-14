import re
import pandas as pd

# Template definitions with verified EBA mappings
TEMPLATE_ROWS = {
    'KM1': {
        '1': ('Common Equity Tier 1', '2520102'),
        '2': ('Tier 1 capital', '2520133'),
        '3': ('Total capital', '2520101'),
        '4': ('Total risk exposure amount', '2520138'),
        '4a': ('Total risk exposure pre-floor', '2520154'),
        '5': ('Common Equity Tier 1 ratio', '2520146'),
        '5b': ('Common Equity Tier 1 ratio', '2520146'),
        '6': ('Tier 1 ratio', '2520147'),
        '6b': ('Tier 1 ratio', '2520147'),
        '7': ('Total capital ratio', '2520148'),
        '7b': ('Total capital ratio', '2520148'),
        '8': ('Capital conservation buffer', None),
        '9': ('Countercyclical capital buffer', None),
        '11': ('Combined buffer requirement', None),
        '13': ('Leverage ratio total exposure measure', '2520903'),
        '14': ('Leverage ratio', '2520905'),
        '15': ('Total HQLA', None),
        '17': ('Liquidity coverage ratio (%)', '2521101'),
        '18': ('Total available stable funding', '2521102'),
        '19': ('Total required stable funding', '2521103'),
        '20': ('NSFR ratio (%)', '2521104'),
    },
    'KM2': {
        '1': ('Own funds and eligible liabilities', None),
        'EU-1a': ('Own Funds', '2520101'),
        '2': ('Total RWA', '2520138'),
        '3': ('MREL ratio (% of RWA)', None),
        '4': ('Total exposure measure', '2520903'),
        '5': ('MREL ratio (% of TEM)', None),
        '6': ('Combined buffer requirement (%)', None),
        '7': ('Subordinate liabilities', None),
        '8': ('Percentage of subordinate liabilities', None),
    },
    'CC1': {
        '1': ('Capital instruments and the related share premium accounts', '2520103'),
        '2': ('Retained earnings', '2520104'),
        '3': ('Accumulated other comprehensive income', '2520105'),
        '4': ('Other reserves', '2520106'),
        'EU-3a': ('Funds for general banking risk', '2520107'),
        '5': ('Minority interests', '2520108'),
        '5a': ('Independently reviewed interim profits net of foreseeable charges or dividends', None),
        '6': ('Common Equity Tier 1 (CET1) capital before regulatory adjustments', None),
        '7': ('Additional value adjustments', '2520109'),
        '8': ('Intangible assets', '2520110'),
        '10': ('Deferred tax assets that rely on future profitability', '2520111'),
        '29': ('Common Equity Tier 1', '2520102'),
        '30': ('Additional Tier 1', '2520129'),
        '36': ('Additional Tier 1 (AT1) capital before regulatory adjustments', '2520128'),
        '44': ('Tier 1 capital', '2520133'),
        '45': ('Tier 2 instruments', '2520135'),
        '58': ('Total capital', '2520101'),
        '59': ('Total risk exposure amount', '2520138'),
        '60': ('Common Equity Tier 1 ratio', '2520140'),
        '61': ('Tier 1 ratio', '2520141'),
        '62': ('Total capital ratio', '2520142'),
    },
    'OV1': {
        '1': ('Credit Risk excl CCR', '2520201'),
        '2': ('Of which SA', '2520202'),
        '3': ('Of which FIRB', '2520203'),
        '4': ('Of which Slotting', '2520204'),
        '5': ('Of which Equities IRB', '2520205'),
        '6': ('Counterparty Credit Risk', '2520206'),
        '10': ('CVA Risk', '2520207'),
        '15': ('Settlement Risk', '2520208'),
        '16': ('Securitisation Banking Book', '2520209'),
        '20': ('Position FX Commodities Risk', '2520210'),
        '21': ('Market Risk SA', '2520211'),
        '22': ('Market Risk IMA', '2520212'),
        '23': ('Operational Risk', '2520215'),
        '24': ('Operational Risk', '2520215'),
        '25': ('Operational Risk SA', '2520217'),
        '29': ('Total RWA', '2520220'),
    },
    'LR2': {
        '13': ('Total On-Balance Sheet Exposures', None),
        '20': ('Leverage Ratio', '2520905'),
        '21': ('Leverage Ratio excl CB Deposits', None),
        '23': ('Tier 1 capital', '2520133'),
        '24': ('Total exposure measure', '2520903'),
    },
    'LIQ1': {
        '1': ('Total HQLA', None),
        '21': ('LCR HQLA', '2520401'),
        '22': ('Total Net Cash Outflows', '2520402'),
        '23': ('LCR Ratio', '2520403'),
    },
    'IRRBB1': {
        '1': ('Parallel up', None),
        '2': ('Parallel down', None),
        '3': ('Steepener', None),
        '4': ('Flattener', None),
        '5': ('Short rates up', None),
        '6': ('Short rates down', None),
        '1a': ('Changes of EVE - Parallel up', '2525001'),
        '2a': ('Changes of EVE - Parallel down', '2525002'),
        '3a': ('Changes of EVE - Steepener', '2525003'),
        '4a': ('Changes of EVE - Flattener', '2525004'),
        '5a': ('Changes of EVE - Short rates up', '2525005'),
        '6a': ('Changes of EVE - Short rates down', '2525006'),
        'EU 1': ('Parallel up NII', '2525011'),
        'EU 2': ('Parallel down NII', '2525012'),
        '7': ('Tier 1 capital', '2520133'),
    },
}

def clean_number(value):
    """Convert string number to float. Robustly handles US and European formats."""
    if value is None or pd.isna(value):
        return None
        
    if isinstance(value, (int, float)):
        return float(value)
    
    value = str(value).strip()
    is_pct = '%' in value
    
    # Remove percentage sign and non-break spaces
    value = value.replace('%', '').replace('\xa0', ' ').strip()
    
    # Handle negative signs
    is_negative = False
    if value.startswith('(') and value.endswith(')'):
        is_negative = True
        value = value[1:-1].strip()
    elif value.startswith('-') or value.startswith('–') or value.startswith('—'):
        is_negative = True
        value = value[1:].strip()

    # Detect format pattern
    if ',' in value and '.' in value:
        if value.rfind(',') > value.rfind('.'):
            # European: 1.234,56 -> omit dots, comma to dot
            value = value.replace('.', '').replace(',', '.')
        else:
            # US: 1,234.56 -> omit commas
            value = value.replace(',', '')
    elif ',' in value:
        if value.count(',') > 1:
             value = value.replace(',', '')
        else:
            parts = value.split(',')
            if len(parts) == 2 and len(parts[1]) == 3:
                value = value.replace(',', '')
            else:
                value = value.replace(',', '.')
    elif '.' in value:
        parts = value.split('.')
        if len(parts) > 2:
            value = value.replace('.', '')
        elif len(parts) == 2 and len(parts[1]) == 3:
            value = value.replace('.', '')

    try:
        result = float(value)
        if is_negative:
            result = -result
        if is_pct:
            result = result / 100
        return result
    except:
        return None

def parse_text_rows(text, template_code, multiplier=1.0):
    """
    Fallback parser that scans raw text for known template rows.
    """
    results = []
    if template_code not in TEMPLATE_ROWS:
        return results
        
    row_defs = TEMPLATE_ROWS[template_code]
    
    # Scan text for each row
    for row_id, (def_label, eba_id) in row_defs.items():
        clean_lbl = re.escape(def_label.replace('(', '').replace(')', '').replace('-', ' ').strip())
        if len(clean_lbl) > 20: 
            clean_lbl = clean_lbl[:20]
            
        id_part = re.escape(row_id).replace('-', r'\s*-?\s*')
        number_pattern = r'((?:-|\()?\d[\d,.]+%?\)?)(?:\s+|$)'
        
        variants = [
            r'(?:^|\n)\s*' + id_part + r'\s+.*?' + clean_lbl + r'.*?' + number_pattern,
            r'(?:^|\n)\s*.*?' + clean_lbl + r'.*?' + number_pattern
        ]
        
        for pattern in variants:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                val_str = match.group(1)
                val = clean_number(val_str)
                if val is not None:
                    # Apply multiplier logic roughly (same as in batch parser)
                    results.append({
                        'row_id': row_id,
                        'row_label': def_label,
                        'raw_label': match.group(0)[:100],
                        'value': val * multiplier if abs(val) > 2.0 else val,
                        'eba_item_id': eba_id,
                        'is_new': eba_id is None,
                        'dimension_name': 'EVE' if template_code == 'IRRBB1' else 'Default'
                    })
                    break
    return results
