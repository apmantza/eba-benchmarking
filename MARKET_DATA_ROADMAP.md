# Roadmap: Split Market Data Benchmarking

This document outlines the plan to extract the Market Data functionality from `eba-benchmarking` into a standalone repository focused purely on market data analytics (using Yahoo Finance).

## 1. Project Goal
Create a lightweight, standalone Streamlit application (`bank-market-benchmarks`) that:
- Tracks market valuations (P/B, P/E, Market Cap) for European banks.
- Analyzes shareholder returns (Dividends, Buybacks, Total Yield).
- Benchmarks individual banks against Domestic, Regional, and Core Peer groups.
- Does **not** require EBA regulatory data (Solvency, RWA, Liquidity).

## 2. Repository Structure
Proposed structure for the new repository:
```
bank-market-benchmarks/
├── data/
│   └── market_data.db       # SQLite DB (Market Data + Simplified Institutions)
├── src/
│   └── market_bench/
│       ├── __init__.py
│       ├── app.py           # Main Streamlit Entrypoint
│       ├── config.py        # Chart colors, DB path
│       ├── data.py          # Yahoo Finance fetcher + DB queries (from market.py)
│       ├── plotting.py      # Plotly functions (from plotting/market.py)
│       └── utils.py         # Helper functions
├── scripts/
│   ├── init_db.py           # Create DB schema
│   └── refresh_data.py      # Batch fetcher (daily job)
├── requirements.txt
└── README.md
```

## 3. Implementation Steps

### Phase 1: Data Extraction & Database Setup
1. **Define Schema**: The new app needs a simplified database with 3 tables:
   - `institutions`: `lei`, `name`, `ticker`, `country`, `region`, `size_category` (Subset of current EBA table).
   - `market_data`: Snapshot metrics (P/B, Yields, etc.).
   - `market_history`: Time-series data (Prices, Volume).
   - `market_financial_years`: Strategic FY data (Dividends, Net Income).

2. **Migration Script**: Create a script to export relevant rows from the existing `eba_data.db` to the new `market_data.db`. This ensures checking continuity.

### Phase 2: Code Migration
1. **Config**:
   - Create `config.py`.
   - Copy `CHART_COLORS` and `DISPLAY_SETTINGS`.
   - **Remove**: `SOLVENCY_ITEMS`, `ASSET_QUALITY_ITEMS`, `RWA_MAPPINGS` etc.

2. **Data Module** (`src/market_bench/data.py`):
   - Copy logic from `eba_benchmarking/data/market.py`.
   - **Refactor**: Remove dependency on the complex `institutions` EBA table joins. Update queries to use the simplified schema.
   - Ensure `fetch_yahoo_data` and metadata overrides (e.g., for NLB) are preserved.

3. **Plotting Module** (`src/market_bench/plotting.py`):
   - Copy `eba_benchmarking/plotting/market.py`.
   - Ensure it imports colors from the new `config.py`.

4. **UI Module** (`src/market_bench/app.py`):
   - Adapt `eba_benchmarking/ui/tabs/market_data.py` to be the *main page*.
   - Add a **Sidebar Selector**:
     - Select Base Bank (Dropdown).
     - Select Peer Group (Domestic, Regional, Custom).
   - This replaces the global `selected_leis` logic from the parent app.

### Phase 3: Automation
1. **Refresh Script**:
   - Adapt the `refresh_market_data()` function into `scripts/refresh_data.py`.
   - Ensure it can run via GitHub Actions or Cron (headless).

## 4. Key Differences (Decoupling)
- **No EBA Dependency**: The new app will not need to parse XBRL or CSVs from the EBA website.
- **Tickers Source**: The list of banks and tickers must be maintained in the new `institutions` table. Initially, this can be seeded from the current app, but effectively it becomes a standalone master list.

## 5. Timeline Estimate
1. **Setup & DB Migration**: 2 Hours
2. **Code Porting**: 3 Hours
3. **UI Refactoring for Standalone**: 2 Hours
4. **Testing & Validation**: 2 Hours

## 6. Immediate Actions
- [ ] Initialize new git repo.
- [ ] Create `init_db.py` to seed data from current `eba_data.db`.
- [ ] Port `market.py` to `data.py`.
