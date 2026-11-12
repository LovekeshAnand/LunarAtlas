#!/usr/bin/env python3
"""
Branching-ratio feasibility screening. Parent axis, A4 catalogue, existing peaks.
NO ratio is computed unless a pair clears every gate. Nothing is modified.
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
BASE = Path(__file__).resolve().parent.parent
OUT  = BASE / "outputs"
ARCH = Path(__import__("os").environ["CH3_LIBS_BUNDLE"])   # PRADAN lib-v2 bundle (for cal_res)
REPO = BASE.parents[2]   # repository root (ported from the co-author's layout)
for p in ("revision_v2", "Pipeline", "core/server"):
    sys.path.insert(0, str(REPO / p))
import analysis as A
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_reference import num

TAG  = "expanded_v4_A4rep"
FWHM = A.S["fwhm_upper_bound_nm"]        # 1.1
TOL  = A.S["match_tol_nm"]               # 0.5
RESOLVE_MIN = FWHM                       # pair must exceed the grouping convention

L = pd.read_csv(OUT / f"E_reference_lines__{TAG}.csv")
G = pd.read_csv(OUT / f"E_line_groups__{TAG}.csv")
F = pd.read_csv(OUT / f"E_feature_matches__{TAG}__parent_axis.csv")
for c in ("ek", "ei", "aki", "obs_nm"):
    if c in L: L[c] = L[c].map(num) if L[c].dtype == object else L[c]

resp = pd.read_csv(ARCH / "miscellaneous" / "ch3_lib_pds_cal_res.csv")
RESP_LO, RESP_HI = resp.iloc[:, 0].min(), resp.iloc[:, 0].max()

cand, blocked = [], []
n_pairs = 0
for sp, g in L.groupby("species"):
    g = g[g.ek.notna()]
    for ek, grp in g.groupby(g.ek.round(3)):
        if len(grp) < 2: continue
        rows = grp.sort_values("obs_nm").to_dict("records")
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                n_pairs += 1
                sep = b["obs_nm"] - a["obs_nm"]
                fails = []
                if not (220 <= a["obs_nm"] <= 800 and 220 <= b["obs_nm"] <= 800):
                    fails.append("outside 220-800 nm")
                if pd.isna(a["aki"]) or pd.isna(b["aki"]):
                    fails.append("Aki missing for one or both lines")
                if sep <= RESOLVE_MIN:
                    fails.append(f"separation {sep:.3f} nm <= {RESOLVE_MIN} nm, not resolvable")
                # supported peaks?
                sup = {}
                for lab, ln in (("a", a), ("b", b)):
                    m = F[(F.species == sp) & (np.abs(F.matched_ref_nm - ln["obs_nm"]) < 1e-3)]
                    sup[lab] = m
                if len(sup["a"]) == 0 or len(sup["b"]) == 0:
                    fails.append("no supported observed peak for one or both lines")
                shared = []
                if len(sup["a"]) and len(sup["b"]):
                    shared = sorted(set(sup["a"].measurement_id) & set(sup["b"].measurement_id))
                    if not shared:
                        fails.append("both lines supported, but never in the SAME acquisition")
                    else:
                        for mid in shared:
                            ca = sup["a"][sup["a"].measurement_id == mid].iloc[0]
                            cb = sup["b"][sup["b"].measurement_id == mid].iloc[0]
                            if ca.unresolved_interference or cb.unresolved_interference:
                                fails.append(f"ID {mid}: competing species within 1.1 nm of a matched line")
                # blend: group holding each line has >1 member
                for lab, ln in (("a", a), ("b", b)):
                    ng = int(G[G.group_id == ln["group_id"]].n_lines.iloc[0])
                    if ng > 1:
                        fails.append(f"line {ln['obs_nm']:.3f} sits in a {ng}-line blended group")
                rec = dict(species=sp, upper_level_Ek_cm1=ek,
                           lambda_a_nm=round(a["obs_nm"], 4), lambda_b_nm=round(b["obs_nm"], 4),
                           separation_nm=round(sep, 4),
                           Aki_a=a["aki"], Aki_b=b["aki"],
                           acquisitions_both_supported=",".join(map(str, shared)) if shared else "",
                           response_available=bool(RESP_LO <= a["obs_nm"] <= RESP_HI and RESP_LO <= b["obs_nm"] <= RESP_HI),
                           optical_depth_assessable=False,
                           status="usable" if not fails else "blocked",
                           blocking_reasons="; ".join(dict.fromkeys(fails)))
                (cand if not fails else blocked).append(rec)

C = pd.DataFrame(cand); B = pd.DataFrame(blocked)
C.to_csv(OUT / "E_ratio_candidate_pairs.csv", index=False)
B.to_csv(OUT / "E_ratio_blocked_pairs.csv", index=False)
print(f"same-upper-level pairs examined : {n_pairs}")
print(f"pairs passing every gate        : {len(C)}")
print(f"pairs blocked                   : {len(B)}")
print()
if len(B):
    reasons = B.blocking_reasons.str.split("; ").explode()
    reasons = reasons.str.replace(r"^ID \d+: ", "", regex=True)
    reasons = reasons.str.replace(r"^line [\d.]+ sits in a (\d+)-line blended group$", r"line sits in a blended group", regex=True)
    reasons = reasons.str.replace(r"^separation [\d.]+ nm", "separation", regex=True)
    print("first-failure census (a pair may fail several gates):")
    print(reasons.value_counts().to_string())
print()
print(f"detector response available over {RESP_LO:.2f}-{RESP_HI:.2f} nm "
      f"from ch3_lib_pds_cal_res.csv ({len(resp)} points)")
if len(C):
    print("\nCANDIDATE PAIRS:"); print(C.to_string(index=False))
