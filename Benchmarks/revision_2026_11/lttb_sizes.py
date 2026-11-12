"""Point-count check for the LTTB+Peaks figure/table (external review item 1): output size of the production
lttb_downsample with and without the detected peaks as targets, IDs 1/3/4, calibrated (1,684 ch.) and full
(2,094 ch.) range, k = 1..5.

usage: lttb_sizes.py <repo> <stage-2 output dir>
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

repo, proc = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo / "core" / "server"))
from app.core.downsampling import lttb_downsample  # noqa: E402

d = pd.read_csv(next(proc.rglob("ch3_lib_002_20230825T104221_00_l1_cleaned.csv")))
for mid in (1, 3, 4):
    g = d[d.Measurement_ID == mid].sort_values("Wavelength_nm")
    wl_all, y_all = g.Wavelength_nm.to_numpy(), g.Cleaned_Intensity.to_numpy()
    n = (wl_all >= 560) & (wl_all <= 580)
    sig = np.std(y_all[n], ddof=0)
    c = (wl_all >= 220) & (wl_all <= 800)
    pk = np.flatnonzero(c)[find_peaks(y_all[c], prominence=3 * sig, distance=5)[0]]
    for rng, m in (("calibrated", c), ("full", np.ones_like(c))):
        wl, y = wl_all[m], y_all[m]
        data = np.column_stack([wl, y, y])
        row = []
        for k in (1, 2, 3, 4, 5):
            a = len(lttb_downsample(data, zoom_level=k, lambda_min=wl[0], lambda_max=wl[-1])["data"])
            b = len(lttb_downsample(data, zoom_level=k, lambda_min=wl[0], lambda_max=wl[-1],
                                    target_wavelengths=list(wl_all[pk]))["data"])
            row.append(f"k={k}: LTTB {a} ({100*a/len(wl):.1f}%) / +peaks {b} ({100*b/len(wl):.1f}%)")
        print(f"ID {mid} {rng} ({len(wl)} ch., {len(pk)} peaks): " + "; ".join(row))
