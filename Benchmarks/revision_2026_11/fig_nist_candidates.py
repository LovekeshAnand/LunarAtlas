"""Point 8 figure: candidate NIST wavelength coincidences for Measurement ID 3 (worked example), with zoomed
windows. Reads the cleaned spectrum (stage-2 output) and the verified per-peak table written by
nist_check.py; peak rule identical to nist_check.py.

usage: fig_nist_candidates.py <repo> <stage-2 output dir> <per-peak csv> <out_dir>
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

repo, proc, perpeak, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
sys.path.insert(0, str(repo / "Pipeline"))
from step4_nist_verification_logs import NIST_DB  # noqa: E402

OBS, MID, NEAR = "ch3_lib_002_20230825T104221_00_l1", 3, 1.1
NIST = pd.DataFrame(NIST_DB).rename(columns={"element": "species", "wavelength": "ref"})
REF = NIST[(NIST.ref >= 220) & (NIST.ref <= 800)].sort_values("ref")
C_REF, C_CLEAN, C_CAND, C_NIST = "#64748b", "#1d4ed8", "#dc2626", "#0d9488"
plt.rcParams.update({"font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9, "legend.fontsize": 8,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5})

d = pd.read_csv(next(proc.rglob(f"{OBS}_cleaned.csv")))
g = d[d.Measurement_ID == MID].sort_values("Wavelength_nm")
wl, y = g.Wavelength_nm.to_numpy(), g.Cleaned_Intensity.to_numpy()
n = (wl >= 560) & (wl <= 580)
sig = float(np.std(y[n], ddof=0))
c = (wl >= 220) & (wl <= 800)
pk = np.flatnonzero(c)[find_peaks(y[c], prominence=3 * sig, distance=5)[0]]
lines = pd.read_csv(perpeak)
lines = lines[(lines.measurement_id == MID) & lines.candidate]
assert len(lines) == 8, len(lines)


def label(r):
    refs = [t.strip().rsplit(" ", 1) for t in r.refs_within_1p1.split(";")]
    txt = (f"{refs[0][0]} " + "/".join(f"{float(w):.1f}" for _, w in refs) if len({s for s, _ in refs}) == 1
           else "/".join(f"{s} {float(w):.1f}" for s, w in refs))
    return txt + " ?" if len(refs) > 1 else txt


windows = [(270, 292), (383, 400), (580, 598), (768, 786)]
fig = plt.figure(figsize=(7.2, 7.4))
gs = fig.add_gridspec(2, 4, height_ratios=[1.5, 1], hspace=0.85, wspace=0.45)
top = fig.add_subplot(gs[0, :])
top.plot(wl[c], y[c], color=C_CLEAN, lw=0.6)
top.plot(wl[pk], y[pk], "v", color=C_REF, ms=2.5, label=f"Detected peak ({len(pk)}; prominence ≥ 3σ = {3 * sig:.0f} a.u.)")
top.plot(lines.observed_nm, lines.intensity, "v", color=C_CAND, ms=4.5,
         label=f"Candidate coincidence, |Δλ| < 0.5 nm ({len(lines)})")
for x in REF.ref:
    top.axvline(x, color=C_NIST, ls=":", lw=0.6)
top.plot([], [], ls=":", color=C_NIST, label="NIST reference wavelength (24-line list)")
ymax, last = y[c].max(), -1e9
for r in lines.sort_values("observed_nm").itertuples():
    xt = max(r.observed_nm, last + 34)
    last = xt
    top.annotate(label(r), (r.observed_nm, r.intensity), xytext=(xt, ymax * 1.08), rotation=90,
                 ha="center", va="bottom", fontsize=6.5, color="#1e293b",
                 arrowprops=dict(arrowstyle="-", color=C_CAND, lw=0.4))
top.set_ylim(max(0, np.floor(y[c].min() / 100) * 100), ymax * 1.95)
top.set_xlim(220, 800)
top.set_ylabel("Cleaned (a.u.)")
top.set_xlabel("Wavelength (nm, L1 parent-table axis)")
top.set_title(f"(a) Measurement ID {MID}: wavelength coincidences, not confirmed identifications", loc="left", pad=22)
top.legend(loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, fontsize=6.5, ncol=3,
           handletextpad=0.3, columnspacing=1.0)
for i, (lo, hi) in enumerate(windows):
    ax = fig.add_subplot(gs[1, i])
    m = (wl >= lo) & (wl <= hi)
    ax.plot(wl[m], y[m], color=C_CLEAN, lw=0.7, drawstyle="steps-mid")
    pm = pk[(wl[pk] >= lo) & (wl[pk] <= hi)]
    ax.plot(wl[pm], y[pm], "v", color=C_REF, ms=3)
    lm = lines[(lines.observed_nm >= lo) & (lines.observed_nm <= hi)]
    ax.plot(lm.observed_nm, lm.intensity, "v", color=C_CAND, ms=4.5)
    groups = []   # references closer than 1.1 nm share one label (possibly unresolved)
    for r in REF[(REF.ref >= lo) & (REF.ref <= hi)].itertuples():
        ax.axvline(r.ref, color=C_NIST, ls=":", lw=0.8)
        if groups and r.ref - groups[-1][-1].ref < NEAR:
            groups[-1].append(r)
        else:
            groups.append([r])
    for grp in groups:
        sp = {r.species for r in grp}
        txt = (f"{grp[0].species} " + "/".join(f"{r.ref:.1f}" for r in grp) if len(sp) == 1
               else "/".join(f"{r.species} {r.ref:.1f}" for r in grp))
        ax.text(np.mean([r.ref for r in grp]), 1.01, txt, transform=ax.get_xaxis_transform(), rotation=90,
                fontsize=6, ha="center", va="bottom", color="#1e293b")
    top.axvspan(lo, hi, color="#fef3c7", zorder=0)
    ax.set_xlim(lo, hi)
    ax.set_xlabel(f"({'bcde'[i]}) {lo}–{hi} nm", fontsize=8)
    ax.tick_params(labelsize=6.5)
out.mkdir(parents=True, exist_ok=True)
for ext in ("png", "pdf"):
    fig.savefig(out / f"fig_nist_candidates.{ext}", dpi=300, bbox_inches="tight", facecolor="white",
                metadata={"CreationDate": None} if ext == "pdf" else None)
print("saved", out / "fig_nist_candidates.{png,pdf}")
