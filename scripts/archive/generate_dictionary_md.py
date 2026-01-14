import sqlite3
import pandas as pd

DB_PATH = 'eba_data.db'
MD_FILE = 'DICTIONARY_PILLAR3.md'

def generate_md():
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT template_code, row_id, p3_label, eba_item_id, category 
    FROM pillar3_dictionary 
    ORDER BY template_code, CAST(row_id AS INTEGER)
    """
    df = pd.read_sql(query, conn)
    
    with open(MD_FILE, 'w', encoding='utf-8') as f:
        f.write("# Pillar 3 Extraction Dictionary\n\n")
        f.write("This document lists all the metrics detected and extracted from the Pillar 3 PDF reports.\n\n")
        f.write(f"**Total Items:** {len(df)}\n")
        # f.write(f"**Mapped to EBA:** {len(df[df['eba_item_id'].notnull()])}\n\n")
        
        f.write("| Template | Row ID | Label | EBA Item ID | Category |\n")
        f.write("|---|---|---|---|---|\n")
        
        for _, row in df.iterrows():
            eba_id = row['eba_item_id'] if row['eba_item_id'] else "-(Unmapped)-"
            cat = row['category'] if row['category'] else ""
            # Escape pipes
            label = str(row['p3_label']).replace('|', '/')
            
            f.write(f"| {row['template_code']} | {row['row_id']} | {label} | {eba_id} | {cat} |\n")
            
    print(f"Generated {MD_FILE} with {len(df)} entries.")
    conn.close()

if __name__ == "__main__":
    generate_md()
