import pdfplumber
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ocr_utils import extract_text_from_image, is_ocr_available
from parse_pillar3_enhanced import reconstruct_page_text

PDF = 'data/raw/Pillar3reports/2025-06-30_Alpha_Bank.pdf'

def test_ocr(page_num):
    print(f"\n--- TESTING PAGE {page_num} ---")
    with pdfplumber.open(PDF) as pdf:
        page = pdf.pages[page_num-1]
        
        recon = reconstruct_page_text(page)
        print(f"Reconstructed Text Length: {len(recon)}")
        print("First 200 chars recon:")
        print(recon[:200])
        
        img = page.to_image(resolution=300)
        text = extract_text_from_image(img)
        print(f"OCR Text Length: {len(text)}")
        if len(text) > 0:
            print("First 200 chars OCR:")
            print(text[:200])

if __name__ == "__main__":
    print(f"OCR Available: {is_ocr_available()}")
    test_ocr(2)  # Index
    test_ocr(14) # KM1 often around here
    test_ocr(15)
