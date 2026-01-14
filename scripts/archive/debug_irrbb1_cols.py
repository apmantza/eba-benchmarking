import pdfplumber
import re
import sys
import os

pdf_path = 'data/raw/Pillar3reports/2025-06-30_NBG.pdf'
page_num = 0 # Scan all

def debug_irrbb1_columns():
    with pdfplumber.open(pdf_path) as pdf:
        # Piraeus index might be off by 1 in pdfplumber (0-based) vs logs (1-based)?
        # Logs said "Found IRRBB1 -> Page 141". Usually log uses 1-based page number.
        # But pdf.pages is 0-based.
        # Let's try page index 140 and 141.
        
        for p_idx in range(len(pdf.pages)):
            text = pdf.pages[p_idx].extract_text()
            if "IRRBB1" in text or "Interest rate risks" in text:
                print(f"--- Found IRRBB1 Context on Page Index {p_idx} ---")
                lines = text.split('\n')
                for line in lines:
                    if "Parallel up" in line or "Parallel down" in line:
                        print(f"Line: {line}")
                        nums = re.findall(r'(?:-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?)', line)
                        # Filter likely page numbers or small ints
                        clean_nums = [n for n in nums if len(n) > 2 or '.' in n]
                        print(f"  Numbers found: {clean_nums}")

if __name__ == "__main__":
    debug_irrbb1_columns()
