"""
Manual ticker mapping for European banks (Yahoo Finance format).
This file maps bank names to their Yahoo Finance ticker symbols.
Only includes publicly traded banks.
Uses more specific patterns to avoid false matches.
"""

# Format: partial_name_match: ticker
# The script will use case-insensitive matching on commercial_name

TICKER_MAPPINGS = {
    # Greece
    'National Bank of Greece': 'ETE.AT',
    'Alpha Bank': 'ALPHA.AT',
    'Eurobank': 'EUROB.AT',
    'Piraeus': 'TPEIR.AT',
    
    # Germany
    'Deutsche Bank': 'DBK.DE',
    'Commerzbank': 'CBK.DE',
    'Deutsche Pfandbriefbank': 'PBB.DE',
    'Aareal Bank': 'ARL.DE',
    
    # France
    'BNP Paribas': 'BNP.PA',
    'Société générale': 'GLE.PA',
    'Crédit Agricole': 'ACA.PA',
    
    # Spain
    'Banco Santander': 'SAN.MC',
    'Bilbao Vizcaya': 'BBVA.MC',  # BBVA
    'CaixaBank': 'CABK.MC',
    'Sabadell': 'SAB.MC',
    'Bankinter': 'BKT.MC',
    'Unicaja': 'UNI.MC',
    
    # Italy
    'Intesa Sanpaolo': 'ISP.MI',
    'UNICREDIT': 'UCG.MI',
    'Banco BPM': 'BAMI.MI',
    'BPER Banca': 'BPE.MI',
    'Monte Paschi': 'BMPS.MI',
    'Mediobanca': 'MB.MI',
    'FINECOBANK': 'FBK.MI',
    'CREDITO EMILIANO': 'CE.MI',
    'BANCA MEDIOLANUM': 'BMED.MI',
    
    # Netherlands
    'ING Groep': 'INGA.AS',  # More specific
    'ABN AMRO': 'ABN.AS',
    
    # Belgium
    'KBC': 'KBC.BR',
    
    # Austria
    'Erste Group': 'EBS.VI',
    'Raiffeisen Bank International': 'RBI.VI',
    'BAWAG': 'BG.VI',
    
    # Portugal
    'Banco Comercial Português': 'BCP.LS',
    
    # Ireland
    'AIB Group': 'A5G.IR',
    'Bank of Ireland': 'BIRG.IR',
    
    # Nordic
    'Nordea Bank': 'NDA-FI.HE',  # More specific
    'Danske Bank': 'DANSKE.CO',
    
    # Cyprus
    'Bank of Cyprus': 'BOCH.CY',
    
    # Slovenia
    'Nova Ljubljanska': 'NLBR.LJ',
}
