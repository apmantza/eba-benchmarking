import pdfplumber
import sys
import os

pdf_path = 'data/raw/Pillar3reports/2025-06-30_Eurobank.pdf'
with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text and 'EU KM1' in text:
            print(f"Found EU KM1 on Page {i+1}")
            # print(text)
            # break
