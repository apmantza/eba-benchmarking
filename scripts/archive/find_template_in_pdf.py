import sys
import pdfplumber

def find_text(pdf_path, text):
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            content = page.extract_text()
            if content and text in content:
                print(f"Found '{text}' on Page {i+1}")
                # Print context
                idx = content.find(text)
                print(content[idx:idx+100].replace('\n', ' '))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <pdf> <text>")
    else:
        find_text(sys.argv[1], sys.argv[2])
