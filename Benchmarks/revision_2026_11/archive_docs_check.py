"""Checks of the wavelength-axis claims against the PRADAN bundle's own documents.

Sources (lib-v2/document, lib-v2/miscellaneous):
  Data User Manual LEOS-PSA-LSID-CHN3-REP-23-01-01: Annexure-I p.18 (pixel->wavelength cubic),
    Annexure-II p.20 (base-temperature shift, eq. 2), p.5 table (WD 205 +/-10 mm hard, +/-6 mm powder;
    resolution <= 1 nm); SIS: WD 205 +/-8 mm.
  Application Note-2 (wavelength_shift_correction_aspects.pdf): WD shift equation, 5 markers, +/-0.17 nm.
  functional_operational_table.pdf: base temperature per operation (3.63-25.57 C over the archive).
usage: python -P archive_docs_check.py <ch3_libs/lib-v2> <stage-2 cleaned dir>
"""
import re, sys
from collections import Counter
from pathlib import Path
import numpy as np, pandas as pd
from scipy.signal import find_peaks

B, PROC = Path(sys.argv[1]), Path(sys.argv[2])
CAL = B / "data" / "calibrated"
I0, C1, C2, C3 = 163.9731, 0.38172, -1.48482e-5, -2.17022e-9          # Annexure-I
T_RANGE = (3.63, 25.57)                                                # op. table min/max base temp, C
T_ID3 = 8.95                                                           # op. 1, ch3_lib_002_20230825T104221_00
MARKERS = np.array([251.75, 288.32, 394.55, 396.88, 777.28])           # App. Note-2 Table-I
temp_shift = lambda lam, T: (T - 25) * (0.05212 + 3.94983e-5 * lam - 5.62736e-8 * lam**2)     # eq. 2
wd_shift = lambda lam, D: D * (-6.70943 + 0.04408 * lam - 8.26777e-5 * lam**2 + 4.7636e-8 * lam**3)

# ---------------- A. axes vs Annexure-I ----------------
parents = sorted(p for p in CAL.rglob("*_l1.csv"))
heads = {tuple(pd.read_csv(p, nrows=0).columns[6:-8]) for p in parents}
parent = np.array(next(iter(heads)), float)
p = np.arange(1, 2095)
ann = I0 + C1 * p + C2 * p**2 + C3 * p**3
first = parents[0]
single = pd.read_csv(sorted(first.parent.glob("*_0_*.csv"))[0]).Wavelength.to_numpy()
singles = {tuple(pd.read_csv(f).Wavelength.round(4)) for f in list(CAL.rglob("*_l1_0_*.csv"))[::25]}
cr = pd.read_csv(B / "miscellaneous" / "ch3_lib_pds_cal_res.csv").iloc[:, 0].to_numpy()
cr_ann = ann[np.abs(ann[:, None] - cr[None]).argmin(0)]
print(f"A. parent tables: {len(parents)}, distinct parent axes {len(heads)}; sampled single-shot axes distinct: {len(singles)}")
print(f"   parent axis - Annexure-I: max |d| {np.abs(parent - ann).max():.4f} nm (header has 2 decimals)")
print(f"   single-shot axis - Annexure-I: {(single - ann).min():.2f} .. {(single - ann).max():.2f} nm")
print(f"   cal_res ({len(cr)} rows, {cr.min()}-{cr.max()} nm) - nearest Annexure-I: max |d| {np.abs(cr - cr_ann).max():.5f} nm")
d_sp = single - parent; c = (parent >= 220) & (parent <= 800)
print(f"   single - parent over 220-800: {d_sp[c].min():.2f} .. {d_sp[c].max():.2f} nm")
# does the second axis look like a documented correction?
lam = parent[c]
for name, g in (("WD shift", wd_shift(lam, 1)), ("temp shift", temp_shift(lam, 26))):
    k = np.polyfit(g, d_sp[c], 1)
    print(f"   fit (single-parent) = a + b*{name}: resid RMS {np.std(d_sp[c] - np.polyval(k, g)):.3f} nm (a={k[1]:.2f}, b={k[0]:.2f})")

# ---------------- B. uncertainty budget (Dua's 4.5-8.4 nm) ----------------
print("\nB. uncorrected shift budget per band, |temp term| over op-table T range + |WD term|")
bands = [(220, 300), (300, 500), (500, 700), (700, 800)]
lam = np.linspace(220, 800, 5801)
tmax = np.max(np.abs([temp_shift(lam, T) for T in T_RANGE]), 0)
print(f"   temp term alone: max {tmax.max():.2f} nm (|T-25| up to {25 - T_RANGE[0]:.1f} C); ID3 product (8.95 C): "
      f"{temp_shift(np.array([300, 400, 500, 777]), T_ID3).round(2)} nm at 300/400/500/777")
for D in (6, 8, 10):
    w = np.abs(wd_shift(lam, D))
    row = []
    for lo, hi in bands:
        m = (lam >= lo) & (lam <= hi)
        lin, rss = tmax[m] + w[m], np.hypot(tmax[m], w[m])
        row.append(f"{lo}-{hi}: WD {w[m].min():.1f}-{w[m].max():.1f}, lin {lin.min():.1f}-{lin.max():.1f}, rss {rss.min():.1f}-{rss.max():.1f}")
    print(f"   D=±{D} mm | " + " | ".join(row))
# Dua's 4.5-8.4 nm: linear sum, ID3 base temperature only, D = ±10 mm
row = []
for lo, hi in bands:
    m = (lam >= lo) & (lam <= hi); v = np.abs(temp_shift(lam[m], T_ID3)) + np.abs(wd_shift(lam[m], 10))
    row.append(f"{lo}-{hi}: {v.min():.1f}-{v.max():.1f}")
print("   ID3 temp (8.95 C) + D=±10 mm, linear | " + " | ".join(row))

# ---------------- C. App. Note-2 markers on ID3 ----------------
print("\nC. Application Note-2 markers, worked example ID 3")
cl = pd.read_csv(next(PROC.rglob("ch3_lib_002_20230825T104221_00_l1_cleaned.csv")))
s = cl[cl.Measurement_ID == 3].sort_values("Wavelength_nm")
wl, y = s.Wavelength_nm.to_numpy(), s.Cleaned_Intensity.to_numpy()
k = (wl >= 220) & (wl <= 800); wl, y = wl[k], y[k]; ax_s = single[(parent >= 220) & (parent <= 800)]
sig = np.std(y[(wl >= 560) & (wl <= 580)]); pk, _ = find_peaks(y, prominence=3 * sig, distance=5)
for name, axis in (("parent", wl), ("single", ax_s), ("parent+temp-corr", wl + temp_shift(wl, T_ID3))):
    off = np.array([axis[pk][np.abs(axis[pk] - m).argmin()] - m for m in MARKERS])
    print(f"   {name:17s} nearest-peak offsets {off.round(2)}  RMS {np.sqrt(np.mean(off**2)):.3f} nm, within ±0.17: {(np.abs(off) <= .17).sum()}/5")
# best single D that brings markers onto peaks (App. Note-2 procedure), on the temp-corrected axis
axT = wl + temp_shift(wl, T_ID3)
best = min(((np.sqrt(np.mean([np.min(np.abs(axT[pk] + wd_shift(axT[pk], D) - m)) ** 2 for m in MARKERS])), D)
            for D in np.arange(-10, 10.01, 0.1)))
print(f"   best D in ±10 mm: {best[1]:+.1f} mm -> marker RMS {best[0]:.3f} nm")

# ---------------- D. label audit ----------------
print("\nD. labels / documents")
xmls = sorted(CAL.rglob("*_l1.xml"))
pat = re.compile(r"accura|vacuum|\bair\b|uncertaint|temperature", re.I)
hits = Counter(m.group(0).lower() for x in xmls for m in pat.finditer(x.read_text(errors="ignore")))
print(f"   parent labels {len(xmls)}; terms found: {dict(hits) or 'none'}")
def sig_of(x):
    t = x.read_text(errors="ignore")
    t = re.sub(r">[^<]*<", "><", t)                 # drop all values, keep element structure
    return re.sub(r"\s+", "", t)
sigs = Counter(sig_of(x) for x in xmls)
print(f"   distinct parent-label element structures (values stripped): {len(sigs)}; sizes {sorted(sigs.values(), reverse=True)[:5]}")
fields = Counter(tuple(re.findall(r"<name>([^<]+)</name>", re.search(r"<Record_Delimited>.*</Record_Delimited>", x.read_text(errors='ignore'), re.S).group(0))) for x in xmls)
print(f"   distinct table field lists: {len(fields)}")
