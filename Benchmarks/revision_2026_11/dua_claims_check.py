"""Independent reproduction of Dua's archive-wide claims (613 spectra, parent + single-shot axes).
usage: python -P Benchmarks/revision_2026_11/dua_claims_check.py   (run from repo root)
"""
import sys
from itertools import combinations
from pathlib import Path
import numpy as np, pandas as pd
from scipy.signal import find_peaks
sys.path[:0] = ["Pipeline", "Benchmarks/revision_2026_11"]
from step4_nist_verification_logs import NIST_DB
import line_corroboration as L

TOL, RES = 0.5, 1.1
SH = L.SHIFTS
# ---------- spectra -> peak indicator matrix on a common axis ----------
P, keys, axis = [], [], None
for f in sorted(Path("datasets/processed/calibrated").rglob("*_cleaned.csv")):
    df = pd.read_csv(f, usecols=["Measurement_ID", "Wavelength_nm", "Cleaned_Intensity"])
    for mid, g in df.groupby("Measurement_ID"):
        g = g.sort_values("Wavelength_nm")
        wl, y = g.Wavelength_nm.to_numpy(), g.Cleaned_Intensity.to_numpy()
        c = (wl >= 220) & (wl <= 800); wl, y = wl[c], y[c]
        if axis is None: axis = wl
        assert np.array_equal(wl, axis)
        s = np.std(y[(wl >= 560) & (wl <= 580)])
        idx, _ = find_peaks(y, prominence=3 * s, distance=5)
        v = np.zeros(len(wl), bool); v[idx] = True
        P.append(v); keys.append((f.stem.replace("_cleaned", ""), mid))
P = np.array(P); C = np.concatenate([np.zeros((len(P), 1), int), P.cumsum(1)], 1)
# single-shot axis: same channels, different wavelengths
d0 = "datasets/uploads/20230825/ch3_lib_002_20230825T104221_00_l1/ch3_lib_002_20230825T104221_00_l1"
full = pd.to_numeric(pd.Series(pd.read_csv(d0 + ".csv", nrows=0).columns[6:]), errors="coerce").dropna().to_numpy(); assert len(full) == 2094
alt = pd.read_csv(d0 + "_0_3.csv").Wavelength.to_numpy()[(full >= 220) & (full <= 800)]
AX = {"parent": axis, "single": alt}
print(f"spectra {len(P)}  peaks {P.sum()}")

def hits(lines, ax, tol=TOL, s=0.0):
    """spectra x lines: any peak with |peak - (line+s)| < tol."""
    lo = np.searchsorted(ax, lines + s - tol, "right"); hi = np.searchsorted(ax, lines + s + tol, "left")
    return (C[:, hi] - C[:, lo]) > 0

def shift_test(lines, ax, tol=TOL, n=len(SH)):
    obs = hits(lines, ax, tol).sum()
    null = np.array([hits(lines, ax, tol, s).sum() for s in SH[:n]])
    return obs, null.mean(), (1 + (null >= obs).sum()) / (1 + n)

def holm(p):
    p = np.asarray(p); o = np.argsort(p); adj = np.empty_like(p); run = 0
    for r, i in enumerate(o):
        run = max(run, (len(p) - r) * p[i]); adj[i] = min(1, run)
    return adj

DB = pd.DataFrame(NIST_DB).rename(columns={"element": "sp", "wavelength": "wl"})
DB = DB[(DB.wl >= 220) & (DB.wl <= 800)].reset_index(drop=True)
ref = DB.wl.to_numpy()
# sanity vs Table 7: matched peaks (a peak counts once)
for name, ax in AX.items():
    pk = ax[np.nonzero(P)[1]]
    print(f"[check] {name}: matched peaks {(np.abs(pk[:, None] - ref[None]) < TOL).any(1).sum()}  (Table 7: 1572 / 1384)")

print("\n== 1. tolerance sensitivity, 24 reference lines, parent axis ==")
for tol in (0.5, 1.1, 2, 3, 5):
    grid = np.linspace(220, 800, 58001)
    cov = (np.abs(grid[:, None] - ref[None]) < tol).any(1).mean()
    h = hits(ref, axis, tol); rate = h.mean(0)
    obs, nm, p = shift_test(ref, axis, tol, 2000)
    print(f"±{tol:>3} nm: axis covered {cov:5.1%}  mean per-line hit rate {rate.mean():5.1%}  "
          f"lines hit in >90% of spectra {(rate > .9).sum():2d}/24  obs/null {obs}/{nm:.0f}  p={p:.3f}")

print("\n== 2. per-line, ±0.5 nm, parent axis ==")
nulls = np.array([hits(ref, axis, TOL, s).sum(0) for s in SH[:2000]])
obs = hits(ref, axis).sum(0)
pk_wl = [axis[r] for r in P]
iqr = []
for l in ref:
    o = [p[np.argmin(np.abs(p - l))] - l for p in pk_wl if len(p) and np.abs(p - l).min() < TOL]
    iqr.append(np.subtract(*np.percentile(o, [75, 25])) if len(o) > 3 else np.nan)
T = DB.assign(obs=obs, null_mean=nulls.mean(0).round(1), iqr=np.round(iqr, 3))
print(T.to_string(index=False))
print(f"lines at/below null mean: {(obs <= nulls.mean(0)).sum()}/24; IQR > 0.499: {(np.array(iqr) > .499).sum()}")
step = np.diff(axis).mean()
print(f"note: mean channel step {step:.3f} nm -> offsets are quantised; uniform-in-±0.5 IQR = 0.5")

print("\n== 3. species-level shift test + Holm ==")
lines = L.load_nist("datasets/nist_asd_lines")
lines = lines[(lines.wl >= 220) & (lines.wl <= 800)]
strong = lines.dropna(subset=["eps_10000"])
strong = strong[strong.eps_10000 >= 0.1 * strong.groupby("species").eps_10000.transform("max")]
for label, cat, col in (("pilot: step4 list", DB, "sp"), ("expanded: 19 NIST lists, eps>=0.1*max @10kK", strong, "species")):
    for name, ax in AX.items():
        rows = []
        for sp, g in cat.groupby(col):
            o, nm, p = shift_test(g.wl.to_numpy(), ax, n=2000)
            rows.append((sp, len(g), o, round(nm, 1), p))
        R = pd.DataFrame(rows, columns=["species", "lines", "obs", "null_mean", "p"]); R["p_holm"] = holm(R.p)
        print(f"-- {label}, {name} axis: {len(R)} tests, min raw p {R.p.min():.4f}, significant after Holm {(R.p_holm < .05).sum()}")
        print(R.sort_values("p").head(5).to_string(index=False))

print("\n== 4. 'contested': another species within 1.1 nm ==")
def contested(targets, tsp, cat):
    return np.mean([((cat.species != s) & ((cat.wl - w).abs() < RES)).any() for w, s in zip(targets, tsp)])
print(f"24 ref lines vs step4 list: {np.mean([((DB.sp != s) & ((DB.wl - w).abs() < RES)).any() for w, s in zip(DB.wl, DB.sp)]):.0%}")
print(f"24 ref lines vs full 19-species catalogue ({len(lines)} lines): {contested(DB.wl, DB.sp, lines):.0%}")
print(f"24 ref lines vs strong-line catalogue ({len(strong)} lines): {contested(DB.wl, DB.sp, strong):.0%}")

print("\n== 5. same-upper-level pairs (19 lists, 220-800 nm, A known) ==")
u = lines.dropna(subset=["A", "Ek", "gk"])
n_pairs = sum(len(g) * (len(g) - 1) // 2 for _, g in u.groupby(["species", "Ek", "gk"]))
n_res = sum(1 for _, g in u.groupby(["species", "Ek", "gk"]) for a, b in combinations(g.wl, 2) if abs(a - b) >= RES)
print(f"pairs sharing species+Ek+J_k: {n_pairs}; of which separated by >= 1.1 nm: {n_res}")

print("\n== 6. the 132 excluded plasma rows: nearest background in ANY product ==")
bg, ex = [], []
for f in sorted(Path("datasets/uploads").rglob("*_l1.csv")):
    df = pd.read_csv(f, usecols=["Time", "Force Reset Status", "Laser Fire Status"])
    t = pd.to_datetime(df.Time); seen = False
    for ti, fr, lf in zip(t, df["Force Reset Status"], df["Laser Fire Status"]):
        if (fr, lf) == (1, 0): bg.append((ti, f.stem)); seen = True
        elif (fr, lf) == (0, 1) and not seen: ex.append((ti, f.stem))
bt = pd.DataFrame(bg, columns=["t", "prod"]).sort_values("t")
gp, ga, same = [], [], 0
for ti, prod in ex:
    other = bt[bt["prod"] != prod]
    before = other[other.t <= ti]
    gp.append((ti - before.t.iloc[-1]).total_seconds() if len(before) else np.inf)
    ga.append((other.t - ti).abs().dt.total_seconds().min())
    same += (bt[bt["prod"] == prod].t > ti).any()
gp, ga = np.array(gp), np.array(ga)
print(f"excluded plasma rows: {len(ex)}; with a later background in the SAME file: {same}")
print(f"nearest PRECEDING background in another product: <=13 s {np.sum(gp <= 13)}, <=60 s {np.sum(gp <= 60)}, "
      f"median {np.median(gp):.0f} s, max {gp.max():.0f} s")
print(f"nearest background either side in another product: <=13 s {np.sum(ga <= 13)}, median {np.median(ga):.0f} s, max {ga.max():.0f} s")
