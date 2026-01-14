# Calculations Documentation

This document provides comprehensive documentation of all calculations performed in the EBA Benchmarking Dashboard, including item IDs, source tables, and calculation formulas.

## Table of Contents

1. [Solvency Tab Calculations](#solvency-tab-calculations)
2. [Asset Quality Tab Calculations](#asset-quality-tab-calculations)
3. [RWA Tab Calculations](#rwa-tab-calculations)
4. [Profitability Tab Calculations](#profitability-tab-calculations)
5. [Liquidity Tab Calculations](#liquidity-tab-calculations)
6. [Assets Tab Calculations](#assets-tab-calculations)
7. [Liabilities Tab Calculations](#liabilities-tab-calculations)
8. [Sovereign Tab Calculations](#sovereign-tab-calculations)
9. [Yields & Funding Tab Calculations](#yields--funding-tab-calculations)
10. [Market Data Tab Calculations](#market-data-tab-calculations)

---

## Solvency Tab Calculations

### Source Table: `facts_oth`

| Item ID | Label | Description |
|---------|-------|-------------|
| 2520102 | CET1 Capital | Common Equity Tier 1 capital |
| 2520129 | AT1 Capital | Additional Tier 1 capital |
| 2520135 | Tier 2 Capital | Tier 2 capital instruments |
| 2520138 | TREA | Total Risk Exposure Amount |
| 2520140 | CET1 Ratio | CET1 capital ratio |
| 2520142 | Total Capital Ratio | Total capital ratio |
| 2520905 | Leverage Ratio | Leverage ratio |
| 2521010 | Total Assets | Total assets (for density calc) |

### Calculated Metrics

#### Total Capital
```python
Total Capital = CET1 Capital + AT1 Capital + Tier 2 Capital
```
**Item IDs**: 2520102 + 2520129 + 2520135

#### RWA Density
```python
RWA Density = TREA / Total Assets
```
**Item IDs**: 2520138 / 2521010
**Source**: `solvency.py:get_solvency_kpis()`

#### Texas Ratio
```python
Texas Ratio = NPL_Amount / (CET1 Capital + Total Provisions)
```
**Item IDs**: 
- NPL_Amount: `facts_cre` item 2520603 with perf_status=2
- CET1 Capital: 2520102
- Total Provisions: `facts_cre` item 2520613

**Source**: `solvency.py:get_solvency_with_texas_ratio()`

#### AT1 Ratio (Calculated)
```python
AT1 Ratio (calc) = AT1 Capital / TREA
```
**Item IDs**: 2520129 / 2520138

#### Tier 2 Ratio (Calculated)
```python
Tier 2 Ratio (calc) = Tier 2 Capital / TREA
```
**Item IDs**: 2520135 / 2520138

---

## Asset Quality Tab Calculations

### Source Table: `facts_cre`

| Item ID | Label | Description |
|---------|-------|-------------|
| 2520603 | Gross Loans | Gross carrying amount on Loans and advances |
| 2520613 | Total Provisions | Accumulated impairment on Loans and advances |
| 2520703 | Forborne Gross | Forborne exposures gross carrying amount |
| 2520713 | Forborne Provisions | Forborne exposures provisions |
| 2521708 | Accumulated Write-offs | Accumulated partial write-off |

### Performance Status Dimensions

| perf_status | Label | Usage |
|-------------|-------|-------|
| 1 | Performing | Stage 1 loans |
| 12 | Stage 2 | Significant increase in credit risk |
| 2 | Non-performing | Stage 3/NPL loans |

### Calculated Metrics

#### NPL Ratio
```python
npl_ratio = Stage 3 Gross Loans / (Performing Gross Loans + Stage 3 Gross Loans)
```
**Formula**: `Exp_2 / (Exp_1 + Exp_2)`
**Source**: `asset_quality.py:get_aq_breakdown()`

#### Stage 3 Coverage
```python
Stage 3 Coverage = Stage 3 Provisions / Stage 3 Gross Loans
```
**Formula**: `Prov_23 / Exp_23`

#### Stage 2 Coverage
```python
Stage 2 Coverage = Stage 2 Provisions / Stage 2 Gross Loans
```
**Formula**: `Prov_12 / Exp_12`

#### Stage 2 Ratio
```python
Stage 2 Ratio = Stage 2 Gross Loans / Performing Gross Loans
```
**Formula**: `Exp_12 / Exp_1`

#### Forborne Ratio
```python
Forborne Ratio = Total Forborne Exposures / Total Loans
```
**Formula**: Sum(Forb_Exp_*) / (Exp_1 + Exp_2)

#### Write-off Rate
```python
Write-off Rate = Accumulated Write-offs / NPL Amount
```
**Formula**: `WriteOff_Total / Exp_2`

#### Total Provisions
```python
Total Provisions = Prov_1 + Prov_2 + Prov_12
```
Sums provisions across all performance statuses.

---

## RWA Tab Calculations

### Source Table: `facts_oth`

| Item ID | Label | Description |
|---------|-------|-------------|
| 2520201 | RWA: Credit Risk | Credit risk RWA |
| 2520211 | RWA: Market Risk | Market risk RWA |
| 2520215 | RWA: Operational Risk | Operational risk RWA |
| 2520220 | Total RWA | Total risk exposure amount |

### Calculated Metrics

#### RWA Density (from Solvency Tab)
```python
RWA Density = Total RWA / Total Assets
```
**Item IDs**: 2520220 / 2521010

#### RWA Composition Percentages
```python
Credit Risk % = RWA: Credit Risk / Total RWA * 100
Market Risk % = RWA: Market Risk / Total RWA * 100
Operational Risk % = RWA: Operational Risk / Total RWA * 100
```

**Source**: `solvency.py:get_rwa_composition()`

---

## Profitability Tab Calculations

### Source Table: `facts_oth`

#### Income Items
| Item ID | Label | Description |
|---------|-------|-------------|
| 2520301 | Interest Income | Total interest income |
| 2520302 | Int Inc: Debt Securities | Interest income from debt securities |
| 2520303 | Int Inc: Loans | Interest income from loans |
| 2520308 | Dividend Income | Dividend income |
| 2520309 | Net Fee & Commission Income | Net fee and commission income |
| 2520311 | Trading Income | Gains/losses on trading |
| 2520314 | FX Income | Exchange differences |
| 2520315 | Other Operating Income | Other operating income |
| 2520316 | Total Operating Income | TOTAL OPERATING INCOME |

#### Expense Items
| Item ID | Label | Description |
|---------|-------|-------------|
| 2520304 | Interest Expenses | Total interest expenses |
| 2520305 | Int Exp: Deposits | Interest expenses on deposits |
| 2520306 | Int Exp: Debt Securities | Interest expenses on debt securities |
| 2520317 | Admin Expenses | Administrative expenses |
| 2520318 | Depreciation | Depreciation |
| 2520324 | Impairment Cost | Impairment cost |
| 2520332 | Profit Before Tax | Profit before tax |
| 2520335 | Net Profit | Net profit for the period |

#### Balance Sheet Items
| Item ID | Label | Description |
|---------|-------|-------------|
| 2521216 | Total Equity | Total equity |
| 2521010 | Total Assets | Total assets |
| 2520138 | TREA | Total Risk Exposure Amount |

### Annualization Factor
```python
ann_factor = 12 / month_of_period
```
Where month_of_period is extracted from the period string (e.g., '2023-03' -> 3)

### Calculated Metrics

#### Return on Equity (RoE)
```python
RoE (YTD) = Net Profit / Total Equity
RoE (Annualized) = RoE (YTD) * ann_factor
```
**Source**: `profitability.py:get_profitability_kpis()`

#### Return on Assets (RoA)
```python
RoA (YTD) = Net Profit / Total Assets
RoA (Annualized) = RoA (YTD) * ann_factor
```

#### Return on RWA (RoRWA)
```python
RoRWA (YTD) = Net Profit / TREA
RoRWA (Annualized) = RoRWA (YTD) * ann_factor
```

#### Cost-to-Income Ratio (CIR)
```python
Operating Expenses = Admin Expenses + Depreciation
Cost to Income = Operating Expenses / Total Operating Income
```
**Item IDs**: (2520317 + 2520318) / 2520316

#### Net Interest Margin (NIM)
```python
Net Interest Income = Interest Income - Interest Expenses
NIM (YTD) = Net Interest Income / Total Assets
NIM (Annualized) = NIM (YTD) * ann_factor
```
**Item IDs**: (2520301 - 2520304) / 2521010

#### Net Interest Income
```python
Net Interest Income = Interest Income - Interest Expenses
```

#### Non-Interest Income
```python
Non-Interest Income = Total Operating Income - Net Interest Income
```

#### Net Trading Income
```python
Net Trading Income = Trading Income + FX Income
```
**Item IDs**: 2520311 + 2520314

#### Tax Expenses
```python
Tax Expenses = Profit Before Tax - Net Profit
```
**Item IDs**: 2520332 - 2520335

#### Net Fees / Assets
```python
Net Fees / Assets (YTD) = Net Fee & Commission Income / Total Assets
Net Fees / Assets (Annualized) = Net Fees / Assets (YTD) * ann_factor
```

#### Cost of Risk
```python
Cost of Risk (YTD) = Impairment Cost / Total Assets
Cost of Risk (Annualized) = Cost of Risk (YTD) * ann_factor
```

#### Cost per Assets
```python
Cost per Assets (YTD) = Operating Expenses / Total Assets
Cost per Assets (Annualized) = Cost per Assets (YTD) * ann_factor
```

#### Jaws Ratio
```python
OpInc Growth = pct_change(Total Operating Income, periods=4)
OpExp Growth = pct_change(Admin Expenses, periods=4)
Jaws Ratio = OpInc Growth - OpExp Growth
```
Calculates YoY growth difference for quarterly data.

---

## Liquidity Tab Calculations

### Source Table: `facts_oth`

#### Loan Items
| Item ID | Label | Description |
|---------|-------|-------------|
| 2521017 | Loans FV | Loans at fair value |
| 2521019 | Loans AC | Loans at amortized cost |

#### Deposit Items
| Item ID | Label | Description |
|---------|-------|-------------|
| 2521215 | Liabilities Breakdown | Financial liabilities by instrument/counterparty |

#### Deposit Dimensions
- `financial_instruments = 30` (Deposits)
- `exposure IN (301, 401)` (NFC + Households)

### Calculated Metrics

#### Total Loans
```python
Total Loans = Loans FV + Loans AC
```
**Item IDs**: 2521017 + 2521019
**Source**: `liquidity.py:get_liquidity_kpis()`

#### Customer Deposits
```python
Customer Deposits = SUM(amount)
WHERE item_id = '2521215'
  AND financial_instruments = 30
  AND exposure IN (301, 401)
```

#### Loan-to-Deposit Ratio (LDR)
```python
LDR = Total Loans / Customer Deposits
```
If Customer Deposits = 0, LDR = 0

#### Funding Gap
```python
Funding Gap = Total Loans - Customer Deposits
```
Expressed in millions EUR.

#### Deposit Coverage
```python
Deposit Coverage = Customer Deposits / Total Loans
```
Inverse of LDR, shows what percentage of loans is funded by deposits.

---

## Assets Tab Calculations

### Source Table: `facts_oth`

| Item ID | Label | Description |
|---------|-------|-------------|
| 2521010 | Total Assets | Total assets |
| 2521001 | Cash | Cash and cash equivalents |
| 2521017 | Loans FV | Loans at fair value |
| 2521019 | Loans AC | Loans at amortized cost |
| 2521016 | Debt Sec FV | Debt securities FV |
| 2521018 | Debt Sec AC | Debt securities AC |
| 2521002 | Trading Assets | Financial assets held for trading |
| 2521003 | Non-Trading FVTPL | Non-trading financial assets mandatorily at FVTPL |
| 2521004 | Designated FVTPL | Financial assets designated at FVTPL |

### Calculated Metrics

#### Loans and Advances
```python
Loans and advances = Loans FV + Loans AC
```

#### Debt Securities
```python
Debt Securities = Debt Sec FV + Debt Sec AC
```

#### Total Securities
```python
Securities = Debt Securities + Trading Assets + Non-Trading FVTPL + Designated FVTPL
```

#### Other Assets
```python
Other Assets = Total Assets - Cash - Loans and advances - Securities
```

#### Loans to Assets Ratio
```python
Loans to Assets = Loans and advances / Total Assets
```

#### Cash to Assets Ratio
```python
Cash to Assets = Cash / Total Assets
```

#### Securities to Assets Ratio
```python
Securities to Assets = Securities / Total Assets
```

---

## Liabilities Tab Calculations

### Source Table: `facts_oth`

| Item ID | Label | Description |
|---------|-------|-------------|
| 2521214 | Total Liabilities | Total liabilities |
| 2521215 | Liabilities Breakdown | Financial liabilities by instrument/counterparty |
| 2520102 | Equity (CET1) | CET1 Capital (proxy for equity) |

#### Liabilities Dimensions
- `financial_instruments = 30`, `exposure = 101`: Central Bank Funding
- `financial_instruments = 30`, `exposure = 102`: Interbank Deposits
- `financial_instruments = 30`, `exposure IN (301, 401)`: Customer Deposits
- `financial_instruments = 40`: Debt Securities Issued
- `financial_instruments = 12`: Derivatives

### Calculated Metrics

#### Customer Deposits
```python
Customer Deposits = SUM(amount)
WHERE item_id = '2521215'
  AND financial_instruments = 30
  AND exposure IN (301, 401)
```

#### Interbank Deposits
```python
Interbank Deposits = SUM(amount)
WHERE item_id = '2521215'
  AND financial_instruments = 30
  AND exposure = 102
```

#### Central Bank Funding
```python
Central Bank Funding = SUM(amount)
WHERE item_id = '2521215'
  AND financial_instruments = 30
  AND exposure = 101
```

#### Debt Securities Issued
```python
Debt Securities Issued = SUM(amount)
WHERE item_id = '2521215'
  AND financial_instruments = 40
```

#### Derivatives (Liability)
```python
Derivatives (Liab) = SUM(amount)
WHERE item_id = '2521215'
  AND financial_instruments = 12
```

#### Other Liabilities
```python
Other Liabilities = Total Liabilities - Known Liabilities
```

#### Total Equity and Liabilities
```python
total_eq_liab = total_liabilities + equity
```

#### Customer Deposit Ratio
```python
Customer Deposit Ratio = Customer Deposits / total_eq_liab
```

#### Wholesale Funding Ratio
```python
Wholesale Funding Ratio = (Interbank Deposits + Debt Securities Issued) / total_eq_liab
```

#### Equity Ratio
```python
Equity Ratio = equity / total_eq_liab
```

---

## Sovereign Tab Calculations

### Source Table: `facts_sov`

| Item ID | Label | Description |
|---------|-------|-------------|
| 2520812 | Held for trading | Sovereign HFT |
| 2520813 | Designated at FV | Sovereign designated at FV |
| 2520814 | FVOCI | Sovereign at FVOCI |
| 2520815 | Amortised Cost | Sovereign at AC |

#### Dimensions
- `country`: Issuer country (from `dim_country`)
- `maturity`: Maturity bucket (from `dim_maturity`)
- `accounting_portfolio`: Portfolio classification

### Maturity Mapping
```python
maturity_map = {
    1: 0.125,   # 0-3 months
    2: 0.625,   # 3 months-1 year
    3: 1.5,     # 1-2 years
    4: 2.5,     # 2-5 years
    5: 4.0,     # 5-10 years
    6: 7.5,     # 10-20 years
    7: 15.0     # >20 years
}
```

### Calculated Metrics

#### Total Sovereign Exposure
```python
Total Sovereign = SUM(all portfolio amounts)
```

#### Portfolio Composition
```python
HFT % = Held for trading / Total Sovereign * 100
FVOCI % = FVOCI / Total Sovereign * 100
AC % = Amortised Cost / Total Sovereign * 100
```

#### Weighted Average Maturity
```python
WAM = SUM(maturity_years * amount) / SUM(amount)
```

#### Concentration Ratio
```python
Concentration Ratio = Largest Country Exposure / CET1 Capital
```

#### Home Bias Ratio
```python
Home Bias = Home Country Sovereign Exposure / CET1 Capital
```

---

## Yields & Funding Tab Calculations

### Source Data
Combines data from:
- `profitability.py:get_profitability_kpis()` (income/expense items)
- `assets.py:get_assets_kpis()` (loan/securities volumes)
- `liabilities.py:get_liabilities_kpis()` (deposit/debt volumes)
- `base_rates` table (ECB rates)

### Interest Rate Calculations

#### Implied Loan Yield
```python
Implied Loan Yield = (Int Inc: Loans / Loans and advances) * ann_factor
```
**Item IDs**: 2520303 / (2521017 + 2521019)

#### Implied Securities Yield
```python
Implied Securities Yield = (Int Inc: Debt Securities / Debt Securities) * ann_factor
```
**Item IDs**: 2520302 / (2521016 + 2521018)

#### Implied Deposit Cost
```python
Implied Deposit Cost = (Int Exp: Deposits / Customer Deposits) * ann_factor
```
**Item IDs**: 2520305 / Customer Deposits

#### Implied Debt Cost
```python
Implied Debt Cost = (Int Exp: Debt Securities / Debt Securities Issued) * ann_factor
```
**Item IDs**: 2520306 / Debt Securities Issued

#### Implied Interbank Cost
```python
Implied Interbank Cost = (
    (Interest Expenses - Int Exp: Deposits - Int Exp: Debt Securities) /
    (total_liabilities - Customer Deposits - Debt Securities Issued)
) * ann_factor
```

#### Implied Funding Cost
```python
Implied Funding Cost = (Interest Expenses / total_liabilities) * ann_factor
```
**Item IDs**: 2520304 / 2521214

### Margin Calculations (vs Euribor 3M)

#### Euribor 3M Rate
```python
euribor_decimal = base_rates.value / 100
```

#### Margin Formulas
```python
Margin: Loan Yield = Implied Loan Yield - euribor_decimal
Margin: Securities Yield = Implied Securities Yield - euribor_decimal
Margin: Deposit Cost = Implied Deposit Cost - euribor_decimal
Margin: Funding Cost = Implied Funding Cost - euribor_decimal
```

---

## Market Data Tab Calculations

### Source: Yahoo Finance API

#### Valuation Metrics

##### Price-to-Book (P/B)
```python
P/B = Market Cap / Total Equity
```
From Yahoo Finance: `priceToBook`

##### Price-to-Earnings (P/E)
```python
P/E = Market Cap / Net Income
```
From Yahoo Finance: `trailingPE`

##### Dividend Yield
```python
Dividend Yield = Annual Dividends per Share / Current Price
```
Calculated from TTM dividends.

#### Return Calculations

##### 1-Year Return
```python
return_1y = (Current Price - Price_1Y_ago) / Price_1Y_ago
```

##### YTD Return
```python
ytd_return = (Current Price - Price_Year_Start) / Price_Year_Start
```

##### Beta (Systematic Risk)
```python
Beta = Cov(Stock Returns, Market Returns) / Var(Market Returns)
```
From Yahoo Finance: `beta`

#### Analyst Metrics

##### Upside Potential
```python
Upside (%) = (Target Mean Price - Current Price) / Current Price * 100
```

---

## Benchmarking Calculations

### Weighted Averages

All peer group averages use asset-weighted methodology:

```python
def weighted_avg(group, value_col, weight_col):
    valid = group[[value_col, weight_col]].dropna()
    if valid[weight_col].sum() > 0:
        return (valid[value_col] * valid[weight_col]).sum() / valid[weight_col].sum()
    return group[value_col].mean()
```

#### Weight Columns by Metric Type
- **Solvency Ratios**: Weighted by TREA
- **Profitability Ratios**: Weighted by Total Assets
- **Liquidity Ratios**: Weighted by Loans
- **Asset Quality**: Weighted by Total Loans

### Texas Ratio (Group Level)
```python
Group Texas Ratio = Sum(NPL_Amount) / Sum(CET1 Capital + Total Provisions)
```

---

## Data Quality Rules

### Outlier Thresholds
```python
OUTLIER_THRESHOLDS = {
    'CET1_MAX': 0.25,       # 25% - exclude if higher
    'TC_MAX': 0.35,         # 35% - exclude if higher
    'NPL_MAX': 0.50,        # 50% - exclude if higher
    'ROE_MIN': -0.50,       # -50% - exclude if lower
    'ROE_MAX': 0.50,        # 50% - exclude if higher
    'CTI_MAX': 1.50,        # 150% - Cost to Income outlier
    'RWA_DENSITY_MAX': 1.0, # 100% - RWA > Assets is impossible
}
```

### Rate Bounds (Implied Rates)
```python
# Implied rates are bounded between 0% and 20%
rate_cols = ['Implied Loan Yield', 'Implied Securities Yield', 
             'Implied Deposit Cost', 'Implied Debt Cost', 
             'Implied Interbank Cost', 'Implied Funding Cost']

df[col] = df[col].apply(lambda x: x if 0 <= x <= 0.20 else 0)
```

---

## Period Handling

### Annualization Factor
```python
month = int(period.split('-')[1])  # Extract month from 'YYYY-MM-DD'
ann_factor = 12 / month
```

This converts YTD values to annualized equivalents:
- Q1 (month=3): Factor = 4
- Q2 (month=6): Factor = 2
- Q3 (month=9): Factor = 1.33
- Q4 (month=12): Factor = 1

---

## File References

| Module | File Path | Key Functions |
|--------|-----------|---------------|
| Solvency | `src/eba_benchmarking/data/solvency.py` | `get_solvency_kpis()`, `get_solvency_with_texas_ratio()` |
| Asset Quality | `src/eba_benchmarking/data/asset_quality.py` | `get_aq_breakdown()` |
| Profitability | `src/eba_benchmarking/data/profitability.py` | `get_profitability_kpis()`, `calculate_implied_rates()` |
| Liquidity | `src/eba_benchmarking/data/liquidity.py` | `get_liquidity_kpis()` |
| Assets | `src/eba_benchmarking/data/assets.py` | `get_assets_kpis()` |
| Liabilities | `src/eba_benchmarking/data/liabilities.py` | `get_liabilities_kpis()` |
| Sovereign | `src/eba_benchmarking/data/sovereign.py` | `get_sovereign_kpis()` |
| Market | `src/eba_benchmarking/data/market.py` | `get_market_data()` |
