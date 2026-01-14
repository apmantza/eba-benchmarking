import re
import sqlite3

def clean_number(s):
    try:
        s = s.replace(',', '').replace('%', '').strip()
        if '(' in s and ')' in s:
            s = '-' + s.replace('(', '').replace(')', '')
        return float(s)
    except:
        return None

def test():
    label = "Common Equity Tier 1 ratio (%)"
    line = "CommonEquityTier1ratio(%) 18.93% 18.48% 18.68% 18.25% 18.25% 18.25% 18.25% 18.25%5"
    
    clean_label_chars = "".join(label.split())
    parts = [re.escape(c) for c in clean_label_chars]
    label_regex = r"[\s.]*".join(parts)
    label_regex = label_regex.replace("1", "[1I]")
    
    print(f"Regex: {label_regex}")
    match = re.search(label_regex, line, re.I)
    print(f"Match: {match}")
    
    if match:
        data_part = line[match.end():]
        print(f"Data part: {data_part}")
        numbers = re.findall(r'(?:-?\d[\d,.]*|\(\d[\d,.]*\))', data_part)
        print(f"Numbers: {numbers}")

if __name__ == "__main__":
    test()
