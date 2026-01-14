# EBA Data Dimensions Reference

This document provides a comprehensive reference of all dimension tables used in the EBA Benchmarking database.

## Table of Contents

1. [dim_perf_status](#dim_perf_status---performance-status)
2. [dim_portfolio](#dim_portfolio---credit-risk-portfolio)
3. [dim_maturity](#dim_maturity---maturity-buckets)
4. [dim_country](#dim_country---country-codes)
5. [dim_exposure](#dim_exposure---exposure-type)
6. [dim_financial_instruments](#dim_financial_instruments---instrument-type)
7. [dim_status](#dim_status---default-status)
8. [dim_assets_stages](#dim_assets_stages---ifrs-9-stages)
9. [dim_assets_fv](#dim_assets_fv---fair-value-hierarchy)
10. [dim_nace_codes](#dim_nace_codes---industry-codes)
11. [dim_mkt_risk](#dim_mkt_risk---market-risk-type)
12. [dim_mkt_modprod](#dim_mkt_modprod---market-product-type)

---

## dim_perf_status: Performance Status

Used in `facts_cre` to indicate IFRS 9 staging and credit quality.

| ID | Label | Description |
|----|-------|-------------|
| 0 | No breakdown by Perf_status | Total without breakdown |
| 1 | Performing | Stage 1: Normal credit risk |
| 11 | Performing - of which exposures with forbearance measures | Forborne performing |
| 12 | Performing Of which: Instruments with significant increase in credit risk since initial recognition but not credit-impaired (Stage 2) | Stage 2: SICR but not credit-impaired |
| 2 | Non Performing | Stage 3: Credit-impaired |
| 21 | Non Performing Of which: exposures with forbearance measures | Forborne non-performing |
| 22 | Non Performing Of which: Unlikely to pay that are not past-due or past-due <= 90 days | Unlikely to pay |
| 222 | Non Performing Of which: Stage 2 | Stage 2 non-performing |
| 23 | NON performing - of which Stage 3 | Stage 3 explicit |
| 3 | Performing but past due >30 days and <=90 days | Past due 30-90 days |
| 4 | Non Performing and Defaulted | Defaulted |
| 5 | Loans and advances subject to impairment | Subject to impairment |

---

## dim_portfolio: Credit Risk Portfolio

Used in `facts_cre` to classify credit risk approaches.

| ID | Label | Description |
|----|-------|-------------|
| 0 | Total / No breakdown by portfolio | Total without breakdown |
| 1 | SA | Standardized Approach |
| 2 | IRB | Internal Ratings-Based Approach |
| 3 | F-IRB | Foundation IRB |
| 4 | A-IRB | Advanced IRB |
| 5 | IM | Internal Models |
| 6 | Fixed rate portfolio | Fixed rate |
| 7 | Floating rate portfolio | Floating rate |

---

## dim_maturity: Maturity Buckets

Used in `facts_sov` and other tables for maturity analysis.

| ID | Label | Years (weighted avg) |
|----|-------|---------------------|
| 1 | [ 0 - 3M [ | 0.125 |
| 2 | [ 3M - 1Y [ | 0.625 |
| 3 | [ 1Y - 2Y [ | 1.5 |
| 4 | [ 2Y - 5Y [ | 2.5 |
| 5 | [ 5Y - 10Y [ | 4.0 |
| 6 | [ 10Y - 20Y [ | 7.5 |
| 7 | [ > 20Y [ | 15.0 |
| 8 | No breakdown | - |

---

## dim_country: Country Codes

Complete list of countries and regions (see full table in file). Key EU countries:

| ID | Label | ISO Code |
|----|-------|----------|
| 0 | Total / No breakdown | 00 |
| 1 | Austria | AT |
| 2 | Belgium | BE |
| 3 | Bulgaria | BG |
| 4 | Cyprus | CY |
| 5 | Czech Republic | CZ |
| 6 | Denmark | DK |
| 7 | Estonia | EE |
| 8 | Finland | FI |
| 9 | France | FR |
| 10 | Germany | DE |
| 11 | Greece | GR |
| 12 | Hungary | HU |
| 13 | Iceland | IS |
| 14 | Ireland | IE |
| 15 | Italy | IT |
| 16 | Latvia | LV |
| 17 | Liechtenstein | LI |
| 18 | Lithuania | LT |
| 19 | Luxembourg | LU |
| 20 | Malta | MT |
| 21 | Netherlands | NL |
| 22 | Norway | NO |
| 23 | Poland | PL |
| 24 | Portugal | PT |
| 25 | Romania | RO |
| 26 | Slovakia | SK |
| 27 | Slovenia | SI |
| 28 | Spain | ES |
| 29 | Sweden | SE |
| 30 | United Kingdom | GB |

---

## dim_exposure: Exposure Type

Used in `facts_cre` and `facts_oth` for counterparty classification.

| ID | Label | Description |
|----|-------|-------------|
| 0 | Total / No breakdown | Total without breakdown |
| 101 | Central banks | Central bank exposures |
| 102 | General governments | Government exposures |
| 103 | Credit institutions | Bank exposures (interbank) |
| 104 | Other financial corporations | Other financial institutions |
| 201 | Non-financial corporations - Small and Medium-sized Enterprises | SME corporates |
| 202 | Non-financial corporations - Small and Medium-sized Enterprises - Exposure to SME | SME exposure |
| 203 | Non-financial corporations - Other | Other corporates |
| 204 | Non-financial corporations - Other - Exposure to property | Property developers |
| 301 | Households - Other household lending | Other retail |
| 401 | Households - Residential mortgages | Residential mortgages |
| 501 | Households - Other secured lending | Other secured retail |
| 601 | Households - Credit card lending | Credit cards |
| 701 | Households - Other revolving retail | Revolving credit |
| 801 | Households - Student loans | Student loans |
| 901 | Households - Exposure to Retail SME | Retail SME |

---

## dim_financial_instruments: Instrument Type

Used in `facts_oth` for liability breakdown.

| ID | Label | Description |
|----|-------|-------------|
| 0 | Total / No breakdown | Total without breakdown |
| 12 | Derivatives | Derivative positions |
| 21 | Short positions - Equity instruments | Short equity positions |
| 22 | Short positions - Debt instruments | Short debt positions |
| 30 | Deposits | Deposit liabilities |
| 31 | Current accounts and overnight deposits | Demand deposits |
| 32 | Time deposits with agreed maturity | Term deposits |
| 33 | Deposits redeemable at notice | Notice deposits |
| 40 | Debt securities issued | Issued bonds/notes |
| 41 | Subordinated debt | Tier 2/subordinated |
| 50 | Other liabilities | Other liability items |

---

## dim_status: Default Status

Used in `facts_cre` for default classification.

| ID | Label | Description |
|----|-------|-------------|
| 0 | No breakdown by status | Total without breakdown |
| 1 | Non defaulted assets | Performing |
| 2 | Defaulted assets | Non-performing |

---

## dim_assets_stages: IFRS 9 Stages

Used for IFRS 9 asset staging classification.

| ID | Label | Description |
|----|-------|-------------|
| 0 | No breakdown by ASSETS_Stages | Total without breakdown |
| 1 | Stage 1 | No significant increase in credit risk |
| 2 | Stage 2 | Significant increase in credit risk |
| 3 | Stage 3 | Credit-impaired |

---

## dim_assets_fv: Fair Value Hierarchy

| ID | Label | Description |
|----|-------|-------------|
| 0 | No breakdown by ASSETS_FV | Total without breakdown |
| 1 | Fair value hierarchy: Level 1 | Level 1 (quoted prices) |
| 2 | Fair value hierarchy: Level 2 | Level 2 (observable inputs) |
| 3 | Fair value hierarchy: Level 3 | Level 3 (unobservable inputs) |

---

## dim_nace_codes: NACE Industry Codes

Industry sector classification (financial institutions).

| ID | Label | Description |
|----|-------|-------------|
| 0 | No breakdown by NACE_codes | Total without breakdown |
| 1 | A Agriculture, forestry and fishing | Agriculture |
| 2 | B Mining and quarrying | Mining |
| 3 | C Manufacturing | Manufacturing |
| 4 | D Electricity, gas, steam and air conditioning supply | Utilities |
| 5 | E Water supply | Water |
| 6 | F Construction | Construction |
| 7 | G Wholesale and retail trade | Retail trade |
| 8 | H Transport and storage | Transport |
| 9 | I Accommodation and food service activities | Hospitality |
| 10 | J Information and communication | ICT |
| 11 | K Financial and insurance activities | Financial services |
| 12 | L Real estate activities | Real estate |
| 13 | M Professional, scientific and technical activities | Professional services |
| 14 | N Administrative and support service activities | Admin services |
| 15 | O Public administration and defence | Government |
| 16 | P Education | Education |
| 17 | Q Human health and social work activities | Healthcare |
| 18 | R Arts, entertainment and recreation | Arts |
| 19 | S Other service activities | Other services |
| 20 | T Activities of households as employers | Households |
| 21 | U Activities of extraterritorial organisations | International |

---

## dim_mkt_risk: Market Risk Type

Used in `facts_mrk` for market risk classification.

| ID | Label | Description |
|----|-------|-------------|
| 0 | No breakdown by MKT_Risk | Total without breakdown |
| 1 | General risk | General market risk |
| 2 | Specific risk | Specific risk |
| 3 | Option risk | Option-related risk |
| 4 | Correlation risk | Correlation risk |

---

## dim_mkt_modprod: Market Product Type

Used in `facts_mrk` for product classification.

| ID | Label | Description |
|----|-------|-------------|
| 0 | No breakdown by MKT_Modprod | Total without breakdown |
| 1 | Traded debt instruments | Trading book debt |
| 2 | Equities | Equity instruments |
| 3 | Commodities | Commodity positions |
| 4 | Credit derivatives | Credit derivatives |
| 5 | Foreign exchange | FX positions |
| 6 | Interest rate derivatives | IR derivatives |
| 7 | Collective investments | Fund units |
| 8 | Other instruments | Other |

---

## dim_accounting_portfolio: Accounting Classification

| ID | Label | Description |
|----|-------|-------------|
| 0 | No breakdown by Accounting_portfolio | Total without breakdown |
| 1 | Held for trading (HFT) | Trading book |
| 2 | Designated at fair value through profit or loss | Designated FVTPL |
| 3 | Fair value through other comprehensive income | FVOCI |
| 4 | Amortised cost | AC |

---

## Usage Notes

### Common Dimension Combinations

**Credit Risk Analysis**:
- `perf_status`: Stage 1/2/3 classification
- `portfolio`: SA/IRB approach
- `exposure`: Counterparty type
- `nace_codes`: Industry sector

**Sovereign Analysis**:
- `country`: Issuer country
- `maturity`: Maturity bucket
- `accounting_portfolio`: Portfolio classification

**Liability Analysis**:
- `financial_instruments`: Instrument type
- `exposure`: Counterparty sector

|   perf_status | label                                                                                                                                 |
|--------------:|:--------------------------------------------------------------------------------------------------------------------------------------|
|             0 | No breakdown by Perf_status                                                                                                           |
|             1 | Performing                                                                                                                            |
|            11 | Performing - of which exposures with forbearance measures                                                                             |
|            12 | Performing Of which: Instruments with significant increase in credit risk since initial recognition but not credit-impaired (Stage 2) |
|             2 | Non Performing                                                                                                                        |
|            21 | Non Performing Of which:                                                                                                              |
|               | exposures with forbearance measures                                                                                                   |
|            22 | Non Performing Of which:                                                                                                              |
|               | Unlikely to pay that are not past-due or past-due <= 90 days                                                                          |
|           222 | Non Performing Of which: Stage 2                                                                                                      |
|            23 | NON performing - of which Stage 3                                                                                                     |
|             3 | Performing but past due >30 days and <=90 days                                                                                        |
|             4 | Non Performing and Defaulted                                                                                                          |
|             5 | Loans and advances subject to impairment                                                                                              |

## dim_exposure_type: Exposure Type (e.g. Retail, Corporate)

> *Table not found in database.*

## dim_instrument_type: Instrument Type (e.g. Debt, Equity)

> *Table not found in database.*

## dim_portfolio: Portfolio (e.g. Trading, Banking Book)

|   portfolio | label                             |
|------------:|:----------------------------------|
|           0 | Total / No breakdown by portfolio |
|           1 | SA                                |
|           2 | IRB                               |
|           3 | F-IRB                             |
|           4 | A-IRB                             |
|           5 | IM                                |
|           6 | Fixed rate portfolio              |
|           7 | Floating rate portfolio           |

## dim_scenarios: Scenarios (for Stress Tests)

> *Table not found in database.*

## dim_country: Country Codes

|   country | label                                                                                | iso_code   |
|----------:|:-------------------------------------------------------------------------------------|:-----------|
|         0 | Total / No breakdown                                                                 | 00         |
|         1 | Austria                                                                              | AT         |
|         2 | Belgium                                                                              | BE         |
|         3 | Bulgaria                                                                             | BG         |
|         4 | Cyprus                                                                               | CY         |
|         5 | Czech Republic                                                                       | CZ         |
|         6 | Denmark                                                                              | DK         |
|         7 | Estonia                                                                              | EE         |
|         8 | Finland                                                                              | FI         |
|         9 | France                                                                               | FR         |
|        10 | Germany                                                                              | DE         |
|        11 | Greece                                                                               | GR         |
|        12 | Hungary                                                                              | HU         |
|        13 | Iceland                                                                              | IS         |
|        14 | Ireland                                                                              | IE         |
|        15 | Italy                                                                                | IT         |
|        16 | Latvia                                                                               | LV         |
|        17 | Liechtenstein                                                                        | LI         |
|        18 | Lithuania                                                                            | LT         |
|        19 | Luxembourg                                                                           | LU         |
|        20 | Malta                                                                                | MT         |
|        21 | Netherlands                                                                          | NL         |
|        22 | Norway                                                                               | NO         |
|        23 | Poland                                                                               | PL         |
|        24 | Portugal                                                                             | PT         |
|        25 | Romania                                                                              | RO         |
|        26 | Slovakia                                                                             | SK         |
|        27 | Slovenia                                                                             | SI         |
|        28 | Spain                                                                                | ES         |
|        29 | Sweden                                                                               | SE         |
|        30 | United Kingdom                                                                       | GB         |
|        31 | Brazil                                                                               | BR         |
|        32 | Chile                                                                                | CL         |
|        33 | China                                                                                | CN         |
|        34 | Croatia                                                                              | HR         |
|        35 | Hong Kong                                                                            | HK         |
|        36 | India                                                                                | IN         |
|        37 | Japan                                                                                | JP         |
|        38 | Mexico                                                                               | MX         |
|        39 | Peru                                                                                 | PE         |
|        40 | Russian Federation                                                                   | RU         |
|        41 | Switzerland                                                                          | CH         |
|        42 | Turkey                                                                               | TR         |
|        43 | United States                                                                        | US         |
|        44 | International organisations                                                          | IZ         |
|        50 | Afghanistan                                                                          | AF         |
|        51 | Albania                                                                              | AL         |
|        52 | Algeria                                                                              | DZ         |
|        53 | American Samoa                                                                       | AS         |
|        54 | Andorra                                                                              | AD         |
|        55 | Angola                                                                               | AO         |
|        56 | Anguilla                                                                             | AI         |
|        57 | Antigua and Barbuda                                                                  | AG         |
|        58 | Argentina                                                                            | AR         |
|        59 | Armenia                                                                              | AM         |
|        60 | Aruba                                                                                | AW         |
|        61 | Australia                                                                            | AU         |
|        62 | Azerbaijan                                                                           | AZ         |
|        63 | Bahamas                                                                              | BS         |
|        64 | Bahrain                                                                              | BH         |
|        65 | Bangladesh                                                                           | BD         |
|        66 | Barbados                                                                             | BB         |
|        67 | Belarus                                                                              | BY         |
|        68 | Belize                                                                               | BZ         |
|        69 | Benin                                                                                | BJ         |
|        70 | Bermuda                                                                              | BM         |
|        71 | Bhutan                                                                               | BT         |
|        72 | BOLIVIA, PLURINATIONAL STATE OF                                                      | BO         |
|        73 | BONAIRE, SINT EUSTATIUS AND SABA                                                     | BQ         |
|        74 | BOSNIA AND HERZEGOVINA                                                               | BA         |
|        75 | Botswana                                                                             | BW         |
|        76 | British Indian Ocean Territory                                                       | IO         |
|        77 | Brunei Darussalam                                                                    | BN         |
|        78 | Burkina Faso                                                                         | BF         |
|        79 | Burundi                                                                              | BI         |
|        80 | Cambodia                                                                             | KH         |
|        81 | Cameroon                                                                             | CM         |
|        82 | Canada                                                                               | CA         |
|        83 | Cape Verde                                                                           | CV         |
|        84 | Cayman Islands                                                                       | KY         |
|        85 | Central African Republic                                                             | CF         |
|        86 | Chad                                                                                 | TD         |
|        87 | Channel Islands                                                                      | CS         |
|        88 | Colombia                                                                             | CO         |
|        89 | Comoros                                                                              | KM         |
|        90 | CONGO, THE DEMOCRATIC REPUBLIC OF THE                                                | CD         |
|        91 | CONGO                                                                                | CG         |
|        92 | Cook Islands                                                                         | CK         |
|        93 | Costa Rica                                                                           | CR         |
|        94 | CÔTE D'IVOIRE                                                                        | CI         |
|        95 | Cuba                                                                                 | CU         |
|        96 | CURAÇAO                                                                              | CW         |
|        97 | Djibouti                                                                             | DJ         |
|        98 | Dominica                                                                             | DM         |
|        99 | Dominican Republic                                                                   | DO         |
|       100 | Ecuador                                                                              | EC         |
|       101 | Egypt                                                                                | EG         |
|       102 | El Salvador                                                                          | SV         |
|       103 | Equatorial Guinea                                                                    | GQ         |
|       104 | Eritrea                                                                              | ER         |
|       105 | Ethiopia                                                                             | ET         |
|       106 | Faroe Islands                                                                        | FO         |
|       107 | Falkland Islands (MALVINAS)                                                          | FK         |
|       108 | Fiji                                                                                 | FJ         |
|       109 | French Guiana                                                                        | GF         |
|       110 | French Polynesia                                                                     | PF         |
|       111 | NORTH MACEDONIA                                                                      | MK         |
|       112 | Gabon                                                                                | GA         |
|       113 | Gambia                                                                               | GM         |
|       114 | Georgia                                                                              | GE         |
|       115 | Ghana                                                                                | GH         |
|       116 | Gibraltar                                                                            | GI         |
|       117 | Greenland                                                                            | GL         |
|       118 | Grenada                                                                              | GD         |
|       119 | Guadeloupe                                                                           | GP         |
|       120 | Guam                                                                                 | GU         |
|       121 | Guatemala                                                                            | GT         |
|       122 | Guinea                                                                               | GN         |
|       123 | Guinea-Bissau                                                                        | GW         |
|       124 | Guyana                                                                               | GY         |
|       125 | Haiti                                                                                | HT         |
|       126 | Holy See (Vatican City State)                                                        | VA         |
|       127 | Honduras                                                                             | HN         |
|       128 | Indonesia                                                                            | ID         |
|       129 | IRAN, ISLAMIC REPUBLIC OF                                                            | IR         |
|       130 | Iraq                                                                                 | IQ         |
|       131 | Isle of Man                                                                          | IM         |
|       132 | Israel                                                                               | IL         |
|       133 | Jamaica                                                                              | JM         |
|       134 | Jordan                                                                               | JO         |
|       135 | Kazakhstan                                                                           | KZ         |
|       136 | Kenya                                                                                | KE         |
|       137 | Kiribati                                                                             | KI         |
|       138 | KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF                                               | KP         |
|       139 | KOREA, REPUBLIC OF                                                                   | KR         |
|       140 | Kosovo                                                                               | XK         |
|       141 | Kuwait                                                                               | KW         |
|       142 | Kyrgyzstan                                                                           | KG         |
|       143 | LAO PEOPLE'S DEMOCRATIC REPUBLIC                                                     | LA         |
|       144 | Lebanon                                                                              | LB         |
|       145 | Lesotho                                                                              | LS         |
|       146 | Liberia                                                                              | LR         |
|       147 | Libya                                                                                | LY         |
|       148 | Macao                                                                                | MO         |
|       149 | Madagascar                                                                           | MG         |
|       150 | Malawi                                                                               | MW         |
|       151 | Malaysia                                                                             | MY         |
|       152 | Maldives                                                                             | MV         |
|       153 | Mali                                                                                 | ML         |
|       154 | Marshall Islands                                                                     | MH         |
|       155 | Martinique                                                                           | MQ         |
|       156 | Mauritania                                                                           | MR         |
|       157 | Mauritius                                                                            | MU         |
|       158 | Mayotte                                                                              | YT         |
|       159 | MICRONESIA, FEDERATED STATES OF                                                      | FM         |
|       160 | MOLDOVA, REPUBLIC OF                                                                 | MD         |
|       161 | Monaco                                                                               | MC         |
|       162 | Mongolia                                                                             | MN         |
|       163 | Montenegro                                                                           | ME         |
|       164 | Montserrat                                                                           | MS         |
|       165 | Morocco                                                                              | MA         |
|       166 | Mozambique                                                                           | MZ         |
|       167 | Myanmar                                                                              | MM         |
|       168 | Namibia                                                                              |            |
|       169 | Nauru                                                                                | NR         |
|       170 | Nepal                                                                                | NP         |
|       171 | New Caledonia                                                                        | NC         |
|       172 | New Zealand                                                                          | NZ         |
|       173 | Nicaragua                                                                            | NI         |
|       174 | Niger                                                                                | NE         |
|       175 | Nigeria                                                                              | NG         |
|       176 | Niue                                                                                 | NU         |
|       177 | Northern Mariana Islands                                                             | MP         |
|       178 | Oman                                                                                 | OM         |
|       179 | Pakistan                                                                             | PK         |
|       180 | Palau                                                                                | PW         |
|       181 | Panama                                                                               | PA         |
|       182 | Papua New Guinea                                                                     | PG         |
|       183 | Paraguay                                                                             | PY         |
|       184 | Philippines                                                                          | PH         |
|       185 | Pitcairn                                                                             | PN         |
|       186 | Puerto Rico                                                                          | PR         |
|       187 | Qatar                                                                                | QA         |
|       188 | RÉUNION                                                                              | RE         |
|       189 | Rwanda                                                                               | RW         |
|       190 | SAINT HELENA, ASCENSION AND TRISTAN DA CUNHA                                         | SH         |
|       191 | Saint Kitts and Nevis                                                                | KN         |
|       192 | Saint Lucia                                                                          | LC         |
|       193 | SAINT MARTIN (FRENCH PART)                                                           | MF         |
|       194 | Saint Vincent and the Grenadines                                                     | VC         |
|       195 | SAINT PIERRE AND MIQUELON                                                            | PM         |
|       196 | Samoa                                                                                | WS         |
|       197 | San Marino                                                                           | SM         |
|       198 | Sao Tome and Principe                                                                | ST         |
|       199 | Saudi Arabia                                                                         | SA         |
|       200 | Senegal                                                                              | SN         |
|       201 | Serbia                                                                               | RS         |
|       202 | Seychelles                                                                           | SC         |
|       203 | Sierra Leone                                                                         | SL         |
|       204 | Singapore                                                                            | SG         |
|       205 | SINT MAARTEN (DUTCH PART)                                                            | SX         |
|       206 | Solomon Islands                                                                      | SB         |
|       207 | Somalia                                                                              | SO         |
|       208 | South Africa                                                                         | ZA         |
|       209 | South Sudan                                                                          | SS         |
|       210 | Sri Lanka                                                                            | LK         |
|       211 | Sudan                                                                                | SD         |
|       212 | Suriname                                                                             | SR         |
|       213 | SVALBARD AND JAN MAYEN                                                               | SJ         |
|       214 | Swaziland                                                                            | SZ         |
|       215 | SYRIAN ARAB REPUBLIC                                                                 | SY         |
|       216 | TAIWAN, PROVINCE OF CHINA                                                            | TW         |
|       217 | Tajikistan                                                                           | TJ         |
|       218 | TANZANIA, UNITED REPUBLIC OF                                                         | TZ         |
|       219 | Thailand                                                                             | TH         |
|       220 | Timor-Leste                                                                          | TL         |
|       221 | Togo                                                                                 | TG         |
|       222 | Tokelau                                                                              | TK         |
|       223 | Tonga                                                                                | TO         |
|       224 | Trinidad and Tobago                                                                  | TT         |
|       225 | Tunisia                                                                              | TN         |
|       226 | Turkmenistan                                                                         | TM         |
|       227 | Turks and Caicos Islands                                                             | TC         |
|       228 | Tuvalu                                                                               | TV         |
|       229 | Uganda                                                                               | UG         |
|       230 | Ukraine                                                                              | UA         |
|       231 | United Arab Emirates                                                                 | AE         |
|       232 | United States Minor Outlying Islands                                                 | UM         |
|       233 | Uruguay                                                                              | UY         |
|       234 | Uzbekistan                                                                           | UZ         |
|       235 | Vanuatu                                                                              | VU         |
|       236 | VENEZUELA, BOLIVARIAN REPUBLIC OF                                                    | VE         |
|       237 | VIET NAM                                                                             | VN         |
|       238 | WALLIS AND FUTUNA                                                                    | WF         |
|       239 | West Bank and Gaza                                                                   | WE         |
|       240 | Western Sahara                                                                       | EH         |
|       241 | Yemen                                                                                | YE         |
|       242 | Zambia                                                                               | ZM         |
|       243 | Zimbabwe                                                                             | ZW         |
|       244 | Other                                                                                | O1         |
|       245 | Other Central and eastern Europe countries non EEA                                   | O2         |
|       246 | Middle East                                                                          | O3         |
|       247 | Latin America and the Caribbean                                                      | O4         |
|       248 | Africa                                                                               | O5         |
|       249 | Other advanced economies non EEA                                                     | O6         |
|       250 | NORFOLK ISLAND                                                                       | NF         |
|       251 | PALESTINIAN TERRITORY, OCCUPIED                                                      | PS         |
|       252 | SAINT BARTHÉLEMY                                                                     | BL         |
|       253 | SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS                                         | GS         |
|       254 | VIRGIN ISLANDS, BRITISH                                                              | VG         |
|       255 | VIRGIN ISLANDS, U.S.                                                                 | VI         |
|       256 | ÅLAND ISLANDS                                                                        | AX         |
|       257 | ANTARCTICA                                                                           | AQ         |
|       258 | BOUVET ISLAND                                                                        | BV         |
|       259 | CHRISTMAS ISLAND                                                                     | CX         |
|       260 | COCOS (KEELING) ISLANDS                                                              | CC         |
|       261 | FRENCH SOUTHERN TERRITORIES                                                          | TF         |
|       262 | GUERNSEY                                                                             | GG         |
|       263 | HEARD ISLAND AND MCDONALD ISLANDS                                                    | HM         |
|       264 | JERSEY                                                                               | JE         |
|       701 | Banque Centrale des États de l’Afrique de l’Ouest (BCEAO)                            | _5O        |
|       702 | CASDB (Central African States’ Development Bank)                                     | _5P        |
|       703 | African Development Fund                                                             | _5Q        |
|       704 | Asian Development Fund                                                               | _5R        |
|       705 | Fonds spécial unifié de développement                                                | _5S        |
|       706 | CABEI (Central American Bank for Economic Integration)                               | _5T        |
|       707 | ADC (Andean Development Corporation)                                                 | _5U        |
|       708 | Other International Organisations (financial institutions)                           | _5V        |
|       709 | Banque des États de l’Afrique centrale (BEAC)                                        | _5W        |
|       710 | Communauté Économique et Monétaire de l’Afrique Centrale (CEMAC)                     | _5X        |
|       711 | Eastern Caribbean Currency Union (ECCU)                                              | _5Y        |
|       712 | Other International Financial Organisations n.i.e.                                   | _5Z        |
|       713 | Other International Organisations (non-financial institutions)                       | _6A        |
|       714 | NATO (North Atlantic Treaty Organisation)                                            | _6B        |
|       715 | Council of Europe                                                                    | _6C        |
|       716 | ICRC (International Committee of the Red Cross)                                      | _6D        |
|       717 | ESA (European Space Agency)                                                          | _6E        |
|       718 | EPO (European Patent Office)                                                         | _6F        |
|       719 | EUROCONTROL (European Organisation for the Safety of Air Navigation)                 | _6G        |
|       720 | EUTELSAT (European Telecommunications Satellite Organisation)                        | _6H        |
|       721 | West African Economic and Monetary Union (WAEMU)                                     | _6I        |
|       722 | INTELSAT (International Telecommunications Satellite Organisation)                   | _6J        |
|       723 | EBU/UER (European Broadcasting Union/Union européenne de radio-télévision)           | _6K        |
|       724 | EUMETSAT (European Organisation for the Exploitation of Meteorological Satellites)   | _6L        |
|       725 | ESO (European Southern Observatory)                                                  | _6M        |
|       726 | ECMWF (European Centre for Medium-Range Weather Forecasts)                           | _6N        |
|       727 | EMBL (European Molecular Biology Laboratory)                                         | _6O        |
|       728 | CERN (European Organisation for Nuclear Research)                                    | _6P        |
|       729 | IOM (International Organisation for Migration)                                       | _6Q        |
|       730 | Islamic Development Bank (IDB)                                                       | _6R        |
|       731 | Eurasian Development Bank (EDB)                                                      | _6S        |
|       732 | Paris Club Creditor Institutions                                                     | _6T        |
|       733 | Council of Europe Development Bank (CEB)                                             | _6U        |
|       734 | Other International Non-Financial Organisations n.i.e.                               | _6Z        |
|       735 | International Organisations excluding European Union Institutions                    | _7Z        |
|       736 | International Union of Credit and Investment Insurers                                | _8A        |
|       737 | Multilateral Lending Agencies                                                        | _9B        |
|       738 | International organisations (as pseudo geographic area)                              | _1A        |
|       739 | United Nations organisations                                                         | _1B        |
|       740 | IMF (International Monetary Fund)                                                    | _1C        |
|       741 | WTO (World Trade Organisation)                                                       | _1D        |
|       742 | IBRD (International Bank for Reconstruction and Development)                         | _1E        |
|       743 | IDA (International Development Association)                                          | _1F        |
|       744 | Other UN Organisations (includes 1H, 1J-1T)                                          | _1G        |
|       745 | UNESCO (United Nations Educational, Scientific and Cultural Organisation)            | _1H        |
|       746 | FAO (Food and Agriculture Organisation)                                              | _1J        |
|       747 | WHO (World Health Organisation)                                                      | _1K        |
|       748 | IFAD (International Fund for Agricultural Development)                               | _1L        |
|       749 | IFC (International Finance Corporation)                                              | _1M        |
|       750 | MIGA (Multilateral Investment Guarantee Agency)                                      | _1N        |
|       751 | UNICEF (United Nations Children’s Fund)                                              | _1O        |
|       752 | UNHCR (United Nations High Commissioner for Refugees)                                | _1P        |
|       753 | UNRWA (United Nations Relief and Works Agency for Palestine)                         | _1Q        |
|       754 | IAEA (International Atomic Energy Agency)                                            | _1R        |
|       755 | ILO (International Labour Organisation)                                              | _1S        |
|       756 | ITU (International Telecommunication Union)                                          | _1T        |
|       757 | Rest of UN Organisations n.i.e.                                                      | _1Z        |
|       758 | European Union Institutions, Organs and Organisms (excluding ECB)                    | _4A        |
|       759 | EMS (European Monetary System)                                                       | _4B        |
|       760 | EIB (European Investment Bank)                                                       | _4C        |
|       761 | EC (European Commission)                                                             | _4D        |
|       762 | EDF (European Development Fund)                                                      | _4E        |
|       763 | European Central Bank                                                                | _4F        |
|       764 | EIF (European Investment Fund)                                                       | _4G        |
|       765 | ECSC (European Coal and Steel Community)                                             | _4H        |
|       766 | Neighbourhood Investment Facility                                                    | _4I        |
|       767 | FEMIP (Facility for Euro-Mediterranean Investment and Partnership)                   | _4V        |
|       768 | Other EU Institutions, Organs and Organisms covered by the General budget            | _4J        |
|       769 | European Parliament                                                                  | _4K        |
|       770 | Council of the European Union                                                        | _4L        |
|       771 | Court of Justice                                                                     | _4M        |
|       772 | Court of Auditors                                                                    | _4N        |
|       773 | European Council                                                                     | _4O        |
|       774 | Economic and Social Committee                                                        | _4P        |
|       775 | Committee of the Regions                                                             | _4Q        |
|       776 | EU-Africa Infrastructure Trust Fund                                                  | _4R        |
|       777 | European Stability Mechanism (ESM)                                                   | _4S        |
|       778 | Joint Committee of the European Supervisory Authorities (ESAs)                       | _4T        |
|       779 | All the European Union Institutions financed via the EU Budget                       | _4W        |
|       780 | All the European Union Institutions not financed via the EU Budget                   | _4X        |
|       781 | All the European Union Institutions                                                  | _4Y        |
|       782 | Other small European Union Institutions (Ombudsman, Data Protection Supervisor etc.) | _4Z        |
|       783 | OECD (Organisation for Economic Co-operation and Development)                        | _5A        |
|       784 | BIS (Bank for International Settlements)                                             | _5B        |
|       785 | IADB (Inter-American Development Bank)                                               | _5C        |
|       786 | AfDB (African Development Bank)                                                      | _5D        |
|       787 | AsDB (Asian Development Bank)                                                        | _5E        |
|       788 | EBRD (European Bank for Reconstruction and Development)                              | _5F        |
|       789 | IIC (Inter-American Investment Corporation)                                          | _5G        |
|       790 | NIB (Nordic Investment Bank)                                                         | _5H        |
|       791 | Eastern Caribbean Central Bank (ECCB)                                                | _5I        |
|       792 | IBEC (International Bank for Economic Co-operation)                                  | _5J        |
|       793 | IIB (International Investment Bank)                                                  | _5K        |
|       794 | CDB (Caribbean Development Bank)                                                     | _5L        |
|       795 | AMF (Arab Monetary Fund)                                                             | _5M        |
|       796 | BADEA (Banque arabe pour le développement économique en Afrique)                     | _5N        |
|       901 | Countries not relevant for MKR purposes                                              | x5         |
|       902 | Not applicable/All geographical areas                                                | x0         |
|       903 | Other Countries                                                                      | x28        |

