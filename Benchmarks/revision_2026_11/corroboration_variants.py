"""Line-corroboration test (line_corroboration.py, unchanged) on four versions of the worked example:
  delivered        - L1 axis and counts as archived (must reproduce table8's 15 candidates)
  temp             - Annexure-II base-temperature correction (8.95 C, operational table, op. 1)
  response         - counts x transfer function (cal_res, intensity-calibration note eq. 2; constant f omitted)
  temp+response    - both
Candidates are regenerated per variant with the paper's rule (3-sigma prominence peaks, nearest step4 reference
within 0.5 nm, one match per peak), so the candidate list itself follows the correction.
usage: python -P corroboration_variants.py <ch3_libs/lib-v2> <out_dir>
"""
import sys, io, contextlib
from pathlib import Path
import numpy as np, pandas as pd
sys.path[:0] = ["Pipeline", "Benchmarks/revision_2026_11"]
from step4_nist_verification_logs import NIST_DB
import line_corroboration as L

B, OUT = Path(sys.argv[1]), Path(sys.argv[2])
CLEAN = Path("datasets/processed/calibrated/20230825/ch3_lib_002_20230825T104221_00_l1/"
             "ch3_lib_002_20230825T104221_00_l1_cleaned.csv")
T_BASE = 8.95
ts = lambda lam: (T_BASE - 25) * (0.05212 + 3.94983e-5 * lam - 5.62736e-8 * lam**2)
cr = pd.read_csv(B / "miscellaneous" / "ch3_lib_pds_cal_res.csv"); cr.columns = ["wl", "tf"]
REF = pd.DataFrame(NIST_DB).rename(columns={"element": "sp", "wavelength": "wl"})
REF = REF[(REF.wl >= 220) & (REF.wl <= 800)]

base = pd.read_csv(CLEAN)
base = base[base.Measurement_ID.isin([1, 3, 4])]
summary = []
for name, temp, resp in (("delivered", 0, 0), ("temp", 1, 0), ("response", 0, 1), ("temp+response", 1, 1)):
    d = base.copy()
    lam0 = d.Wavelength_nm.to_numpy()
    if resp:   # per pixel, before any wavelength shift; outside cal_res range -> NaN -> dropped
        tf = np.interp(lam0, cr.wl, cr.tf, left=np.nan, right=np.nan)
        d["Cleaned_Intensity"] = d.Cleaned_Intensity * tf
        d = d[np.isfinite(d.Cleaned_Intensity)]
    if temp:
        d["Wavelength_nm"] = d.Wavelength_nm + ts(d.Wavelength_nm)
    od = OUT / name; od.mkdir(parents=True, exist_ok=True)
    d.to_csv(od / "spectrum.csv", index=False)
    cands = []
    for mid in (1, 3, 4):
        wl, y, sigma, pk, prom = L.spectrum(d, mid)
        for p in pk:
            dd = (REF.wl - p).abs()
            if dd.min() < 0.5:
                r = REF.loc[dd.idxmin()]
                cands.append(dict(mid=mid, detected_wl=round(p, 2), nist_element=r.sp, nist_wl=r.wl,
                                  delta_wl=round(r.wl - p, 2)))
    C = pd.DataFrame(cands); C.to_csv(od / "candidates.csv", index=False)
    with contextlib.redirect_stdout(io.StringIO()):
        L.main("datasets/nist_asd_lines", od / "spectrum.csv", od / "candidates.csv", od)
    S = pd.read_csv(od / "corroboration_summary.csv")
    S["p_shift"] = pd.to_numeric(S.p_shift, errors="coerce")
    R = pd.read_csv(od / "line_ratios.csv")
    testable = S.expected_partner_features > 0
    summary.append(dict(variant=name, candidates=len(S),
                        candidate_list="; ".join(f"ID{a} {b} {c}" for a, b, c in zip(S.measurement_id, S.species, S.ref_nm)),
                        testable=int(testable.sum()),
                        no_partner_found=int((testable & (S.partners_found == 0)).sum()),
                        partner_found_not_chance=int((testable & (S.partners_found > 0) & (S.p_shift >= .05)).sum()),
                        confirmed_p_lt_005=int((testable & (S.p_shift < .05)).sum()),
                        caii_ratio_id3=R[R.measurement_id == 3].obs_ratio_peak.iloc[0]))
    if name == "delivered":
        t8 = pd.read_csv("Benchmarks/table_outputs/table8_nist_verification.csv")
        same = sorted(zip(t8.mid, t8.nist_element, t8.nist_wl)) == sorted(zip(C.mid, C.nist_element, C.nist_wl))
        print(f"[check] delivered candidates == table8 (15 rows): {same} ({len(C)} rows)")
        assert same
S = pd.DataFrame(summary); S.to_csv(OUT / "variants_summary.csv", index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 200)
print(S.drop(columns="candidate_list").to_string(index=False))
for r in summary: print(f"\n{r['variant']}: {r['candidate_list']}")
