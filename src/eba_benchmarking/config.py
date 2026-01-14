import os

# Get the root directory of the project
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Path to the database
DB_NAME = os.path.join(ROOT_DIR, 'data', 'eba_data.db')

# =============================================================================
# ITEM ID MAPPINGS
# =============================================================================

SOLVENCY_ITEMS = {
    '2520102': 'CET1 Capital',
    '2520129': 'AT1 Capital', 
    '2520135': 'Tier 2 Capital',
    '2520138': 'TREA',
    '2520140': 'CET1 Ratio',
    '2520142': 'Total Capital Ratio',
    '2520905': 'Leverage Ratio'
}

PROFITABILITY_ITEMS = {
    '2520301': 'Interest Income',
    '2520302': 'Int Inc: Debt Securities',
    '2520303': 'Int Inc: Loans',
    '2520304': 'Interest Expenses',
    '2520305': 'Int Exp: Deposits',
    '2520306': 'Int Exp: Debt Securities',
    '2520308': 'Dividend Income',
    '2520309': 'Net Fee & Commission Income',
    '2520311': 'Trading Income',
    '2520314': 'FX Income',
    '2520315': 'Other Operating Income',
    '2520316': 'Total Operating Income',
    '2520317': 'Admin Expenses',
    '2520318': 'Depreciation',
    '2520319': 'Provisions',
    '2520324': 'Impairment Cost',
    '2520332': 'Profit Before Tax',
    '2520335': 'Net Profit',
    '2521216': 'Total Equity',
    '2521010': 'Total Assets',
    '2520138': 'TREA'  # For RoRWA calculation
}

ASSET_QUALITY_ITEMS = {
    # Exposure items
    '2520603': 'Gross Loans',              # Gross carrying amount
    '2520605': 'Gross Loans (by exposure)', # With exposure dimension
    '2520613': 'Total Provisions',          # Accumulated impairment
    '2520615': 'Provisions (by exposure)',  # With exposure dimension
    # Forborne
    '2520703': 'Forborne Gross',
    '2520713': 'Forborne Provisions',
    # Write-offs
    '2521708': 'Accumulated Write-offs',
}

LIQUIDITY_ITEMS = {
    '2521017': 'Loans FV',
    '2521019': 'Loans AC',
    '2521215': 'Deposits Breakdown',  # With financial_instruments dimension
}

ASSET_ITEMS = {
    '2521010': 'Total Assets',
    '2521001': 'Cash',
    '2521017': 'Loans FV',
    '2521019': 'Loans AC',
    '2521016': 'Debt Sec FV',
    '2521018': 'Debt Sec AC',
    '2521002': 'Trading Assets',
    '2521003': 'Non-Trading FVTPL',
    '2521004': 'Designated FVTPL'
}

LIABILITY_ITEMS = {
    '2521214': 'Total Liabilities',
    '2521215': 'Liabilities Breakdown',  # With dimensions
    '2520102': 'Equity (CET1)',
}

# =============================================================================
# RWA CATEGORY MAPPING
# =============================================================================

RWA_CATEGORY_MAPPING = {
    # Main categories to include (not "Of which" items)
    'credit risk': 'Credit Risk',
    'operational risk': 'Operational Risk',
    'market risk': 'Market Risk',
    'counterparty': 'Counterparty Risk',
    'ccr': 'Counterparty Risk',
    'cva': 'Counterparty Risk',
    'settlement': 'Settlement Risk',
    'securitisation': 'Securitisation',
}

RWA_EXCLUDE_PATTERNS = ['of which', 'total']

RWA_CATEGORY_COLORS = {
    'Credit Risk': '#1f77b4',       # Blue
    'Operational Risk': '#ff7f0e',  # Orange
    'Market Risk': '#2ca02c',       # Green
    'Counterparty Risk': '#d62728', # Red
    'Settlement Risk': '#9467bd',   # Purple
    'Securitisation': '#e377c2',    # Pink
    'Other': '#7f7f7f'              # Gray
}

RWA_CATEGORY_ORDER = [
    'Credit Risk', 
    'Operational Risk', 
    'Market Risk', 
    'Counterparty Risk', 
    'Settlement Risk', 
    'Securitisation', 
    'Other'
]

# =============================================================================
# OUTLIER THRESHOLDS
# =============================================================================

OUTLIER_THRESHOLDS = {
    'CET1_MAX': 0.25,       # 25% - exclude if higher
    'TC_MAX': 0.35,         # 35% - exclude if higher
    'NPL_MAX': 0.50,        # 50% - exclude if higher
    'ROE_MIN': -0.50,       # -50% - exclude if lower
    'ROE_MAX': 0.50,        # 50% - exclude if higher
    'CTI_MAX': 1.50,        # 150% - Cost to Income outlier
    'RWA_DENSITY_MAX': 1.0, # 100% - RWA > Assets is impossible
}

# =============================================================================
# PEER GROUP DEFINITIONS
# =============================================================================

SYSTEMIC_IMPORTANCE_LEVELS = ['GSIB', 'OSII', 'Other']

SIZE_CATEGORIES = ['Large', 'Medium', 'Small']

# =============================================================================
# CHART COLORS
# =============================================================================

CHART_COLORS = {
    'base_bank': '#FF4B4B',     # Streamlit Red
    'peer': '#E0E0E0',          # Light Grey
    'average': '#333333',       # Fallback Dark Grey
    'domestic_avg': '#FF8C00',  # Dark Orange
    'eu_avg': '#2F4F4F',        # Dark Slate Grey
    'benchmark_line': '#00CC96', # Greenish for EU/EBA avg
    
    # Standard Categorical (Plotly Default adapted)
    'cat1': '#1f77b4',  # Blue
    'cat2': '#ff7f0e',  # Orange
    'cat3': '#2ca02c',  # Green
    'cat4': '#d62728',  # Red
    'cat5': '#9467bd',  # Purple
    'cat6': '#8c564b',  # Brown
    'cat7': '#e377c2',  # Pink
    'cat8': '#7f7f7f',  # Grey
    'cat9': '#bcbd22',  # Olive
    'cat10': '#17becf', # Cyan

    # Semantic Groups
    'capital': {
        'cet1': '#1f77b4', 
        'at1': '#ff7f0e', 
        't2': '#2ca02c'
    },
    'asset_quality': {
        'stage1': '#2ca02c', 
        'stage2': '#ff7f0e', 
        'arrears': '#9467bd', 
        'npl': '#d62728'
    },
    'income': ['#1f77b4', '#2ca02c', '#17becf', '#9467bd', '#8c564b'],
    'expense': ['#d62728', '#ff7f0e', '#7f7f7f', '#bcbd22', '#e377c2']
}

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================

DISPLAY_SETTINGS = {
    'chart_height': 450,
    'chart_height_small': 300,
    'decimal_places_percent': 1,
    'decimal_places_ratio': 2,
    'amount_unit': 1e6,  # Display in millions
    'amount_suffix': 'M',
}