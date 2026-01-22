import sys
import os
import time

# Add the 'src' directory to sys.path to allow importing the 'eba_benchmarking' package
# src/eba_benchmarking/ingestion/pipeline.py -> src
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Import sub-modules from the consolidated structure
import eba_benchmarking.ingestion.db_init as db_init
import eba_benchmarking.ingestion.processors.gen_com_names as gen_com_names
import eba_benchmarking.ingestion.parsers.tr_cre as tr_cre
import eba_benchmarking.ingestion.parsers.tr_oth as tr_oth
import eba_benchmarking.ingestion.parsers.tr_rest as tr_rest
import eba_benchmarking.ingestion.processors.classify_bm as classify_bm
import eba_benchmarking.ingestion.processors.classify_size as classify_size
import eba_benchmarking.ingestion.fetchers.ecb_markets as ecb_markets
import eba_benchmarking.ingestion.fetchers.base_rates as base_rates
import eba_benchmarking.ingestion.fetchers.lending_spreads as lending_spreads
import eba_benchmarking.ingestion.fetchers.ecb_stats as ecb_stats
import eba_benchmarking.ingestion.fetchers.macro as macro
import eba_benchmarking.ingestion.fetchers.bog as bog
import eba_benchmarking.ingestion.parsers.kri as kri_parser
import eba_benchmarking.ingestion.parsers.map_kris as map_kris
import eba_benchmarking.ingestion.processors.cleanup_db as cleanup_db

# Import Pillar 3 parser
try:
    from eba_benchmarking.ingestion.parsers.unified import run_pillar3_parser
    PILLAR3_AVAILABLE = True
except ImportError:
    PILLAR3_AVAILABLE = False
    run_pillar3_parser = None

def run_pipeline():
    print("==========================================")
    print("🚀 STARTING EBA BENCHMARKING DATA PIPELINE")
    print("==========================================\n")
    start_time = time.time()

    steps = [
        ("Initializing Database & Metadata", db_init.main),
        ("Generating Commercial Names", gen_com_names.main),
        ("Parsing Credit Risk Data (CRE)", tr_cre.main),
        ("Parsing Other Financial Data (OTH)", tr_oth.main),
        ("Parsing Market Risk & Sovereign Data", tr_rest.main),
        ("Classifying Business Models", classify_bm.main),
        ("Classifying Bank Size", classify_size.main),
        ("Fetching ECB Market Rates", ecb_markets.main),
        ("Fetching ECB Base Rates", base_rates.main),
        ("Fetching Lending Spreads", lending_spreads.main),
        ("Fetching ECB Statistics (CET1/NPL)", ecb_stats.main),
        ("Fetching Macroeconomic Data (WB/Eurostat)", macro.main),
        ("Fetching BoG Data (Direct)", bog.main),
        ("Parsing EBA Country KRIs (Annex)", kri_parser.main),
        ("Mapping KRIs to Dictionary", map_kris.main),
        ("Cleaning and Normalizing Database", cleanup_db.main),
    ]
    
    # Add Pillar 3 parsing if available
    if PILLAR3_AVAILABLE:
        steps.append(("Parsing Pillar 3 Reports (PDFs & Excel)", run_pillar3_parser))

    for title, func in steps:
        print(f"\n--- [STEP] {title} ---")
        try:
            step_start = time.time()
            func()
            print(f"✅ Completed in {time.time() - step_start:.2f}s")
        except Exception as e:
            print(f"❌ FAILED: {e}")

    print("\n==========================================")
    print(f"🏁 PIPELINE COMPLETED in {time.time() - start_time:.2f}s")
    print("==========================================")

if __name__ == "__main__":
    run_pipeline()
