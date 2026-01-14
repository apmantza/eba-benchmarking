import pdfplumber
import pandas as pd
import re

def clean_val(v):
    if v is None: return None
    v = str(v).replace(',', '').replace('%', '').strip()
    try:
        return float(v)
    except:
        return None

def test_nbg_km1():
    pdf = pdfplumber.open('data/raw/Pillar3reports/2025-06-30_NBG.pdf')
    p = pdf.pages[16] # Page 17
    table = p.extract_table()
    if not table:
        print("No table found")
        return
        
    for row in table:
        if row and row[0]:
            rid = str(row[0]).strip()
            label = str(row[1]).strip() if len(row) > 1 else ""
            val = row[2] if len(row) > 2 else None
            print(f"ID: {rid} | Label: {label[:30]} | Val: {val}")

if __name__ == "__main__":
    test_nbg_km1()
