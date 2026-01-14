import pandas as pd
df = pd.read_excel('data/raw/Pillar3reports/2025-09-30_Piraeus.xlsx', sheet_name='EU KM1', header=None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
print(df.iloc[5:45, :6].to_string())
