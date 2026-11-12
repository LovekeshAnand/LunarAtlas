#!/usr/bin/env python3
"""F-A and F-B for the validation package. Plot only: no new computation."""
import sys
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.25,
                     "figure.dpi": 200, "savefig.bbox": "tight"})

BASE = Path(__file__).resolve().parent.parent
OUT  = BASE / "outputs" / "figures"; OUT.mkdir(parents=True, exist_ok=True)
REPO = BASE.parents[2]   # repository root (ported from the co-author's layout)
ARCH = Path(__import__("os").environ["CH3_LIBS_BUNDLE"])   # PRADAN lib-v2 bundle (for cal_res)
for p in ("revision_v2", "Pipeline", "core/server"):
    sys.path.insert(0, str(REPO / p))
import analysis as A

TAG = "expanded_v4_A4rep"
OBS = A.S["worked_obs"]
pix = np.arange(1, 2095)
POLY = 163.9731 + 0.38172*pix - 1.48482e-5*pix**2 - 2.17022e-9*pix**3

# ───────────────────────── F-A: calibration cross-check ─────────────────────
d = A.RAW / "20230825" / OBS
hdr = np.array([float(x) for x in open(d / f"{OBS}.csv").readline().strip().split(",")[6:2100]])
sub = pd.read_csv(sorted(d.glob(f"{OBS}_*.csv"))[0]).iloc[:, 0].to_numpy(float)
cal = pd.read_csv(ARCH / "miscellaneous" / "ch3_lib_pds_cal_res.csv").iloc[:, 0].to_numpy(float)
cpix = np.arange(147, 147 + len(cal))

fig, ax = plt.subplots(2, 1, figsize=(7.6, 5.0), sharex=True)
a = ax[0]
a.plot(pix, (hdr - POLY)*1000, lw=0.9, color="#1f6feb", label="L1 parent-table header")
a.plot(cpix, (cal - POLY[cpix-1])*1000, lw=0.9, color="#1f7a4d",
       label="radiometric transfer-function table (pixels 147-1832)")
a.axhspan(-5, 5, color="#999", alpha=0.18)
a.text(2080, 7.0, "grey band = +/-5 pm, the CSV rounding half-step; residuals are rounding noise only",
       ha="right", fontsize=7.2, color="#555")
a.set_ylabel("residual vs Annexure-I (pm)"); a.set_ylim(-9, 9)
a.legend(fontsize=7.5, loc="lower left", framealpha=0.95)
a.set_title("(a) Two archive products agree with the documented dispersion polynomial to within their own rounding",
            fontsize=8.5, loc="left")
b = ax[1]
b.plot(pix, sub - POLY, lw=1.0, color="#b03030", label="single-shot subfile axis")
b.axhline(0, lw=0.8, color="#666")
b.set_ylabel("residual vs Annexure-I (nm)"); b.set_xlabel("detector pixel number")
b.legend(fontsize=7.5, loc="upper right", framealpha=0.95)
b.set_title("(b) The subfile axis departs by 4.96-11.14 nm and matches no documented transformation",
            fontsize=8.5, loc="left")
b.set_ylim(-12.5, 0.8)
b.annotate(f"{sub[0]-POLY[0]:+.2f} nm", xy=(1, sub[0]-POLY[0]), xytext=(60, -11.9),
           fontsize=7.5, color="#b03030")
b.annotate(f"{sub[-1]-POLY[-1]:+.2f} nm", xy=(2094, sub[-1]-POLY[-1]), xytext=(1700, -4.1),
           fontsize=7.5, color="#b03030", ha="right")
a.set_xlim(1, 2094)
fig.tight_layout(); fig.savefig(OUT / "F-A_calibration_cross_check.png")
print("F-A written | parent max |resid| = %.4f nm | cal_res max = %.5f nm | subfile %.2f to %.2f nm"
      % (np.abs(hdr-POLY).max(), np.abs(cal-POLY[cpix-1]).max(), (sub-POLY).min(), (sub-POLY).max()))

# ───────────────────────── F-B: focused panels ──────────────────────────────
G = pd.read_csv(BASE / "outputs" / f"E_line_groups__{TAG}.csv")
L = pd.read_csv(BASE / "outputs" / f"E_reference_lines__{TAG}.csv")
F = pd.read_csv(BASE / "outputs" / f"E_feature_matches__{TAG}__parent_axis.csv")
cl = A.cleaned(OBS, "20230825")

targets = [("Fe II", 754.8661, 751.5, 758.5), ("O I", 777.4170, 774.5, 780.5)]
fig, axs = plt.subplots(3, 2, figsize=(9.2, 7.0), sharex="col")
for col, (sp, gnm, lo, hi) in enumerate(targets):
    grp = G[(G.species == sp) & (np.isclose(G.group_nm, gnm))].iloc[0]
    mem = [float(x) for x in grp.members_nm.split(";")]
    comp = L[(L.obs_nm.between(lo, hi)) & (L.species != sp)]
    for row, mid in enumerate(A.S["eval_ids"]):
        ax2 = axs[row, col]
        g = cl[mid]; wl = g.Wavelength_nm.to_numpy(float); y = g.Cleaned_Intensity.to_numpy(float)
        pk, prom, sig = A.detect(wl, y)
        m = (wl >= lo) & (wl <= hi)
        ax2.plot(wl[m], y[m], "-o", lw=1.0, ms=2.6, color="#222", zorder=3)
        ax2.axhline(3*sig, ls="--", lw=0.9, color="#b03030")
        for mm in mem:
            ax2.axvspan(mm-0.5, mm+0.5, color="#1f7a4d", alpha=0.10, lw=0)
            ax2.axvline(mm, ls=":", lw=1.0, color="#1f7a4d", zorder=2)
        for r in comp.itertuples():
            ax2.axvline(r.obs_nm, ls="-.", lw=1.0, color="#e0a21a", zorder=2)
        hit = F[(F.species == sp) & (np.isclose(F.group_nm, gnm)) & (F.measurement_id == mid)]
        txt = "no supported match"
        if len(hit):
            h = hit.iloc[0]
            ax2.plot([h.peak_nm], [y[np.argmin(np.abs(wl - h.peak_nm))]], "v", ms=8,
                     color="#b03030", zorder=5)
            txt = (f"peak {h.peak_nm:.2f} -> member {h.matched_ref_nm:.3f}, "
                   f"offset {h.offset_nm:+.3f} nm; "
                   + ("contested: " + h.competitors if h.unresolved_interference else "uncontested"))
        ax2.set_title(f"{sp} {gnm:.2f} nm group | acquisition {mid} | 3 sigma = {3*sig:.0f}\n{txt}",
                      fontsize=7.4, loc="left")
        ax2.set_xlim(lo, hi)
        if col == 0: ax2.set_ylabel("cleaned counts")
        if row == 2: ax2.set_xlabel("wavelength (nm), parent-table axis")
fig.suptitle("Dotted green: group member lines, shaded +/-0.5 nm. Dash-dot amber: competing-species lines within the window. "
             "Red triangle: supported peak. Dashed red: 3 sigma threshold.", fontsize=7.6, y=1.005)
fig.tight_layout(); fig.savefig(OUT / "F-B_focused_panels_FeII_OI.png")
print("F-B written")
