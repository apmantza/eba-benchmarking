from blueprint_pipeline import BlueprintPipeline
import pandas as pd
import logging

p = BlueprintPipeline('data/raw/Pillar3reports/2025-06-30_Eurobank.pdf')
p.scan_index()
results = p.parse_template('KM1')
df = pd.DataFrame(results)
print(df[df['row_id'].isin(['1', '5', '14', '15', '20'])].to_string())
