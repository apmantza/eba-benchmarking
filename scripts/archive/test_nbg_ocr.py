import os
import sys
import pytesseract
from PIL import Image
import pdfplumber

# Add current dir to path
sys.path.append(os.getcwd())
from scripts.parse_pillar3_enhanced import reconstruct_page_text

def test_page(pdf_path, page_num):
    print(f"\n--- TESTING {os.path.basename(pdf_path)} PAGE {page_num} ---")
    with pdfplumber.open(pdf_path) as pdf:
        if page_num > len(pdf.pages):
            print("Page out of range")
            return
        
        page = pdf.pages[page_num - 1]
        
        # 1. Reconstruct text
        recon = reconstruct_page_text(page)
        print(f"Reconstructed Text Length: {len(recon)}")
        print(f"First 500 chars recon:\n{recon[:500]}")
        
        # 2. OCR
        print("\n--- OCR EXTRACT ---")
        try:
            pil_img = page.to_image(resolution=300).original
            ocr_text = pytesseract.image_to_string(pil_img)
            print(f"OCR Text Length: {len(ocr_text)}")
            print(f"First 500 chars OCR:\n{ocr_text[:500]}")
        except Exception as e:
            print(f"OCR Failed: {e}")

if __name__ == "__main__":
    test_page('data/raw/Pillar3reports/2025-06-30_NBG.pdf', 17)
    test_page('data/raw/Pillar3reports/2025-06-30_NBG.pdf', 18)
