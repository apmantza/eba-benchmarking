import pdfplumber
import pandas as pd

pdf = pdfplumber.open('data/raw/Pillar3reports/2025-06-30_Eurobank.pdf')
p = pdf.pages[19]
table = p.extract_table()
df = pd.DataFrame(table)
print(f"Table length: {len(table)}")
for i, row in enumerate(table):
    if row:
        print(f"{i:2d} | {row}")
