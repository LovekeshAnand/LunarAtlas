"""Does the Annexure-II temperature correction move detected peaks toward the Application Note-2 markers?
For each of the 613 spectra and each marker, the nearest detected peak within 2 nm; compares the axis as delivered,
the manual's sign and the opposite sign. Expected for the right sign: smaller |offset|, more peaks within 0.17/0.5 nm.
usage: python -P marker_sign_check.py <base_temperatures.csv>
"""
import sys, io, contextlib, runpy
import numpy as np, pandas as pd
temps = sys.argv[1]; sys.argv = ["x"]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path("Benchmarks/revision_2026_11/dua_claims_check.py")
P, axis, keys = g["P"], g["AX"]["parent"], g["keys"]
T = pd.read_csv(temps).set_index("product").base_temp_c
ts = lambda lam, t: (t - 25) * (0.05212 + 3.94983e-5 * lam - 5.62736e-8 * lam**2)
MK = np.array([251.75, 288.32, 394.55, 396.88, 777.28])
rng = np.random.default_rng(1)
for name, sign in (("as delivered", 0), ("manual sign", 1), ("opposite sign", -1)):
    offs = {m: [] for m in MK}
    for row, k in zip(P, keys):
        pk = axis[row]; pk = pk + sign * ts(pk, T[k[0]])
        for m in MK:
            d = pk - m
            if len(d) and np.abs(d).min() < 2: offs[m].append(d[np.abs(d).argmin()])
    allo = np.concatenate([np.array(v) for v in offs.values()])
    print(f"{name:14s} found {len(allo):4d}  median|d| {np.median(np.abs(allo)):.3f}  within 0.17: {np.sum(np.abs(allo)<=.17):4d}  "
          f"within 0.5: {np.sum(np.abs(allo)<.5):4d}  | per-marker median d: "
          + ", ".join(f"{m}:{np.median(v):+.2f}" for m, v in offs.items()))
