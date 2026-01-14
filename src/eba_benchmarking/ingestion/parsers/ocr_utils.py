import sys
import os

try:
    import pytesseract
    # Check if tesseract binary is available in PATH
    try:
        pytesseract.get_tesseract_version()
        TESSERACT_AVAILABLE = True
    except pytesseract.TesseractNotFoundError:
        # Try common Windows paths
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\R3LiC\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
        ]
        found = False
        for path in common_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                TESSERACT_AVAILABLE = True
                found = True
                break
        if not found:
            TESSERACT_AVAILABLE = False
            
except ImportError:
    TESSERACT_AVAILABLE = False

def extract_text_from_image(page_image):
    """
    Extract text from a pdfplumber PageImage using Tesseract OCR.
    """
    if not TESSERACT_AVAILABLE:
        return ""
    
    try:
        # Convert to PIL Image
        pil_image = page_image.original
        # Perform OCR
        text = pytesseract.image_to_string(pil_image)
        return text
    except Exception as e:
        print(f"OCR Failed: {e}")
        return ""

def is_ocr_available():
    return TESSERACT_AVAILABLE
