# EBA Bank Benchmarking Dashboard

A comprehensive Streamlit-based dashboard for benchmarking European banks using EBA Transparency Exercise data. This application provides detailed analysis of European banking metrics including solvency, asset quality, profitability, liquidity, and sovereign exposure.

## Features

### Core Banking Analysis
- **Solvency Analysis**: CET1, Total Capital, Leverage ratios with peer comparison
- **Asset Quality**: NPL ratios, Stage 2/3 coverage, Forborne exposures, Write-off rates
- **RWA Analysis**: Risk-weighted assets composition, RWA density, Texas Ratio
- **Profitability**: RoE, RoA, RoRWA, Cost-to-Income, Jaws Ratio, NIM analysis
- **Liquidity**: Loan-to-Deposit Ratio, Funding Gap analysis
- **Sovereign Exposure**: Country concentration analysis, Home Bias metrics

### Advanced Analytics
- **Country Benchmarking**: EBA Risk Dashboard KRI comparisons against EU averages
- **Market Data**: Real-time stock prices, valuation metrics (P/B, P/E), analyst targets
- **Implied Yields & Funding Costs**: Interest rate analysis with Euribor spreads
- **Deposit Beta Analysis**: Sensitivity of deposit costs to ECB rate changes

### Benchmarking Capabilities
- **Dynamic Peer Groups**: Domestic, Regional (same size), EU (same size), EU Large
- **Weighted Averages**: All peer group calculations use asset-weighted methodology
- **Period-over-Period Analysis**: Historical trends with quarterly granularity
- **Executive Insights**: Automated comparative analysis with rule-based insights

## Quick Start

### Prerequisites
```
Python 3.8+
streamlit>=1.30.0
pandas>=2.0.0
plotly>=5.18.0
yfinance>=0.2.0
```

### Installation

1. **Clone and install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Initialize database**:
   - Ensure `eba_data.db` exists in the `data/` directory
   - Database must contain EBA transparency exercise data

3. **Run the application**:
```bash
streamlit run src/app.py
```

4. **Access the dashboard**:
   - Open `http://localhost:8501` in your browser

### Quick Start Guide

#### Step 1: Verify Database
```bash
# Check database exists and has data
sqlite3 data/eba_data.db "SELECT COUNT(*) FROM institutions;"

# Expected output: Number of banks (e.g., 100+)
```

#### Step 2: Run Pipeline (First Time Setup)
```bash
cd src
python eba_benchmarking/ingestion/pipeline.py
```

This will:
- Initialize database tables
- Parse EBA transparency data
- Fetch market rates
- Classify banks by size

#### Step 3: Launch Dashboard
```bash
streamlit run src/app.py
```

#### Step 4: Explore Tabs
| Tab | Description |
|-----|-------------|
| **Solvency** | CET1, Total Capital, Leverage ratios |
| **Asset Quality** | NPL, Stage 2, Coverage ratios |
| **RWA** | Risk-weighted assets breakdown |
| **Profitability** | RoE, RoA, Cost-to-Income |
| **Liquidity** | Loan-to-Deposit, Funding |
| **Sovereign** | Country exposure analysis |
| **Yields** | Interest rate analysis |
| **Market** | Stock prices, P/B, P/E |

### Example Commands

#### Running the Dashboard
```bash
# Standard launch
streamlit run src/app.py

# With custom port
streamlit run src/app.py --server.port 8080

# With browser auto-launch disabled
streamlit run src/app.py --server.headless true
```

#### Running the Data Pipeline
```bash
# Full pipeline (all steps)
cd src
python eba_benchmarking/ingestion/pipeline.py

# Specific pipeline steps
python -c "from eba_benchmarking.ingestion.db_init import main; main()"  # Initialize DB
python -c "from eba_benchmarking.ingestion.parsers.tr_oth import OtherParser; OtherParser().run()"  # Parse Other data
python -c "from eba_benchmarking.ingestion.parsers.tr_cre import CreditRiskParser; CreditRiskParser().run()"  # Parse Credit data
python -c "from eba_benchmarking.ingestion.processors.classify_size import main; main()"  # Classify bank sizes
```

#### Utility Scripts
```bash
# Fetch missing ticker symbols from Yahoo Finance
python scripts/fetch_missing_tickers.py

# Verify size classification merge
python scripts/verify_size.py

# Merge size data from bank_models to institutions
python scripts/merge_size.py

# Verify metrics and data integrity
python scripts/verify_metrics.py
```

#### Database Queries
```bash
# Check database state
sqlite3 data/eba_data.db "SELECT COUNT(*) FROM institutions;"
sqlite3 data/eba_data.db "SELECT COUNT(*) FROM facts_oth;"
sqlite3 data/eba_data.db "SELECT size_category, COUNT(*) FROM institutions GROUP BY size_category;"
```

## Project Structure

```
eba-benchmarking/
├── src/
│   ├── app.py                              # Main Streamlit application
│   └── eba_benchmarking/
│       ├── config.py                       # Configuration (item IDs, thresholds)
│       ├── analysis/
│       │   └── insights.py                 # Rule-based insight generation
│       ├── data/
│       │   ├── base.py                     # Core data fetching and peer groups
│       │   ├── solvency.py                 # Solvency metrics and RWA
│       │   ├── asset_quality.py            # NPL, Coverage, Forborne metrics
│       │   ├── profitability.py            # P&L and return metrics
│       │   ├── liquidity.py                # LDR and funding metrics
│       │   ├── assets.py                   # Balance sheet assets
│       │   ├── liabilities.py              # Balance sheet liabilities
│       │   ├── sovereign.py                # Sovereign exposure
│       │   ├── market.py                   # Yahoo Finance integration
│       │   ├── benchmarking.py             # Benchmarking calculations
│       │   └── generic.py                  # Generic data fetching
│       ├── plotting/
│       │   ├── basic.py                    # Benchmark bar charts
│       │   ├── solvency.py                 # Capital ratio charts
│       │   ├── structure.py                # Composition charts
│       │   └── ...
│       └── ui/
│           └── tabs/                       # Individual dashboard tabs
├── data/
│   ├── eba_data.db                        # SQLite database
│   └── raw/                               # Raw data files
├── docs/
│   ├── CALCULATIONS.md                    # Detailed calculation documentation
│   ├── DATABASE_SCHEMA.md                 # Database schema reference
│   ├── DIMENSIONS.md                      # Dimension table values
│   ├── DICTIONARY.md                      # EBA item ID reference
│   └── DICTIONARY_PILLAR3.md              # Pillar 3 metrics reference
├── README.md                              # This file
└── requirements.txt                       # Python dependencies
```

## Database Schema

### Main Tables

| Table | Description | Source |
|-------|-------------|--------|
| `institutions` | Bank metadata (LEI, name, country, systemic importance) | EBA |
| `bank_models` | Business model classification and size category | Derived |
| `facts_oth` | Financial data (capital, P&L, assets, liabilities) | EBA |
| `facts_cre` | Credit risk data (exposures, provisions, NPL) | EBA |
| `facts_mrk` | Market risk data | EBA |
| `facts_sov` | Sovereign exposure data | EBA |
| `facts_pillar3` | Pillar 3 extracted data | Bank Reports |
| `dictionary` | Item metadata and labels | EBA |
| `eba_kris` | EBA Risk Dashboard country-level KRIs | EBA |

### Dimension Tables

| Table | Description | Key Values |
|-------|-------------|------------|
| `dim_country` | Country codes and labels | 900+ countries |
| `dim_maturity` | Maturity buckets | 0-3M to 15Y+ |
| `dim_portfolio` | Portfolio type (SA, IRB) | Trading, Banking Book |
| `dim_perf_status` | Performance status | Stage 1, 2, 3, NPL |
| `dim_exposure` | Counterparty type | Central banks, Households, NFC |

## Key Metrics Reference

### Solvency Metrics
- **CET1 Ratio**: CET1 Capital / TREA
- **Total Capital Ratio**: (CET1 + AT1 + T2) / TREA
- **Leverage Ratio**: Tier 1 Capital / Total Exposure
- **RWA Density**: TREA / Total Assets
- **Texas Ratio**: NPLs / (CET1 + Provisions)

### Asset Quality Metrics
- **NPL Ratio**: Stage 3 Exposure / Total Loans
- **Stage 2 Ratio**: Stage 2 Exposure / Performing Loans
- **Stage 3 Coverage**: Provisions / Stage 3 Gross Exposure
- **Forborne Ratio**: Forborne Exposures / Total Loans

### Profitability Metrics
- **RoE (Annualized)**: Net Profit / Average Equity × Annualization Factor
- **RoA (Annualized)**: Net Profit / Average Assets × Annualization Factor
- **Cost-to-Income**: Operating Expenses / Operating Income
- **NIM (Annualized)**: Net Interest Income / Total Assets × Annualization Factor

### Liquidity Metrics
- **LDR**: Loans / Customer Deposits
- **Funding Gap**: Loans - Customer Deposits
- **Deposit Coverage**: Customer Deposits / Loans

### Implied Rates (Yields & Costs)
- **Implied Loan Yield**: Interest Income (Loans) / Loans × Annualization
- **Implied Deposit Cost**: Interest Expenses (Deposits) / Deposits × Annualization
- **Margin**: Implied Rate - Euribor 3M

## Configuration

Key settings in `src/eba_benchmarking/config.py`:

```python
# Database path
DB_NAME = "data/eba_data.db"

# Outlier thresholds
OUTLIER_THRESHOLDS = {
    'CET1_MAX': 0.25,       # 25% - exclude if higher
    'TC_MAX': 0.35,         # 35% - exclude if higher
    'NPL_MAX': 0.50,        # 50% - exclude if higher
    'ROE_MIN': -0.50,       # -50% - exclude if lower
    'ROE_MAX': 0.50,        # 50% - exclude if higher
    'CTI_MAX': 1.50,        # 150% - Cost to Income outlier
    'RWA_DENSITY_MAX': 1.0, # 100% - RWA > Assets is impossible
}

# Item ID mappings
SOLVENCY_ITEMS = {
    '2520102': 'CET1 Capital',
    '2520140': 'CET1 Ratio',
    '2520142': 'Total Capital Ratio',
    '2520905': 'Leverage Ratio',
}

# Peer group colors
CHART_COLORS = {
    'base_bank': '#FF4B4B',
    'peer': '#E0E0E0',
    'average': '#333333',
    'domestic_avg': '#FF8C00',
    'eu_avg': '#2F4F4F',
}

# Display settings
DISPLAY_SETTINGS = {
    'chart_height': 450,
    'chart_height_small': 300,
    'decimal_places_percent': 1,
    'decimal_places_ratio': 2,
    'amount_unit': 1e6,  # Display in millions
    'amount_suffix': 'M',
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EBA_DATA_PATH` | Path to database | `data/eba_data.db` |
| `STREAMLIT_SERVER_PORT` | Port for dashboard | `8501` |

## Utility Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/fetch_missing_tickers.py` | Discover stock tickers from Yahoo Finance | `python scripts/fetch_missing_tickers.py` |
| `scripts/verify_size.py` | Verify size classification merge results | `python scripts/verify_size.py` |
| `scripts/merge_size.py` | Merge size data from bank_models to institutions | `python scripts/merge_size.py` |
| `scripts/verify_metrics.py` | Check bank_models and institutions tables | `python scripts/verify_metrics.py` |

## Data Sources

| Source | Description | Update Frequency |
|--------|-------------|------------------|
| EBA Transparency Exercise | Semi-annual bank-level data | Semi-annual |
| EBA Risk Dashboard | Aggregated country/EU averages | Quarterly |
| Pillar 3 Reports | Bank-specific disclosures | As available |
| Yahoo Finance | Market data (prices, caps) | Daily |
| ECB | Base rates (Euribor) | Daily |

## Data Ingestion & Pipeline

This section documents the data ingestion architecture using the main pipeline and Pillar 3 parser.

### Architecture Overview

```
src/eba_benchmarking/ingestion/
├── pipeline.py              # Main orchestration script
├── db_init.py              # Database initialization
├── parsers/
│   ├── base.py             # Base parser class
│   ├── unified.py          # Pillar 3 unified parser (PDF & Excel)
│   ├── pdf_enhanced.py     # Enhanced PDF parsing
│   ├── excel.py            # Excel template parsing
│   ├── tr_oth.py           # Transparency Other data parser
│   ├── tr_cre.py           # Transparency Credit Risk parser
│   ├── tr_rest.py          # Transparency Market/Sovereign parser
│   ├── kri.py              # KRI parser
│   └── common.py           # Template definitions
├── fetchers/
│   ├── market_data.py      # Yahoo Finance market data
│   ├── base_rates.py       # ECB base rates
│   ├── ecb_stats.py        # ECB statistics
│   ├── macro.py            # Macro-economic data
│   └── ...
└── processors/
    ├── classify_bm.py      # Business model classification
    ├── classify_size.py    # Bank size classification
    └── cleanup_db.py       # Database normalization
```

---

### 1. Main Data Pipeline (pipeline.py)

The main pipeline orchestrates the complete data ingestion workflow.

#### Running the Full Pipeline
```bash
cd src
python -m eba_benchmarking.ingestion.pipeline
# Or directly:
python eba_benchmarking/ingestion/pipeline.py
```

#### Pipeline Steps
The pipeline executes the following steps in order:

| Step | Module | Function | Description |
|------|--------|----------|-------------|
| 1 | `db_init` | `main()` | Initialize database, institutions, dimension tables |
| 2 | `gen_com_names` | `main()` | Generate commercial names |
| 3 | `tr_cre` | `main()` | Parse Credit Risk data (facts_cre) |
| 4 | `tr_oth` | `main()` | Parse Other data (facts_oth) - Capital, P&L, Assets |
| 5 | `tr_rest` | `main()` | Parse Market Risk & Sovereign (facts_mrk, facts_sov) |
| 6 | `classify_bm` | `main()` | Classify business models |
| 7 | `classify_size` | `main()` | Classify bank size (Large/Medium/Small) |
| 8 | `ecb_markets` | `main()` | Fetch ECB market rates |
| 9 | `base_rates` | `main()` | Fetch ECB base rates (Euribor) |
| 10 | `lending_spreads` | `main()` | Fetch lending spreads |
| 11 | `ecb_stats` | `main()` | Fetch ECB statistics (CET1, NPL) |
| 12 | `macro` | `main()` | Fetch macro data (World Bank, Eurostat) |
| 13 | `bog` | `main()` | Fetch Bank of Greece data |
| 14 | `kri_parser` | `main()` | Parse EBA Risk Dashboard KRIs |
| 15 | `map_kris` | `main()` | Map KRIs to dictionary items |
| 16 | `cleanup_bank_models` | `main()` | Clean bank_models table |
| 17 | `cleanup_db` | `main()` | Normalize database |
| 18 | `unified` | `run_pillar3_parser()` | Parse Pillar 3 PDFs/Excel |

#### Required Data Files
Place input files in `data/raw/` directory:

| File Pattern | Source | Parsed By |
|--------------|--------|-----------|
| `tr_cre_*.csv` | EBA Transparency Credit Risk | `tr_cre.py` |
| `tr_oth_*.csv` | EBA Transparency Other | `tr_oth.py` |
| `tr_mrk_*.csv` | EBA Transparency Market Risk | `tr_rest.py` |
| `tr_sov_*.csv` | EBA Transparency Sovereign | `tr_rest.py` |
| `kri_*.xlsx` | EBA Risk Dashboard | `kri.py` |
| `Pillar3reports/*.pdf` | Bank Pillar 3 Reports | `unified.py` |
| `Pillar3reports/*.xlsx` | Bank Pillar 3 Excel | `unified.py` |

---

### 2. Pillar 3 Report Parsing (unified.py)

The unified Pillar 3 parser handles both PDF and Excel reports.

#### Prerequisites
```bash
pip install pdfplumber openpyxl
```

#### Directory Structure
```
data/
├── raw/
│   └── Pillar3reports/
│       ├── 2024-09-30_Eurobank.pdf
│       ├── 2024-09-30_NBG.pdf
│       ├── 2024-09-30_Alpha_Bank.pdf
│       └── Piraeus_Pillar3_2024.xlsx
└── templates/
    └── *.xlsx              # Template definitions
```

#### Running Pillar 3 Parser Standalone
```bash
# Run as part of main pipeline (automatic)
python src/eba_benchmarking/ingestion/pipeline.py

# Run standalone
python -c "from eba_benchmarking.ingestion.parsers.unified import run_pillar3_parser; run_pillar3_parser()"
```

#### Supported Templates
| Template | Description | EBA Items |
|----------|-------------|-----------|
| KM1 | Key Metrics Overview | Capital ratios, Leverage, LCR, NSFR |
| KM2 | MREL Requirements | MREL ratios |
| CC1 | Own Funds Composition | CET1, AT1, T2 breakdown |
| CC2 | Own Funds Reconciliation | Balance sheet reconciliation |
| OV1 | RWA Overview | Credit, Market, Operational RWA |
| LR1/LR2/LR3 | Leverage Ratio | Tier 1, Exposure measure |
| LIQ1/LIQ2 | Liquidity (LCR/NSFR) | HQLA, Net cash outflows |
| IRRBB1 | Interest Rate Risk | Rate shock scenarios |
| CCR1 | Counterparty Credit Risk | CCR exposures |

#### Parser Features
- **Auto-detection**: Identifies bank name and period from PDF content
- **Fallback chain**: Standard parsing → Geometric parsing → Line parsing
- **Template matching**: Maps rows to EBA item IDs
- **Source tracking**: Records source file and page number
- **CSV export**: Auto-exports parsed data to CSV
- **Bank LEI Mapping**: Pre-configured for major European banks

#### Bank Configuration (in unified.py)
```python
BANK_CONFIG_EXCEL = {
    'Piraeus': {
        'filename_patterns': ['Pillar III_EN_', 'piraeus'],
        'lei': '213800OYHR4PPVA77574',
    },
    'Bank of Cyprus': {
        'filename_patterns': ['interim-pillar-3', 'cyprus', 'boc'],
        'lei': '635400L14KNHJ3DMBX37',
    },
    'NBG': {
        'filename_patterns': ['nbg', 'national'],
        'lei': '5UMCZOEYKCVFAW8ZLO05',
    },
}
```

---

### 3. Transparency Data Parsers

#### Credit Risk Parser (tr_cre.py)
```bash
# Part of main pipeline
python src/eba_benchmarking/ingestion/pipeline.py

# Standalone
python -c "from eba_benchmarking.ingestion.parsers.tr_cre import CreditRiskParser; CreditRiskParser().run()"
```

**Input**: `data/raw/tr_cre_*.csv`
**Output**: `facts_cre` table

#### Other Data Parser (tr_oth.py)
```bash
# Parses: Capital, P&L, Balance Sheet items
python -c "from eba_benchmarking.ingestion.parsers.tr_oth import OtherParser; OtherParser().run()"
```

**Input**: `data/raw/tr_oth_*.csv`
**Output**: `facts_oth` table

#### Market/Sovereign Parser (tr_rest.py)
```bash
# Parses: Market Risk, Sovereign Exposure
python -c "from eba_benchmarking.ingestion.parsers.tr_rest import RestParser; RestParser().run()"
```

**Input**: `data/raw/tr_mrk_*.csv`, `data/raw/tr_sov_*.csv`
**Output**: `facts_mrk`, `facts_sov` tables

---

### 4. Data Fetchers

#### Market Data (Yahoo Finance)
```bash
python src/eba_benchmarking/ingestion/fetchers/market_data.py
```

**Output**: `market_data`, `market_history` tables

#### ECB Base Rates
```bash
python src/eba_benchmarking/ingestion/fetchers/base_rates.py
```

**Output**: `base_rates` table (Euribor 3M, MRO, Deposit Facility)

#### ECB Statistics
```bash
python src/eba_benchmarking/ingestion/fetchers/ecb_stats.py
```

**Output**: `ecb_stats` table (Country-level CET1, NPL)

#### Macro-Economic Data
```bash
python src/eba_benchmarking/ingestion/fetchers/macro.py
```

**Output**: `macro_economics` table (GDP, inflation)

---

### 5. Processors

#### Business Model Classification
```bash
python src/eba_benchmarking/ingestion/processors/classify_bm.py
```

Classifies banks into: Universal Bank, Corporate Lender, Retail Bank, etc.

#### Size Classification
```bash
python src/eba_benchmarking/ingestion/processors/classify_size.py
```

Classifies by total assets:
- **Huge**: > 500bn EUR
- **Large**: 200-500bn EUR
- **Medium**: 50-200bn EUR
- **Small**: < 50bn EUR

---

### 6. Database Initialization

#### Initialize from Scratch
```bash
python -c "from eba_benchmarking.ingestion.db_init import main; main()"
```

Creates:
- Dimension tables (dim_country, dim_maturity, etc.)
- `institutions` table
- `dictionary` table

#### Quick Pipeline Start
```bash
cd src/eba_benchmarking/ingestion
python pipeline.py
```

---

### 7. Data Source URLs

| Source | URL | Format |
|--------|-----|--------|
| EBA Transparency | https://www.eba.europa.eu/risk-analysis-and-data/transparency-exercise | Excel/CSV |
| EBA Risk Dashboard | https://www.eba.europa.eu/risk-analysis-and-data/eba-risk-dashboard | Excel |
| Pillar 3 Reports | Bank websites (download PDFs) | PDF/Excel |
| ECB Statistics | https://data.ecb.europa.eu | API/CSV |
| World Bank | https://data.worldbank.org | API/CSV |

---

### 8. Troubleshooting

#### No data in facts_oth/facts_cre
1. Check raw files exist in `data/raw/`
2. Verify file naming: `tr_oth_2024.csv`, `tr_cre_2024.csv`
3. Run parser standalone: `python -c "from eba_benchmarking.ingestion.parsers.tr_oth import OtherParser; OtherParser().run()"`

#### Pillar 3 parsing fails
1. Ensure pdfplumber installed: `pip install pdfplumber`
2. Check PDF is text-based (not scanned image)
3. Run with debug: `python -c "from eba_benchmarking.ingestion.parsers.unified import run_pillar3_parser; run_pillar3_parser()"`

#### Missing dimension values
1. Reinitialize database: `python -c "from eba_benchmarking.ingestion.db_init import main; main()"`
2. Check DIMENSIONS.md for valid values

#### Institution counts mismatch
1. Verify EBA file contains all expected banks
2. Check `institutions` table: `SELECT COUNT(*) FROM institutions;`
3. Run classification: `python src/eba_benchmarking/ingestion/processors/classify_size.py`

## Common Tasks

### Adding a New Bank
1. Ensure bank exists in EBA transparency data
2. Verify LEI is in `institutions` table
3. Run pipeline to parse new data:
```bash
python -c "from eba_benchmarking.ingestion.parsers.tr_oth import OtherParser; OtherParser().run()"
python -c "from eba_benchmarking.ingestion.parsers.tr_cre import CreditRiskParser; CreditRiskParser().run()"
```

### Updating Market Data
```bash
python src/eba_benchmarking/ingestion/fetchers/market_data.py
```

### Re-running Classification
```bash
# Business model
python src/eba_benchmarking/ingestion/processors/classify_bm.py

# Size category
python src/eba_benchmarking/ingestion/processors/classify_size.py
```

### Checking Data Quality
```bash
# Verify metrics
python scripts/verify_metrics.py

# Check size distribution
python scripts/verify_size.py
```

### Exporting Data
```bash
# Export institutions to CSV
sqlite3 data/eba_data.db -header -csv "SELECT * FROM institutions LIMIT 10;" > banks.csv
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following code conventions
4. Submit a pull request

## License

[Specify your license here]
