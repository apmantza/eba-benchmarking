# Database Schema Documentation

This document provides a comprehensive reference of all tables in the EBA Benchmarking database.

## Fact Tables (Core Data)

### Table: `facts_oth` (Other Financial Data)

Stores capital, P&L, balance sheet items, and RWA data from EBA Transparency Exercise.

| CID | Name | Type | NotNull | PK | Description |
|-----|------|------|---------|-----|-------------|
| 0 | id | INTEGER | 0 | 0 | Primary key |
| 1 | lei | TEXT | 0 | 0 | Legal Entity Identifier |
| 2 | period | TEXT | 0 | 0 | Reporting period (YYYY-MM-DD) |
| 3 | item_id | TEXT | 0 | 0 | EBA item identifier |
| 4 | nsa | TEXT | 0 | 0 | National specific approach code |
| 5 | assets_fv | INTEGER | 0 | 0 | Fair value hierarchy dimension |
| 6 | assets_stages | INTEGER | 0 | 0 | IFRS 9 stage dimension |
| 7 | exposure | INTEGER | 0 | 0 | Exposure type dimension |
| 8 | financial_instruments | INTEGER | 0 | 0 | Instrument type dimension |
| 9 | amount | REAL | 0 | 0 | Monetary amount in millions EUR |

**Key Item IDs**: Capital (25201xx), P&L (25203xx), Assets (25210xx), Liabilities (25212xx), RWA (25202xx)

---

### Table: `facts_cre` (Credit Risk Data)

Stores credit risk exposures, provisions, and collateral data.

| CID | Name | Type | NotNull | PK | Description |
|-----|------|------|---------|-----|-------------|
| 0 | id | INTEGER | 0 | 0 | Primary key |
| 1 | lei | TEXT | 0 | 0 | Legal Entity Identifier |
| 2 | period | TEXT | 0 | 0 | Reporting period |
| 3 | item_id | TEXT | 0 | 0 | EBA item identifier |
| 4 | portfolio | INTEGER | 0 | 0 | SA/IRB portfolio dimension |
| 5 | country | TEXT | 0 | 0 | Counterparty country dimension |
| 6 | exposure | INTEGER | 0 | 0 | Exposure type dimension |
| 7 | status | INTEGER | 0 | 0 | Default status dimension |
| 8 | perf_status | INTEGER | 0 | 0 | Performance status (Stage 1/2/3) |
| 9 | nace_codes | INTEGER | 0 | 0 | NACE industry code dimension |
| 10 | amount | REAL | 0 | 0 | Amount in millions EUR |

**Key Item IDs**: NPE (25206xx), Forborne (25207xx), Collateral (25217xx), Credit Risk RWA (25205xx)

---

### Table: `facts_mrk` (Market Risk Data)

Stores market risk capital charges and VaR metrics.

| CID | Name | Type | NotNull | PK | Description |
|-----|------|------|---------|-----|-------------|
| 0 | id | INTEGER | 0 | 0 | Primary key |
| 1 | lei | TEXT | 0 | 0 | Legal Entity Identifier |
| 2 | period | TEXT | 0 | 0 | Reporting period |
| 3 | item_id | TEXT | 0 | 0 | EBA item identifier |
| 4 | portfolio | INTEGER | 0 | 0 | Portfolio type |
| 5 | mkt_modprod | INTEGER | 0 | 0 | Product type dimension |
| 6 | mkt_risk | INTEGER | 0 | 0 | Risk type dimension |
| 7 | amount | REAL | 0 | 0 | Risk exposure amount |

**Key Item IDs**: 25204xx (Market Risk RWA, VaR, SVaR)

---

### Table: `facts_sov` (Sovereign Exposure Data)

Stores sovereign debt holdings by country, portfolio, and maturity.

| CID | Name | Type | NotNull | PK | Description |
|-----|------|------|---------|-----|-------------|
| 0 | id | INTEGER | 0 | 0 | Primary key |
| 1 | lei | TEXT | 0 | 0 | Legal Entity Identifier |
| 2 | period | TEXT | 0 | 0 | Reporting period |
| 3 | item_id | TEXT | 0 | 0 | EBA item identifier |
| 4 | country | TEXT | 0 | 0 | Issuer country (dim_country) |
| 5 | maturity | INTEGER | 0 | 0 | Maturity bucket (dim_maturity) |
| 6 | accounting_portfolio | INTEGER | 0 | 0 | Portfolio classification |
| 7 | amount | REAL | 0 | 0 | Amount in millions EUR |

**Key Item IDs**: 25208xx (Sovereign exposures by portfolio)

---

### Table: `facts_pillar3` (Pillar 3 Extracted Data)

Stores metrics extracted directly from bank Pillar 3 reports.

| CID | Name | Type | NotNull | PK | Description |
|-----|------|------|---------|-----|-------------|
| 0 | lei | TEXT | 0 | 1 | Legal Entity Identifier |
| 1 | period | TEXT | 0 | 2 | Reporting period |
| 2 | template_code | TEXT | 0 | 3 | Pillar 3 template code |
| 3 | table_title | TEXT | 0 | 0 | Original table title |
| 4 | row_id | TEXT | 0 | 4 | Row identifier |
| 5 | row_label | TEXT | 0 | 0 | Human-readable row label |
| 6 | raw_label | TEXT | 0 | 0 | Original raw label from PDF |
| 7 | amount | REAL | 0 | 0 | Extracted value |
| 8 | eba_item_id | TEXT | 0 | 0 | Mapped EBA item ID |
| 9 | is_new_metric | INTEGER | 0 | 0 | 1 if new metric, 0 if mapped |
| 10 | source_page | INTEGER | 0 | 0 | Page number in source PDF |
| 11 | bank_name | TEXT | 0 | 0 | Bank commercial name |

---

## Dimension Tables

### Table: `dim_country`

Country codes and labels for counterparties and sovereign issuers.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | country | INTEGER | Country dimension ID |
| 1 | label | TEXT | Full country name |
| 2 | iso_code | TEXT | 2-letter ISO code |

---

### Table: `dim_maturity`

Maturity buckets for sovereign and other long-term exposures.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | maturity | INTEGER | Maturity bucket ID |
| 1 | label | TEXT | Human-readable range |

**Standard Buckets**:
- 1: [0-3 months[
- 2: [3 months-1 year[
- 3: [1-2 years[
- 4: [2-5 years[
- 5: [5-10 years[
- 6: [10-20 years[
- 7: [>20 years[
- 8: [No breakdown]

---

### Table: `dim_portfolio`

Portfolio classification for credit risk exposures.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | portfolio | INTEGER | Portfolio ID |
| 1 | label | TEXT | Portfolio description |

**Values**:
- 0: Total / No breakdown
- 1: SA (Standardized Approach)
- 2: IRB (Internal Ratings-Based)
- 3: F-IRB
- 4: A-IRB
- 5: IM (Internal Model)

---

### Table: `dim_perf_status`

Performance status indicating IFRS 9 staging.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | perf_status | INTEGER | Status ID |
| 1 | label | TEXT | Status description |

**Values**:
- 0: No breakdown
- 1: Performing (Stage 1)
- 11: Performing with forbearance
- 12: Stage 2 (SICR)
- 2: Non-performing (Stage 3)
- 21: Non-performing with forbearance
- 23: Stage 3

---

### Table: `dim_exposure`

Counterparty type classification.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | exposure | INTEGER | Exposure type ID |
| 1 | label | TEXT | Counterparty description |

**Key Values**:
- 0: Total / No breakdown
- 101: Central banks
- 102: General governments
- 301: Non-financial corporations (NFC)
- 401: Households

---

### Table: `dim_financial_instruments`

Instrument type classification for liability breakdown.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | financial_instruments | INTEGER | Instrument ID |
| 1 | label | TEXT | Instrument description |

**Key Values**:
- 0: No breakdown
- 12: Derivatives
- 30: Deposits
- 40: Debt securities issued

---

### Table: `dim_assets_stages`

IFRS 9 staging classification.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | assets_stages | INTEGER | Stage ID |
| 1 | label | TEXT | Stage description |

---

### Table: `dim_assets_fv`

Fair value hierarchy classification.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | assets_fv | INTEGER | FV hierarchy level |
| 1 | label | TEXT | Level description |

---

## Reference Tables

### Table: `institutions`

Bank master data with identification and classification.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | lei | TEXT | Legal Entity Identifier (PK) |
| 1 | name | TEXT | Full legal name |
| 2 | country_iso | TEXT | 2-letter country code |
| 3 | country_name | TEXT | Full country name |
| 4 | commercial_name | TEXT | Trading name |
| 5 | short_name | TEXT | Abbreviated name |
| 6 | ticker | TEXT | Yahoo Finance stock ticker |
| 7 | bond_ticker | TEXT | Bond ticker symbol |
| 8 | region | TEXT | Geographic region |
| 9 | Systemic_Importance | TEXT | GSIB/OSII/Other |
| 10 | trading_status | TEXT | Public/Private trading status |
| 11 | bank_type | TEXT | Bank type (Cooperative, State-owned, Landesbank, etc.) |
| 12 | majority_owner | TEXT | Majority owner (if applicable) |

---

### Table: `bank_models`

Bank classification based on business model and size.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | lei | TEXT | Legal Entity Identifier (PK) |
| 1 | business_model | TEXT | Business model classification |
| 2 | total_assets | REAL | Total assets in EUR millions |
| 3 | size_category | TEXT | Size classification |

**Size Categories**:
- Small (< 50bn EUR)
- Medium (50-200bn EUR)
- Large (200-500bn EUR)
- Huge (> 500bn EUR)

---

### Table: `dictionary`

EBA item ID to label mapping.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | item_id | TEXT | EBA item identifier (PK) |
| 1 | label | TEXT | Item description |
| 2 | template | TEXT | EBA template name |
| 3 | category | TEXT | Metric category |
| 4 | tab_name | TEXT | Dashboard tab name |

---

### Table: `eba_kris`

EBA Risk Dashboard Key Risk Indicators at country level.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | period | TEXT | Reporting date |
| 1 | country | TEXT | Country code |
| 2 | kri_code | TEXT | KRI identifier |
| 3 | kri_name | TEXT | KRI description |
| 4 | value | REAL | KRI value |

---

## Configuration Tables

### Table: `item_mappings`

Maps item IDs across different exercise years.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | exercise_year | TEXT | Source year |
| 1 | original_item_id | TEXT | Original item ID |
| 2 | canonical_item_id | TEXT | Canonical (current) item ID |

---

### Table: `kri_to_item`

Maps EBA KRI names to item IDs for bank-level comparison.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | kri_name | TEXT | KRI name (PK) |
| 1 | item_id | TEXT | Corresponding item ID |

---

### Table: `pillar3_dictionary`

Pillar 3 item definitions with EBA mappings.

| CID | Name | Type | Description |
|-----|------|------|-------------|
| 0 | p3_item_id | TEXT | Pillar 3 item ID (PK) |
| 1 | template_code | TEXT | Template code |
| 2 | row_id | TEXT | Row identifier |
| 3 | p3_label | TEXT | Pillar 3 label |
| 4 | eba_item_id | TEXT | Mapped EBA item ID |
| 5 | notes | TEXT | Additional notes |
| 6 | category | TEXT | Metric category |

---

## Market Data Tables

### Table: `market_data`

Real-time market data fetched from Yahoo Finance.

| Column | Type | Description |
|--------|------|-------------|
| lei | TEXT | Bank identifier (PK) |
| ticker | TEXT | Stock ticker |
| current_price | REAL | Latest price |
| market_cap | REAL | Market capitalization |
| pe_trailing | REAL | P/E ratio |
| price_to_book | REAL | P/B ratio |
| dividend_yield | REAL | Dividend yield |
| beta | REAL | Beta coefficient |
| recommendation | TEXT | Analyst recommendation |

---

### Table: `market_history`

Historical monthly market data.

| Column | Type | Description |
|--------|------|-------------|
| lei | TEXT | Bank identifier (PK) |
| date | TEXT | Month-end date (PK) |
| close | REAL | Closing price |
| dividend | REAL | Dividend paid |
| dividend_ttm | REAL | TTM dividend |
| dividend_yield | REAL | Trailing yield |
| market_cap | REAL | Market cap |

---

## External Data Tables

### Table: `base_rates`

Central bank base rates (ECB, Fed, etc.).

| Column | Type | Description |
|--------|------|-------------|
| date | TEXT | Rate date |
| metric | TEXT | Rate name |
| value | REAL | Rate value (%) |

---

### Table: `ecb_stats`

ECB banking statistics.

| Column | Type | Description |
|--------|------|-------------|
| period | TEXT | Reporting period |
| variable | TEXT | Metric name |
| group_type | TEXT | Country/Region |
| group_name | TEXT | Group identifier |
| value | REAL | Metric value |

---

### Table: `macro_economics`

Macroeconomic indicators.

| Column | Type | Description |
|--------|------|-------------|
| country | TEXT | Country code |
| period | TEXT | Period |
| indicator | TEXT | Indicator name |
| value | REAL | Indicator value |
| source | TEXT | Data source |

---

## Table: `base_rates`

ECB and other central bank policy rates.

| Column | Type | Description |
|--------|------|-------------|
| date | TEXT | Rate date |
| metric | TEXT | Rate name (e.g., 'Euribor 3M', 'Deposit Facility Rate') |
| value | REAL | Rate value (%) |

---
### Sample Data (Limit 3)
- ('0W2PZJM8XOY22M4GG883', 'Corporate Lender', 96079.97843525, 'Medium (50-200bn)')
- ('2138008AVF4W7FMW8W87', 'Corporate Lender', 19594.3948884513, 'Small (<50bn)')
- ('2138009Y59EAR7H1UO97', 'Corporate Lender', 5032.17057082, 'Small (<50bn)')

---
## Table: `base_rates`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | date | TEXT | 0 | None | 0 |
| 1 | metric | TEXT | 0 | None | 0 |
| 2 | value | REAL | 0 | None | 0 |

### Sample Data (Limit 3)
- ('2020-01-31', 'MRO Rate', 0.0)
- ('2020-02-29', 'MRO Rate', 0.0)
- ('2020-03-31', 'MRO Rate', 0.0)

---
## Table: `bog_macro`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | date | TEXT | 0 | None | 0 |
| 1 | category | TEXT | 0 | None | 0 |
| 2 | metric | TEXT | 0 | None | 0 |
| 3 | value | REAL | 0 | None | 0 |

### Sample Data (Limit 3)
- ('2020-01-31', 'Real Estate Indices', 'Prop. Prices: National (Apartments)', 109.35593497932274)
- ('2020-04-30', 'Real Estate Indices', 'Prop. Prices: National (Apartments)', 109.88003111820824)
- ('2020-07-31', 'Real Estate Indices', 'Prop. Prices: National (Apartments)', 110.94460140031936)

---
## Table: `dictionary`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | item_id | TEXT | 0 | None | 1 |
| 1 | label | TEXT | 0 | None | 0 |
| 2 | template | TEXT | 0 | None | 0 |
| 3 | category | TEXT | 0 | None | 0 |
| 4 | tab_name | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- ('2520101', 'OWN FUNDS', 'Capital', 'Capital', 'Solvency')
- ('2520102', 'COMMON EQUITY TIER 1 CAPITAL (net of deductions and after applying transitional adjustments)', 'Capital', 'Capital', 'Solvency')
- ('2520103', 'Capital instruments eligible as CET1 Capital (including share premium and net own capital instruments)', 'Capital', 'Capital', 'Solvency')

---
## Table: `dim_accounting_portfolio`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | accounting_portfolio | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'No breakdown by Accounting_portfolio')
- (1, 'Held for trading')
- (2, 'Designated at fair value through profit or loss')

---
## Table: `dim_assets_fv`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | assets_fv | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'No breakdown by ASSETS_FV')
- (1, 'Fair value hierarchy: Level 1')
- (2, 'Fair value hierarchy: Level 2')

---
## Table: `dim_assets_stages`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | assets_stages | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'No breakdown by ASSETS_Stages')
- (1, 'Stage 1: Assets without significant increase in credit risk since initial recognition')
- (2, 'Stage 2: Assets with significant increase in credit risk since initial recognition but not credit-impaired')

---
## Table: `dim_country`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | country | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |
| 2 | iso_code | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'Total / No breakdown ', '00')
- (1, 'Austria', 'AT')
- (2, 'Belgium', 'BE')

---
## Table: `dim_exposure`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | exposure | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'Total / No breakdown')
- (101, 'Central banks')
- (102, 'General governments')

---
## Table: `dim_financial_instruments`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | financial_instruments | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'Total / No breakdown')
- (12, 'Derivatives')
- (21, 'Short positions - Equity instruments')

---
## Table: `dim_maturity`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | maturity | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (1, '[ 0 - 3M [')
- (2, '[ 3M - 1Y [')
- (3, '[ 1Y - 2Y [')

---
## Table: `dim_mkt_modprod`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | mkt_modprod | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'No breakdown by MKT_Modprod')
- (1, 'Traded debt instruments')
- (2, 'Equities')

---
## Table: `dim_mkt_risk`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | mkt_risk | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'No breakdown by MKT_Risk')
- (1, 'General risk')
- (2, 'Specific risk')

---
## Table: `dim_nace_codes`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | nace_codes | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'No breakdown by NACE_codes')
- (1, 'A Agriculture, forestry and fishing')
- (2, 'B Mining and quarrying')

---
## Table: `dim_perf_status`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | perf_status | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'No breakdown by Perf_status')
- (1, 'Performing')
- (11, 'Performing - of which exposures with forbearance measures')

---
## Table: `dim_portfolio`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | portfolio | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'Total / No breakdown by portfolio')
- (1, 'SA')
- (2, 'IRB')

---
## Table: `dim_status`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | status | INTEGER | 0 | None | 0 |
| 1 | label | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- (0, 'No breakdown by status')
- (1, 'Non defaulted assets')
- (2, 'Defaulted assets')

---
## Table: `eba_kris`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | period | TEXT | 0 | None | 1 |
| 1 | country | TEXT | 0 | None | 2 |
| 2 | kri_code | TEXT | 0 | None | 3 |
| 3 | kri_name | TEXT | 0 | None | 0 |
| 4 | value | REAL | 0 | None | 0 |

### Sample Data (Limit 3)
- ('2014-12-31', 'AT', 'AQT_3.1', 'Non-performing debt instruments (loans and advances & debt securities) other than held for trading to total gross debt instruments (NPE ratio)', 0.06628183825239581)
- ('2014-12-31', 'BE', 'AQT_3.1', 'Non-performing debt instruments (loans and advances & debt securities) other than held for trading to total gross debt instruments (NPE ratio)', 0.030865486597611937)
- ('2014-12-31', 'BG', 'AQT_3.1', 'Non-performing debt instruments (loans and advances & debt securities) other than held for trading to total gross debt instruments (NPE ratio)', 0.12834243866156309)

---
## Table: `ecb_stats`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | period | TEXT | 0 | None | 0 |
| 1 | variable | TEXT | 0 | None | 0 |
| 2 | group_type | TEXT | 0 | None | 0 |
| 3 | group_name | TEXT | 0 | None | 0 |
| 4 | value | REAL | 0 | None | 0 |

### Sample Data (Limit 3)
- ('2015-06-30', 'CET1 Ratio', 'Country', 'AT', 11.13)
- ('2015-09-30', 'CET1 Ratio', 'Country', 'AT', 11.18)
- ('2015-12-31', 'CET1 Ratio', 'Country', 'AT', 12.03)

---
## Table: `facts_cre`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | id | INTEGER | 0 | None | 0 |
| 1 | lei | TEXT | 0 | None | 0 |
| 2 | period | TEXT | 0 | None | 0 |
| 3 | item_id | TEXT | 0 | None | 0 |
| 4 | portfolio | INTEGER | 0 | None | 0 |
| 5 | country | TEXT | 0 | None | 0 |
| 6 | exposure | INTEGER | 0 | None | 0 |
| 7 | status | INTEGER | 0 | None | 0 |
| 8 | perf_status | INTEGER | 0 | None | 0 |
| 9 | nace_codes | INTEGER | 0 | None | 0 |
| 10 | amount | REAL | 0 | None | 0 |

### Sample Data (Limit 3)
- (1, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2520502', 2, '0', 103, 0, 0, 0, 419.97579665)
- (2, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2520502', 2, '0', 203, 0, 0, 0, 16941.37431464)
- (3, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2520502', 2, '0', 303, 0, 0, 0, 32797.84050106)

---
## Table: `facts_mrk`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | id | INTEGER | 0 | None | 0 |
| 1 | lei | TEXT | 0 | None | 0 |
| 2 | period | TEXT | 0 | None | 0 |
| 3 | item_id | TEXT | 0 | None | 0 |
| 4 | portfolio | INTEGER | 0 | None | 0 |
| 5 | mkt_modprod | INTEGER | 0 | None | 0 |
| 6 | mkt_risk | INTEGER | 0 | None | 0 |
| 7 | amount | REAL | 0 | None | 0 |

### Sample Data (Limit 3)
- (1, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2520401', 1, 0, 0, 2426.03670865)
- (2, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2520401', 5, 0, 0, 2425.6197769)
- (3, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2520402', 1, 1, 0, 1266.53738755)

---
---
## Table: `facts_sov`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | id | INTEGER | 0 | None | 0 |
| 1 | lei | TEXT | 0 | None | 0 |
| 2 | period | TEXT | 0 | None | 0 |
| 3 | item_id | TEXT | 0 | None | 0 |
| 4 | country | TEXT | 0 | None | 0 |
| 5 | maturity | INTEGER | 0 | None | 0 |
| 6 | accounting_portfolio | INTEGER | 0 | None | 0 |
| 7 | amount | REAL | 0 | None | 0 |

### Sample Data (Limit 3)
- (1, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2520810', '1', 3, 0, 3.10)
- (2, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2520810', '1', 3, 0, 3.10)
- (3, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2520810', '1', 3, 0, 3.10)

---
## Table: `facts_oth`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | id | INTEGER | 0 | None | 0 |
| 1 | lei | TEXT | 0 | None | 0 |
| 2 | period | TEXT | 0 | None | 0 |
| 3 | item_id | TEXT | 0 | None | 0 |
| 4 | nsa | TEXT | 0 | None | 0 |
| 5 | assets_fv | INTEGER | 0 | None | 0 |
| 6 | assets_stages | INTEGER | 0 | None | 0 |
| 7 | exposure | INTEGER | 0 | None | 0 |
| 8 | financial_instruments | INTEGER | 0 | None | 0 |
| 9 | amount | REAL | 0 | None | 0 |

### Sample Data (Limit 3)
- (1, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2521001', 'DE', 0, 0, 0, 0, 22438.22306648)
- (2, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2521002', 'DE', 0, 0, 0, 0, 16279.12057071)
- (3, '0W2PZJM8XOY22M4GG883', '2022-09-30', '2521002', 'DE', 1, 0, 0, 0, 3956.73764532)

---
## Table: `facts_sov`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | id | INTEGER | 0 | None | 0 |
| 1 | lei | TEXT | 0 | None | 0 |
| 2 | period | TEXT | 0 | None | 0 |
| 3 | item_id | TEXT | 0 | None | 0 |
| 4 | country | TEXT | 0 | None | 0 |
| 5 | maturity | INTEGER | 0 | None | 0 |
| 6 | accounting_portfolio | INTEGER | 0 | None | 0 |
| 7 | amount | REAL | 0 | None | 0 |

### Sample Data (Limit 3)
- (1, '0W2PZJM8XOY22M4GG883', '2022-12-31', '2520810', '1', 1, 0, 0.0)
- (2, '0W2PZJM8XOY22M4GG883', '2022-12-31', '2520810', '1', 2, 0, 0.0)
- (3, '0W2PZJM8XOY22M4GG883', '2022-12-31', '2520810', '1', 3, 0, 3.10163046)

---
## Table: `institutions`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | lei | TEXT | 0 | None | 1 |
| 1 | name | TEXT | 0 | None | 0 |
| 2 | country_iso | TEXT | 0 | None | 0 |
| 3 | country_name | TEXT | 0 | None | 0 |
| 4 | commercial_name | TEXT | 0 | None | 0 |
| 5 | short_name | TEXT | 0 | None | 0 |
| 6 | ticker | TEXT | 0 | None | 0 |
| 7 | bond_ticker | TEXT | 0 | None | 0 |
| 8 | region | TEXT | 0 | None | 0 |
| 9 | Systemic_Importance | TEXT | 0 | None | 0 |
| 10 | trading_status | TEXT | 0 | None | 0 |
| 11 | bank_type | TEXT | 0 | None | 0 |
| 12 | majority_owner | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- ('529900S9YO2JHTIIDG38', 'BAWAG Group AG', 'AT', 'Austria', 'BAWAG Group AG', 'BAWAG Group AG', 'BG.VI', None, 'Western Europe', 'Other', 'Public', None, None)
- ('9ZHRYM6F437SQJ6OUG95', 'Raiffeisen Bank International AG', 'AT', 'Austria', 'Raiffeisen Bank International AG', 'Raiffeisen Bank International A', 'RBI.VI', None, 'Western Europe', 'Other', 'Public', None, None)
- ('529900SXEWPJ1MRRX537', 'Raiffeisen-Holding Niederösterreich-Wien', 'AT', 'Austria', 'Raiffeisen-Holding Niederösterreich-Wien', 'Raiffeisen-Holding Niederösterr', None, None, 'Western Europe', 'Other', 'Private', None, None)

---
## Table: `item_mappings`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | exercise_year | TEXT | 0 | None | 1 |
| 1 | original_item_id | TEXT | 0 | None | 2 |
| 2 | canonical_item_id | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- ('2024', '2420101', '2520101')
- ('2024', '2420102', '2520102')
- ('2024', '2420103', '2520103')

---
## Table: `kri_to_item`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | kri_name | TEXT | 0 | None | 1 |
| 1 | item_id | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- ('CET 1 capital ratio', '2520140')
- ('Tier 1 capital ratio', '2520141')
- ('Total capital ratio', '2520142')

---
## Table: `macro_economics`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | country | TEXT | 0 | None | 0 |
| 1 | period | TEXT | 0 | None | 0 |
| 2 | indicator | TEXT | 0 | None | 0 |
| 3 | value | REAL | 0 | None | 0 |
| 4 | source | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- ('AT', '2024-12-31', 'GDP Growth (%)', -0.659089573171372, 'World Bank')
- ('AT', '2023-12-31', 'GDP Growth (%)', -0.786244288594673, 'World Bank')
- ('AT', '2022-12-31', 'GDP Growth (%)', 5.33096379400371, 'World Bank')

---
## Table: `market_data`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | date | TEXT | 0 | None | 0 |
| 1 | category | TEXT | 0 | None | 0 |
| 2 | metric | TEXT | 0 | None | 0 |
| 3 | value | REAL | 0 | None | 0 |
| 4 | region | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- ('2020-01-31', 'Yield Curve', 'Yield 10Y (AAA)', -0.1739952290506492, None)
- ('2020-02-29', 'Yield Curve', 'Yield 10Y (AAA)', -0.402813896006994, None)
- ('2020-03-31', 'Yield Curve', 'Yield 10Y (AAA)', -0.5880763725897622, None)

---
## Table: `sqlite_sequence`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | name |  | 0 | None | 0 |
| 1 | seq |  | 0 | None | 0 |

### Sample Data (Limit 3)

---
## Table: `tickers`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | lei | TEXT | 0 | None | 1 |
| 1 | ticker | TEXT | 0 | None | 0 |
| 2 | exchange | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)

---

## Table: `facts_pillar3`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | lei | TEXT | 0 | None | 1 |
| 1 | period | TEXT | 0 | None | 2 |
| 2 | template_code | TEXT | 0 | None | 3 |
| 3 | table_title | TEXT | 0 | None | 0 |
| 4 | row_id | TEXT | 0 | None | 4 |
| 5 | row_label | TEXT | 0 | None | 0 |
| 6 | raw_label | TEXT | 0 | None | 0 |
| 7 | amount | REAL | 0 | None | 0 |
| 8 | eba_item_id | TEXT | 0 | None | 0 |
| 9 | is_new_metric | INTEGER | 0 | None | 0 |
| 10 | source_page | INTEGER | 0 | None | 0 |
| 11 | bank_name | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- ('JEUVK5RWVJEN8W0C9M24', '2025-09-30', 'KM1', 'Eurobank Patch', '1', 'Common Equity Tier 1 (CET1) capital', '1 Common Equity Tier 1 (CET1) capital 8,049', 8049000000.0, '2520102', 0, 20, 'Eurobank')

---

## Table: `pillar3_dictionary`
| CID | Name | Type | NotNull | DfltVal | PK |
|---|---|---|---|---|---|
| 0 | p3_item_id | TEXT | 0 | None | 1 |
| 1 | template_code | TEXT | 0 | None | 0 |
| 2 | row_id | TEXT | 0 | None | 0 |
| 3 | p3_label | TEXT | 0 | None | 0 |
| 4 | eba_item_id | TEXT | 0 | None | 0 |
| 5 | notes | TEXT | 0 | None | 0 |
| 6 | category | TEXT | 0 | None | 0 |

### Sample Data (Limit 3)
- ('KM1_1', 'KM1', '1', 'Common Equity Tier 1 (CET1) capital', '2520102', '', 'Capital')
- ('OV1_29', 'OV1', '29', 'Total', '2520220', '', 'RWA')

---


