import pdfplumber
import sys
import os

sys.path.insert(0, 'scripts')

from parse_pillar3_enhanced import reconstruct_page_text

PDF = 'data/raw/Pillar3reports/2025-06-30_Alpha_Bank.pdf'

def test_pages(p_range):
    with pdfplumber.open(PDF) as pdf:
        for p_idx in p_range:
            print(f"\n--- PAGE {p_idx+1} ---")
            page = pdf.pages[p_idx]
            recon = reconstruct_page_text(page)
            # Search for row ids
            for line in recon.split('\n'):
                # Look for lines starting with or containing a number and some key metric text
                if any(k in line.lower() for k in ['capital', 'ratio', 'weighted', 'hqla', 'nsfr', 'stable funding']):
                    print(line)

if __name__ == "__main__":
    test_pages([26, 27, 28, 29, 30])
