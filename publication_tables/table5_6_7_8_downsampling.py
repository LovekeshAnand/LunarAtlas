#!/usr/bin/env python3
"""
DEPRECATED — replaced by downsampling_comparison.py
====================================================
This script previously required a non-existent figures/evaluate_downsampling.py
and figures/downsampling_eval_results.json.

It has been superseded by:
  publication_tables/downsampling_comparison.py

which is fully self-contained (no external figures/ directory needed) and
reproduces Table 5 from the SoftwareX paper directly from the cleaned CSV.

Usage
-----
  python publication_tables/downsampling_comparison.py
"""

import sys
import subprocess
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent


def main():
    replacement = root_dir / "publication_tables" / "downsampling_comparison.py"
    print("[INFO] This script is deprecated. Forwarding to downsampling_comparison.py ...")
    try:
        subprocess.run([sys.executable, str(replacement)], check=True)
    except Exception as e:
        print(f"[ERROR] {e}")
        print(f"  Please run directly: python {replacement.relative_to(root_dir)}")


if __name__ == "__main__":
    main()
