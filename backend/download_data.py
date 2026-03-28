"""
Download Instacart dataset from Kaggle or direct source.

This script provides multiple download options:
1. Manual instructions for Kaggle download
2. Direct download from Instacart (if available)
"""

import os
import sys
from pathlib import Path
import urllib.request
import zipfile


DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

REQUIRED_FILES = [
    "orders.csv",
    "order_products__prior.csv",
    "order_products__train.csv",
    "products.csv",
    "aisles.csv",
    "departments.csv",
]


def check_existing_data() -> bool:
    """Check if all required CSV files exist."""
    missing = []
    for file in REQUIRED_FILES:
        if not (DATA_DIR / file).exists():
            missing.append(file)

    if missing:
        print(f"Missing files: {', '.join(missing)}")
        return False

    print("All required files are present!")
    return True


def print_manual_instructions():
    """Print manual download instructions."""
    print("\n" + "="*70)
    print("MANUAL DOWNLOAD INSTRUCTIONS")
    print("="*70)
    print("""
The Instacart dataset can be downloaded from Kaggle:

1. Go to: https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis

2. Click "Download" (you may need to create a free Kaggle account)

3. Extract the ZIP file

4. Copy these files to the backend/data/ directory:
   - orders.csv
   - order_products__prior.csv
   - order_products__train.csv
   - products.csv
   - aisles.csv
   - departments.csv

5. Run this script again to verify

ALTERNATIVE: Kaggle API (for advanced users)
-------------------------------------------
If you have kaggle CLI installed:

    pip install kaggle
    kaggle datasets download -d psparks/instacart-market-basket-analysis
    unzip instacart-market-basket-analysis.zip -d backend/data/

Dataset Stats:
- Size: ~3.4M orders, ~32M order items
- Total disk space: ~200MB compressed, ~800MB uncompressed
""")
    print("="*70 + "\n")


def main():
    print("Instacart Dataset Downloader")
    print("-" * 70)

    # Check if data already exists
    if check_existing_data():
        print("\nData is ready to use!")
        print(f"Location: {DATA_DIR.absolute()}")
        return

    print("\nData not found. Download required.")

    # Check for Kaggle API
    try:
        import kaggle
        print("\nKaggle API detected! Attempting automatic download...")

        try:
            kaggle.api.dataset_download_files(
                'psparks/instacart-market-basket-analysis',
                path=str(DATA_DIR),
                unzip=True
            )
            print("\nDownload complete!")

            if check_existing_data():
                print("Setup successful!")
            else:
                print("Some files are still missing. Please check manually.")

        except Exception as e:
            print(f"\nAutomatic download failed: {e}")
            print_manual_instructions()

    except ImportError:
        print("\nKaggle API not installed.")
        print_manual_instructions()


if __name__ == "__main__":
    main()
