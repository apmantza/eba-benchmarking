"""
Script to refresh Yahoo Finance market data for all banks with tickers.
Run this script periodically to update market data.

Usage:
    python scripts/refresh_market_data.py          # Current snapshot only
    python scripts/refresh_market_data.py --history # Historical data only
    python scripts/refresh_market_data.py --all    # Both current and historical
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from eba_benchmarking.data.market import refresh_market_data, refresh_market_history

if __name__ == "__main__":
    print("=" * 60)
    print("Yahoo Finance Market Data Refresh")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--history':
            print("Mode: Historical data only\n")
            refresh_market_history()
        elif sys.argv[1] == '--all':
            print("Mode: Current + Historical\n")
            refresh_market_data()
            print("\n" + "=" * 60 + "\n")
            refresh_market_history()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage: python refresh_market_data.py [--history|--all]")
    else:
        print("Mode: Current snapshot only\n")
        refresh_market_data()
