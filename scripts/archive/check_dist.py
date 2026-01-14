import pdfplumber

pdf_path = 'data/raw/Pillar3reports/2025-06-30_Eurobank.pdf'
with pdfplumber.open(pdf_path) as pdf:
    p = pdf.pages[21]
    words = p.extract_words()
    seven = [w for w in words if w['text'] == '7' and w['top'] > 300][0]
    next_word = [w for w in words if w['text'] == ',932'][0]
    print(f"7 at x1={seven['x1']}, next at x0={next_word['x0']}, dist={next_word['x0'] - seven['x1']}")
