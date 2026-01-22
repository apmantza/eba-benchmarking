# Currency Conversion Implementation Summary

## Problem
The application was showing incorrect P/B ratios and other metrics for banks listed in non-EUR currencies:
- **AIB (Ireland)**: P/B ratio of 136.73 (should be ~1.63)
- **Nordic banks** (SEK, NOK): All metrics in local currency
- **CEE banks** (PLN, HUF, RON): All metrics in local currency
- **UK-listed banks** (GBp): Prices in pence mixed with EUR financial data

## Solution Implemented

### 1. Currency Conversion Utilities
Added comprehensive FX conversion functions in `market.py`:
- `get_fx_rate(currency)`: Fetches current FX rate from Yahoo Finance
- `get_fx_history(currency, period)`: Fetches historical FX rates
- `convert_to_eur(value, currency, fx_rate)`: Converts values to EUR

### 2. Supported Currencies
- EUR (no conversion)
- GBp (British Pence - special handling)
- SEK (Swedish Krona)
- NOK (Norwegian Krone)
- DKK (Danish Krone)
- PLN (Polish Zloty)
- HUF (Hungarian Forint)
- RON (Romanian Leu)
- ISK (Icelandic Króna)
- CHF (Swiss Franc)
- USD (US Dollar)
- GBP (British Pound)

### 3. Dual Currency Handling
Yahoo Finance uses two currencies for some stocks:
- **Listing Currency**: Used for prices, market cap (e.g., GBp for AIB)
- **Financial Currency**: Used for book value, EPS, dividends (e.g., EUR for AIB)

Our implementation correctly handles both:
- `to_eur_price()`: Converts price-based metrics using listing currency
- `to_eur_financial()`: Converts financial metrics using financial currency

### 4. What Gets Converted

#### Price-based (Listing Currency):
- Current price, previous close, open, high, low
- 52-week high/low
- Market cap, enterprise value
- Analyst target prices

#### Financial (Financial Currency):
- EPS (trailing, forward)
- DPS (trailing)
- Book value
- Dividend rate, last dividend value

#### Not Converted (Ratios):
- P/E, P/B, P/S ratios
- Dividend yield, payout ratio
- Beta, returns

### 5. Database Schema Updates
Added to `market_data` table:
- `currency TEXT`: Stores listing currency
- `fx_rate_to_eur REAL`: Stores FX rate used for conversion

## Results

### Before Fix:
| Bank | Currency | P/B Ratio | Issue |
|------|----------|-----------|-------|
| AIB | GBp | 136.73 | Pence mixed with EUR |
| DNB | NOK | N/A | All in NOK |
| SEB | SEK | N/A | All in SEK |

### After Fix:
| Bank | Currency | P/B Ratio | Status |
|------|----------|-----------|--------|
| AIB | GBp→EUR | 1.58 | ✓ Correct |
| DNB | NOK→EUR | TBD | ✓ Will convert |
| SEB | SEK→EUR | TBD | ✓ Will convert |

## Next Steps

1. **Refresh Market Data**: Run `refresh_market_data()` to update all banks with EUR-converted values
2. **Historical Data**: Implement FX conversion for historical price data (5-year monthly)
3. **Financial Year Data**: Implement FX conversion for FY attribution engine
4. **Testing**: Verify all 47 banks have correct EUR-normalized metrics

## Technical Notes

- FX rates are fetched in real-time from Yahoo Finance (e.g., `EURSEK=X`)
- For EUR/XXX pairs, we invert the rate (1/rate) to get XXX→EUR
- For GBP/EUR pairs, we use the rate directly
- GBp (pence) is divided by 100 before conversion to GBP
- All conversions are cached to minimize API calls
