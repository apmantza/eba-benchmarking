import sqlite3
import pandas as pd
import re
from eba_benchmarking.config import DB_NAME

def clean_bank_name(full_name):
    """
    Standardizes bank names into clean commercial names.
    Removes legal suffixes, generic banking terms, and domestic abbreviations.
    """
    if not full_name: return "Unknown"
    
    # 1. Standardize Case & Basic Cleaning
    name = str(full_name).strip()
    
    # 2. Remove everything after a hyphen (inclusive) as requested
    if '-' in name:
        name = name.split('-')[0].strip()

    # 3. Sequential regex patterns for cleaning
    patterns = [
        # Legal Forms (International & Domestic)
        r'\bAG\b', r'\bS\.?A\.?\b', r'\bS\.?p\.?A\.?\b', r'\bPlc\b', r'\bN\.?V\.?\b', 
        r'\bLtd\b', r'\bInc\b', r'\bCorp\b', r'\beGen\b', r'\beG\b', r'\bEG\b', 
        r'\bS\.?A\.?R\.?L\.?\b', r'\bR\.?L\.?\b', r'\bPublic Limited Company\b',
        r'\bSE\b', r'\bKGaA\b', r'\bCo\b', r'\b& Co\b', r'\bA/S\b',
        r'\bSOCIETA\'? PER AZIONI\b', r'\bS\.?P\.?A\.?\b',
        
        # Generic Banking Terms (often clatter)
        r'\bGroup\b', r'\bHoldings\b', r'\bFinancial\b', r'\bServices\b', 
        r'\bInternational\b', r'\bInvestment\b', r'\bAsset Management\b',
        r'\bGlobal Markets\b', r'\bBausparkasse\b', r'\bGenossenschaftsbank\b',
        r'\bZentral-Genossenschaftsbank\b', r'\bVerbund\b', r'\bHolding\b', r'\bBank\b$',
        
        # Specific Domestic Abbreviations (like Austrian 'VB' for Volksbank)
        r'\bVB\b', r'\bRLB\b', r'\bRB\b',
        
        # trailing punctuation/spaces
        r'[,.\-\s]+$'
    ]
    
    # Apply patterns iteratively
    for _ in range(3):
        for pattern in patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE).strip()
            # Remove double spaces
            name = re.sub(r'\s+', ' ', name)
            # Remove leading/trailing commas or dashes
            name = name.strip(' ,-')

    # 4. Final special character removal (except spaces)
    name = re.sub(r'[.&]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()

    # 5. Special Overrides / Hardcoded Fixes
    overrides = {
        'Volksbank Wien': 'Volksbank Wien',
        'Alpha Services': 'Alpha Bank',
        'National Bank of Greece': 'National Bank of Greece',
        'Eurobank Ergasias': 'Eurobank',
        'Piraeus Financial': 'Piraeus',
        'THE BANK OF NEW YORK MELLON': 'BNY Mellon',
        'Investeringsmaatschappij Argenta': 'Argenta',
        'KBC Groupe': 'KBC',
        'Bayerische Landesbank': 'BayernLB',
        'COMMERZBANK': 'Commerzbank',
        'DEUTSCHE BANK': 'Deutsche Bank',
        'DekaBank Deutsche Girozentrale': 'DekaBank',
        'Raiffeisenbankengruppe OÖ': 'Raiffeisen OÖ'
    }
    
    for key, val in overrides.items():
        if key.lower() in name.lower():
            return val
            
    return name

def generate_short_name(commercial_name):
    """
    Generates initials for multi-word names.
    e.g., "National Bank Greece" -> "NBG"
    """
    if not commercial_name: return None
    # Ignore stop words for initials
    stop_words = ['of', 'the', 'for', 'in', 'on', 'at', 'and']
    words = [w for w in str(commercial_name).split() if w.lower() not in stop_words]
    
    if len(words) > 1:
        return "".join([w[0].upper() for w in words if w])
    return None

def main():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("--- 1. Updating Institutions with Clean Commercial and Short Names ---")

    # Get data
    df = pd.read_sql("SELECT lei, name FROM institutions", conn)
    
    if not df.empty:
        df['commercial_name'] = df['name'].apply(clean_bank_name)
        df['short_name'] = df['commercial_name'].apply(generate_short_name)
        
        # Update Database
        data = df[['commercial_name', 'short_name', 'lei']].values.tolist()
        cursor.executemany("UPDATE institutions SET commercial_name = ?, short_name = ? WHERE lei = ?", data)
        conn.commit()
        
        print(f"  > Successfully updated {len(df)} names.")
        # Show a few examples
        print("  > Samples:")
        for _, row in df.head(10).iterrows():
            print(f"    '{row['name']}' -> '{row['commercial_name']}' (Short: {row['short_name']})")

    conn.close()

if __name__ == "__main__":
    main()