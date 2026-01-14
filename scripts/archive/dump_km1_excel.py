import pandas as pd
df = pd.read_excel('data/templates/1 Disclosure of overview of risk management, key prudential metrics.xlsx', sheet_name='EU KM1')
for i, row in df.iterrows():
    print(f"{i}: {row.iloc[1]} | {row.iloc[2]}")
