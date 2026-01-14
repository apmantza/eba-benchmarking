import pandas as pd
xl = pd.ExcelFile('data/raw/Pillar3reports/2025-06-30_Bank_of_Cyprus.xlsx')
for s in xl.sheet_names:
    print(f"'{s}'")
