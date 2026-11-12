"""Point 3: clamped-fraction statistics over all paired spectra (stage-2 output), both definitions:
old (v1.0.1, submitted paper): share of channels == 0 after clamping;
new (current code/DB):          share of channels with a negative residual before clamping.
Also recomputes Table 4 (worked example, 2,094 channels).

usage: clip_stats.py <stage-2 output dir>
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

root = Path(sys.argv[1])
rows = []
for p in root.rglob("*_instrument_params.csv"):
    par = pd.read_csv(p)
    cl = pd.read_csv(str(p).replace("_instrument_params.csv", "_cleaned.csv"))
    for _, r in par.iterrows():
        s = cl[cl.Measurement_ID == r.Measurement_ID]
        cal = s[(s.Wavelength_nm >= 220) & (s.Wavelength_nm <= 800)]
        rows.append(dict(file=p.name[:-len("_instrument_params.csv")], mid=r.Measurement_ID,
                         clip_new=r.Clip_Fraction, clip_old=(s.Cleaned_Intensity == 0).mean(),
                         mean_all=s.Cleaned_Intensity.mean(), std_all=s.Cleaned_Intensity.std(ddof=0),
                         max_all=s.Cleaned_Intensity.max(), mean_cal=cal.Cleaned_Intensity.mean()))
d = pd.DataFrame(rows)
print("spectra:", len(d))
for col in ("clip_new", "clip_old"):
    print(f"{col}: " + ", ".join(f">{t}: {(d[col] > t).sum()} ({(d[col] > t).mean()*100:.1f}%)" for t in (0.25, 0.5, 0.75)))
    print("  histogram (0-1, 10 bins):", np.histogram(d[col], bins=10, range=(0, 1))[0].tolist())
print("median clip_new:", round(d.clip_new.median(), 4))
for lo, hi in ((0, .25), (.25, .5), (.5, .75), (.75, 1.01)):
    g = d[(d.clip_new >= lo) & (d.clip_new < hi)]
    print(f"clip_new [{lo},{hi}): n={len(g)}  median mean intensity 220-800 nm = {g.mean_cal.median():.1f}")
print("Spearman(clip_new, mean intensity 220-800 nm):", round(d.clip_new.corr(d.mean_cal, method="spearman"), 3))
w = d[d.file == "ch3_lib_002_20230825T104221_00_l1"].sort_values("mid")
w = w.assign(clip_old=w.clip_old * 100, clip_new=w.clip_new * 100)
print("\nTable 4 (2,094 channels):\n", w[["mid", "mean_all", "std_all", "max_all", "clip_old", "clip_new"]].round(1).to_string(index=False))
