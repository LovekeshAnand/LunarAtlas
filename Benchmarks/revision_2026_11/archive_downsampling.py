"""Archive-wide downsampling check (port of the co-author's archive_wide_spectral.py to the current repository):
all 613 cleaned spectra, production lttb_downsample, k = 1..5, calibrated range 220-800 nm, peaks as in the paper.
Reports peak retention for LTTB and LTTB+Peaks and the RMSE of each against the full spectrum (linear interpolant).
usage: python -P archive_downsampling.py <stage-2 calibrated dir> <out.csv>
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.signal import find_peaks
sys.path.insert(0, "core/server")
from app.core.downsampling import lttb_downsample  # noqa: E402

def rmse(wl, y, pts):
    w = np.array([p["wavelength_nm"] for p in pts]); v = np.array([p["intensity"] for p in pts]); o = np.argsort(w)
    return float(np.sqrt(np.mean((np.interp(wl, w[o], v[o]) - y) ** 2)))

rows = []
for f in sorted(Path(sys.argv[1]).rglob("*_cleaned.csv")):
    df = pd.read_csv(f, usecols=["Measurement_ID", "Wavelength_nm", "Cleaned_Intensity"])
    for mid, g in df.groupby("Measurement_ID"):
        g = g.sort_values("Wavelength_nm")
        wl, y = g.Wavelength_nm.to_numpy(), g.Cleaned_Intensity.to_numpy()
        c = (wl >= 220) & (wl <= 800); wl, y = wl[c], y[c]
        pk = wl[find_peaks(y, prominence=3 * np.std(y[(wl >= 560) & (wl <= 580)]), distance=5)[0]]
        data = np.column_stack([wl, y, y])
        for k in range(1, 6):
            a = lttb_downsample(data, zoom_level=k, lambda_min=wl[0], lambda_max=wl[-1])["data"]
            b = lttb_downsample(data, zoom_level=k, lambda_min=wl[0], lambda_max=wl[-1], target_wavelengths=list(pk))["data"]
            ka = np.isin(pk, [p["wavelength_nm"] for p in a]).sum(); kb = np.isin(pk, [p["wavelength_nm"] for p in b]).sum()
            rows.append(dict(product=f.stem, mid=mid, k=k, n_peaks=len(pk), n_lttb=len(a), n_lttb_peaks=len(b),
                             ret_lttb=ka / len(pk) if len(pk) else np.nan, ret_lttb_peaks=kb / len(pk) if len(pk) else np.nan,
                             rmse_lttb=rmse(wl, y, a), rmse_lttb_peaks=rmse(wl, y, b)))
D = pd.DataFrame(rows); D.to_csv(sys.argv[2], index=False)
D["worse"] = D.rmse_lttb_peaks > D.rmse_lttb + 1e-9
D["d_rmse"] = D.rmse_lttb_peaks - D.rmse_lttb
S = D.groupby("k").agg(spectra=("mid", "size"), med_ret_lttb=("ret_lttb", "median"), min_ret_lttb_peaks=("ret_lttb_peaks", "min"),
                       pct_rmse_worse=("worse", "mean"), med_d_rmse=("d_rmse", "median"),
                       med_pct_points=("n_lttb", lambda s: 100 * s.median() / 1684))
S["med_ret_lttb"] *= 100; S["pct_rmse_worse"] *= 100
print(S.round(2).to_string())
