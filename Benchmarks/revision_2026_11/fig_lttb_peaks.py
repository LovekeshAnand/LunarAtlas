"""Figure 3 (regenerated): production LTTB with the detected peaks of Measurement ID 3 as preserved channels,
k = 1-4, calibrated range (1,684 channels). Point counts in the panel titles are the actual output sizes.

usage: fig_lttb_peaks.py <repo> <stage-2 output dir> <out_dir>
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

repo, proc, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(repo / "core" / "server"))
from app.core.downsampling import lttb_downsample  # noqa: E402

plt.rcParams.update({"font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9, "legend.fontsize": 8,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5})

d = pd.read_csv(next(proc.rglob("ch3_lib_002_20230825T104221_00_l1_cleaned.csv")))
g = d[d.Measurement_ID == 3].sort_values("Wavelength_nm")
wl_all, y_all = g.Wavelength_nm.to_numpy(), g.Cleaned_Intensity.to_numpy()
sig = np.std(y_all[(wl_all >= 560) & (wl_all <= 580)], ddof=0)
c = (wl_all >= 220) & (wl_all <= 800)
wl, y = wl_all[c], y_all[c]
pk = find_peaks(y, prominence=3 * sig, distance=5)[0]
data = np.column_stack([wl, y, y])

fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.6), sharey=True)
for k, ax in zip((1, 2, 3, 4), axes.ravel()):
    res = lttb_downsample(data, zoom_level=k, lambda_min=wl[0], lambda_max=wl[-1], target_wavelengths=list(wl[pk]))
    o = np.array([[p["wavelength_nm"], p["intensity"]] for p in res["data"]])
    budget = min(2094, int(2094 * 2 ** -k))
    ax.plot(wl, y, color="#cbd5e1", lw=0.5, label="Full resolution")
    ax.plot(o[:, 0], o[:, 1], color="#1d4ed8", lw=0.6, marker=".", ms=2, label="Downsampled")
    ax.plot(wl[pk], y[pk], "x", color="#dc2626", ms=4, mew=1.2, label=f"Preserved peaks ({len(pk)})")
    ax.set_title(f"({'abcd'[k-1]}) $k={k}$\nLTTB budget {budget}; output {len(o)} points "
                 f"({100 * len(o) / len(wl):.1f}%)", loc="left", fontsize=8)
    ax.set_xlim(220, 800)
    if k in (3, 4): ax.set_xlabel("Wavelength (nm)")
    if k in (1, 3): ax.set_ylabel("Cleaned (a.u.)")
fig.tight_layout(rect=(0, 0.05, 1, 1))
h, l = axes[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=8)
out.mkdir(parents=True, exist_ok=True)
for ext in ("png", "pdf"):
    fig.savefig(out / f"fig_lttb_peaks.{ext}", dpi=300, bbox_inches="tight", facecolor="white",
                metadata={"CreationDate": None} if ext == "pdf" else None)
print("saved; peaks:", len(pk))
