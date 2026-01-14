"""Comprehensive template scanner for all Pillar 3 templates."""
import pdfplumber
import re
from collections import defaultdict

pdf_path = 'data/raw/Pillar3reports/2025-06-30_NBG.pdf'

# Extended template patterns - includes IRRBB, ESG, etc.
template_patterns = [
    r'EU\s*([A-Z]{2,5}\d+[a-z]?)',
    r'Template\s+([A-Z]{2,5}\d+[a-z]?)',
    r'\b([A-Z]{2,5}\d+[a-z]?)\s*[–:-]',
    r'Table\s+\d+[:\s.]*(?:EU\s+)?([A-Z]{2,5}\d+[a-z]?)',
    r'(?:EU\s+)?([A-Z]{2,5}\d+[a-z]?)\s*–\s*',
    r'IRRBB\d+[a-z]?',  # Direct IRRBB
]

KNOWN_PREFIXES = ['KM', 'CC', 'OV', 'LR', 'LIQ', 'CR', 'CCR', 'CQ', 'MR', 'SEC', 'IRRBB', 'ESG', 'CMS', 'SSP', 'AE', 'OF', 'OR']
currently_parsed = ['KM1', 'KM2', 'CC1', 'CC2', 'OV1', 'LR1', 'LR2', 'LR3', 'LIQ1', 'LIQ2', 'CR1', 'CR3', 'CCR1']

templates_found = defaultdict(list)

print("Scanning PDF...")
with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        page_num = i + 1
        text = page.extract_text() or ""
        
        for pattern in template_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                code = match.upper().strip() if isinstance(match, str) else match
                if any(code.startswith(prefix) for prefix in KNOWN_PREFIXES):
                    if len(code) >= 2 and len(code) <= 8:
                        if page_num not in templates_found[code]:
                            templates_found[code].append(page_num)

sorted_templates = sorted(templates_found.items())

print(f"\nTotal templates found: {len(sorted_templates)}")
print(f"Currently parsed: {len(currently_parsed)}")

parsed = [code for code, _ in sorted_templates if code in currently_parsed]
gap = [code for code, _ in sorted_templates if code not in currently_parsed]

print(f"\nPARSED ({len(parsed)}): {', '.join(parsed)}")
print(f"\nGAP ({len(gap)}): {', '.join(gap)}")

# Look specifically for IRRBB
print("\n--- Searching for IRRBB ---")
with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages[:70]):
        text = page.extract_text() or ""
        if 'IRRBB' in text.upper():
            print(f"Page {i+1}: IRRBB found")
            lines = [l for l in text.split('\n') if 'IRRBB' in l.upper()][:3]
            for l in lines:
                print(f"  -> {l[:80]}")
