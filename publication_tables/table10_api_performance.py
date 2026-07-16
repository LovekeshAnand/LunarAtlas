#!/usr/bin/env python3
"""
LunarAtlas — Reproduce API Performance Table
=============================================
Prints the API latency percentiles reported in Section 4.4 of the paper.
Benchmark environment: Intel Core i7-11850H / 16 GB RAM / NVMe SSD (Windows 11);
FastAPI under Python 3.11.9 venv; n=1,000 runs per config (20 warm-up discarded);
caching bypassed; Measurement ID 3.

Reads from Benchmarks/measurement1_latencies.csv when available to recompute
the co-located stats; otherwise prints the confirmed paper values.

Usage
-----
  python publication_tables/table10_api_performance.py
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))


def main():
    print("====================================================")
    print(" API PERFORMANCE — LATENCY PERCENTILES (Section 4.4)")
    print("====================================================")
    print()
    print(f"  {'Configuration':<35} {'Mean±Std':>18} {'Median':>10} {'P95':>12} {'P99':>12}")
    print("  " + "-" * 90)
    print(f"  {'Local + co-located DB':<35} {'22.34±17.05 ms':>18} {'17.13 ms':>10} {'73.03 ms':>12} {'88.59 ms':>12}")
    print(f"  {'Local + remote WAN DB':<35} {'300.53±97.14 ms':>18} {'296.27 ms':>10} {'471.72 ms':>12} {'673.52 ms':>12}")
    print(f"  {'Production + remote WAN DB':<35} {'1111.07±188.25 ms':>18} {'1056.37 ms':>10} {'1461.86 ms':>12} {'1650.45 ms':>12}")
    print()
    print("  DB index speedup (measurement_id idx vs seq scan) : ~133× (1.74 ms vs 230.35 ms)")
    print("  Payload size range                                 : 10–400 kB")
    print()

    # Optionally recompute co-located stats from stored CSV
    csv_path = root_dir / "Benchmarks" / "measurement1_latencies.csv"
    if csv_path.exists():
        try:
            import numpy as np
            import pandas as pd
            df = pd.read_csv(csv_path)
            lat_col = next((c for c in df.columns if "latency" in c.lower()), None)
            if lat_col:
                vals = df[lat_col].dropna().values
                print(f"[INFO] Recomputed from {csv_path.name} (n={len(vals)}):")
                print(f"  mean={vals.mean():.2f} ms  std={vals.std():.2f} ms  "
                      f"median={np.median(vals):.2f} ms  "
                      f"P95={np.percentile(vals, 95):.2f} ms  "
                      f"P99={np.percentile(vals, 99):.2f} ms")
        except Exception as e:
            print(f"[WARNING] Could not parse {csv_path.name}: {e}")

    print("\n--- LaTeX snippet (Table in paper) ---")
    print("Local + co-located DB      & 17.13~ms   & 73.03~ms   & 88.59~ms \\\\")
    print("Local + remote WAN DB      & 296.27~ms  & 471.72~ms  & 673.52~ms \\\\")
    print("Production + remote WAN DB & 1{,}056.37~ms & 1{,}461.86~ms & 1{,}650.45~ms \\\\")
    print("\\midrule")
    print("DB index speedup (vs.\\ seq.\\ scan) & \\multicolumn{3}{c}{$\\approx 133{\\times}$} \\\\")
    print("Payload size range & \\multicolumn{3}{c}{10--400~kB} \\\\")
    print("====================================================\n")


if __name__ == "__main__":
    main()
