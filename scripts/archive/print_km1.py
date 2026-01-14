from blueprint_pipeline import BlueprintPipeline
import pandas as pd

p = BlueprintPipeline('data/raw/Pillar3reports/2025-06-30_NBG.pdf')
results = p.run()
df = pd.DataFrame([r for r in results if r['template_code'] == 'KM1'])
df.to_csv('output/km1_res.csv', index=False)
print("Saved to output/km1_res.csv")
