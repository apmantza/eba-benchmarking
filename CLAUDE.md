# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EBA Bank Benchmarking Dashboard - A Streamlit application for analyzing and benchmarking European banks using EBA (European Banking Authority) Transparency Exercise data. Provides analysis across solvency, asset quality, profitability, liquidity, credit risk, market risk, and sovereign exposure.

**Tech Stack:** Python 3.8+, Streamlit, SQLite, Plotly, Pandas, yfinance

## Common Commands

```bash
# Launch dashboard
streamlit run src/app.py

# Run full data pipeline (initializes DB, parses data, fetches market data)
cd src && python eba_benchmarking/ingestion/pipeline.py

# Run individual pipeline steps
python -c "from eba_benchmarking.ingestion.db_init import main; main()"
python -c "from eba_benchmarking.ingestion.parsers.tr_oth import OtherParser; OtherParser().run()"
python -c "from eba_benchmarking.ingestion.parsers.tr_cre import CreditRiskParser; CreditRiskParser().run()"
python -c "from eba_benchmarking.ingestion.processors.classify_size import main; main()"

# Database checks
sqlite3 data/eba_data.db "SELECT COUNT(DISTINCT lei) FROM institutions;"
sqlite3 data/eba_data.db "SELECT MAX(period) FROM facts_oth;"
```

**Note:** No automated test suite exists. Testing is manual via database verification.

## Architecture

### Layer Organization
```
src/
├── app.py                          # Streamlit entry point
└── eba_benchmarking/
    ├── config.py                   # Item ID mappings, thresholds, colors
    ├── data/                       # Data fetching layer (SQL queries)
    │   ├── base.py                 # Core queries, peer group construction
    │   ├── solvency.py             # Capital metrics
    │   ├── profitability.py        # RoE, RoA, NIM, Cost-to-Income
    │   ├── asset_quality.py        # NPL, Stage 2/3, Coverage
    │   └── [domain].py             # Other metric domains
    ├── plotting/                   # Plotly visualization functions
    ├── ui/tabs/                    # Dashboard tab implementations
    └── ingestion/                  # Data pipeline
        ├── pipeline.py             # Orchestrator (18 steps)
        ├── parsers/                # EBA data parsers
        ├── fetchers/               # External data (Yahoo, ECB)
        └── processors/             # Classifications, normalization
```

### Database Schema (SQLite: `data/eba_data.db`)
- **Fact Tables:** `facts_oth` (financials), `facts_cre` (credit risk), `facts_mrk` (market risk), `facts_sov` (sovereign)
- **Metadata:** `institutions` (bank master), `bank_models` (size/business model), `dictionary` (item labels)
- **Dimensions:** `dim_country`, `dim_maturity`, `dim_portfolio`, `dim_perf_status`, `dim_exposure`
- All monetary values stored in millions EUR

### Key Patterns
- Data functions: `get_*_kpis(selected_leis)` returns latest period metrics
- Peer averages: `get_*_averages()` with base_country, base_region, base_sys, base_size params
- Caching: `@st.cache_data` on all data layer functions
- UI tabs: `render_*_tab(selected_leis, base_bank_name, ...)` signature

### Hardcoded Values (in `app.py` and `data/base.py`)
- Base bank: National Bank of Greece (LEI: `5UMCZOEYKCVFAW8ZLO05`)
- Bank of Cyprus LEI hardcoded for ATHEX peer group: `635400L14KNHJ3DMBX37`

## Key Configuration (config.py)

**Item ID Mappings** - EBA item codes to metric names:
- `SOLVENCY_ITEMS` - CET1, Total Capital, Leverage ratios
- `PROFITABILITY_ITEMS` - Interest income/expense, P&L, RoE
- `ASSET_QUALITY_ITEMS` - NPL, Stage 2/3, Forborne
- `LIQUIDITY_ITEMS` - Loans, Deposits, LDR

**Size Categories** (by total assets):
- Huge: >500bn, Large: 200-500bn, Medium: 50-200bn, Small: <50bn

**Peer Groups:**
- Domestic, Regional (same size), EU (same size), EU Large
- All use asset-weighted averages

## Data Flow

1. Raw EBA files in `data/raw/` (tr_oth_*.csv, tr_cre_*.csv, etc.)
2. Pipeline parses → fact tables
3. Fetchers pull external data (ECB rates, Yahoo Finance)
4. Processors classify banks (size, business model)
5. Dashboard queries via data layer functions

## Documentation Reference

- `docs/DATABASE_SCHEMA.md` - Complete table structures
- `docs/CALCULATIONS.md` - Metric formulas and adjustments
- `docs/DICTIONARY.md` - EBA item ID → label mappings
- `docs/DIMENSIONS.md` - All dimension table values
