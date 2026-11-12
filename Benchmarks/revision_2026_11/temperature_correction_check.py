"""Effect of the Data User Manual's base-temperature correction (Annexure-II, eq. 2) on the NIST random-shift test.
corrected = measured + (T_base - 25) * (0.05212 + 3.94983e-5*measured - 5.62736e-8*measured^2), per product T_base
from base_temperatures.csv. Matching and peaks as Table 7 (one match per peak, |d| < 0.5 nm), and the SAME shift sets
as Table 7 (nist_check.py): seed 20261021 x 10,000 per spectrum; seed 20261022 x 1,000 for the archive, first 300 of
them for the single-shot axis. Both wavelength axes; both signs of the correction.
usage: python -P temperature_correction_check.py <base_temperatures.csv>
"""
import sys, io, contextlib, runpy
import numpy as np, pandas as pd

sys.argv, temps_csv = ["x"], sys.argv[1]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path("Benchmarks/revision_2026_11/dua_claims_check.py")
P, AX, ref, keys, DB, holm = (g[k] for k in "P AX ref keys DB holm".split())
T = pd.read_csv(temps_csv).set_index("product").base_temp_c
Tspec = np.array([T[k[0]] for k in keys])
ts = lambda lam, t: (t - 25) * (0.05212 + 3.94983e-5 * lam - 5.62736e-8 * lam**2)
R = np.sort(ref)

def shifts(n, seed):                     # identical to nist_check.py (Table 7)
    rng = np.random.default_rng(seed)
    return rng.uniform(2.0, 20.0, n) * rng.choice([-1, 1], n)
SH_W, SH_A = shifts(10000, 20261021), shifts(1000, 20261022)

def matched(pk, s=0.0):
    """peaks with a reference line within 0.5 nm (ref shifted by s)."""
    r = R + s; i = np.clip(np.searchsorted(r, pk), 1, len(r) - 1)
    return (np.minimum(np.abs(pk - r[i - 1]), np.abs(pk - r[i])) < 0.5).sum()

def peaks(axis, sign):
    return [axis[row] + sign * ts(axis[row], t) for row, t in zip(P, Tspec)]

def pval(o, null):
    return (1 + (null >= o).sum()) / (1 + len(null))

WE = [keys.index(("ch3_lib_002_20230825T104221_00_l1", m)) for m in (1, 3, 4)]
for axname, axis in AX.items():
    nA = 1000 if axname == "parent" else 300
    for label, sign in (("as delivered", 0), ("corrected (manual sign)", 1), ("corrected (opposite sign)", -1)):
        pk = peaks(axis, sign)
        out = []
        for i, m in zip(WE, (1, 3, 4)):
            o = matched(pk[i]); out.append(f"ID{m} {o} p={pval(o, np.array([matched(pk[i], s) for s in SH_W])):.4f}")
        allpk = np.concatenate(pk); o = matched(allpk); null = np.array([matched(allpk, s) for s in SH_A[:nA]])
        out.append(f"archive {o} (null {null.mean():.1f}) p={pval(o, null):.4f} [{nA} shifts]")
        print(f"[{axname:6s}] {label:26s} " + " | ".join(out))

print("\nper species, Holm (step4 list), parent axis, Table 7 archive shifts (1,000)")
for label, sign in (("as delivered", 0), ("corrected (manual sign)", 1)):
    pk = peaks(AX["parent"], sign)
    rows = []
    for sp, gq in DB.groupby("sp"):
        L = gq.wl.to_numpy()
        cnt = lambda s=0.0: sum(int((np.abs(p[:, None] - (L[None] + s)) < 0.5).any(0).sum()) for p in pk)
        o = cnt(); null = np.array([cnt(s) for s in SH_A])
        rows.append((sp, o, round(null.mean(), 1), pval(o, null)))
    D = pd.DataFrame(rows, columns=["species", "obs", "null_mean", "p"]); D["p_holm"] = holm(D.p)
    print(f"-- {label}: significant after Holm: {D[D.p_holm < .05].species.tolist()}")
    print(D.sort_values("p").head(4).to_string(index=False))
