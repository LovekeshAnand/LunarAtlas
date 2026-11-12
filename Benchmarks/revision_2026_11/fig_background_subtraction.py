"""Point 11 figure: raw plasma acquisition, paired background, and cleaned spectrum (Measurement ID 3,
worked example). Raw inputs from the PRADAN parent table (pairing = most recent preceding background row);
cleaned spectrum from the stage-2 output, checked to equal max(0, P - B).

usage: fig_background_subtraction.py <datasets/uploads> <stage-2 output dir> <out_dir> [measurement_id, default 3]
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

raw, proc, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OBS, MID = "ch3_lib_002_20230825T104221_00_l1", int(sys.argv[4]) if len(sys.argv) > 4 else 3
SUFFIX = "" if MID == 3 else f"_id{MID}"
C_P, C_BG, C_CLEAN = "#64748b", "#d97706", "#1d4ed8"
plt.rcParams.update({"font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9, "legend.fontsize": 8,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5})

df = pd.read_csv(next(raw.rglob(f"{OBS}.csv")))
cols = df.columns[6:-8]
wl = cols.astype(float).to_numpy()
last, k = None, 0
for i, r in df.iterrows():
    fl = (int(r["Force Reset Status"]), int(r["Laser Fire Status"]))
    if fl == (1, 0):
        last = i
    elif fl == (0, 1):
        k += 1
        if k == MID:
            p_row, b_row = i, last
            break
P, B = df.loc[p_row, cols].to_numpy(float), df.loc[b_row, cols].to_numpy(float)
cl = pd.read_csv(next(proc.rglob(f"{OBS}_cleaned.csv")))
cl = cl[cl.Measurement_ID == MID].sort_values("Wavelength_nm")
C = cl.Cleaned_Intensity.to_numpy()
assert np.array_equal(np.maximum(P - B, 0), C), "stored cleaned spectrum != max(0, P - B)"

fig, (a, b) = plt.subplots(2, 1, figsize=(7.2, 4.8), sharex=True, gridspec_kw={"height_ratios": [1.2, 1]})
a.plot(wl, P, color=C_P, lw=0.6, label=f"Plasma acquisition $I_P$ (row {p_row + 1}, {df.loc[p_row, 'Time']})")
a.plot(wl, B, color=C_BG, lw=0.6, label=f"Paired background $I_B$ (row {b_row + 1}, {df.loc[b_row, 'Time']})")
a.set_ylabel("L1 response (a.u.)")
a.set_ylim(top=max(P.max(), B.max()) * 1.32)
a.legend(loc="upper right", frameon=True, framealpha=1, edgecolor="none")
a.set_title("(a) Measured inputs (timestamps have 1 s resolution)", loc="left")
b.plot(wl, C, color=C_CLEAN, lw=0.6, label=r"$\max(0, I_P - I_B)$")
b.axvspan(560, 580, color="#e2e8f0", label="560–580 nm window")
b.set_ylabel("Cleaned (a.u.)")
b.set_xlabel("Wavelength (nm, L1 parent-table axis)")
b.set_ylim(0, C.max() * 1.35)
b.legend(loc="upper right", frameon=True, framealpha=1, edgecolor="none", ncol=2)
b.set_title("(b) Measured-frame subtraction with zero-clamping", loc="left")
for ax in (a, b):
    for lo, hi in [(wl[0], 220), (800, wl[-1])]:
        ax.axvspan(lo, hi, color="#f1f5f9", zorder=0)
    ax.set_xlim(wl[0], wl[-1])
b.text(0.006, 0.95, "outside\n220–800 nm", transform=b.transAxes, fontsize=6.5, color=C_P, va="top")
out.mkdir(parents=True, exist_ok=True)
for ext in ("png", "pdf"):
    fig.savefig(out / f"fig_background_subtraction{SUFFIX}.{ext}", dpi=300, bbox_inches="tight", facecolor="white",
                metadata={"CreationDate": None} if ext == "pdf" else None)
print(f"saved; plasma row {p_row + 1}, background row {b_row + 1}")
