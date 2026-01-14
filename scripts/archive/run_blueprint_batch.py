import os
from blueprint_pipeline import BlueprintPipeline

pdf_dir = 'data/raw/Pillar3reports/'
pdfs = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

print(f"Starting Blueprint Pipeline for {len(pdfs)} files...")

for pdf in pdfs:
    try:
        p = BlueprintPipeline(pdf)
        p.run(save=True)
    except Exception as e:
        print(f"Error processing {pdf}: {e}")

print("Batch processing complete.")
