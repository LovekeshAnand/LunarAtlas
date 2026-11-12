"""Independent re-scoring of the co-author's species test (worked example IDs 1,3,4, parent axis) from her
line-group catalogue, with this repository's peak detection; plus counts behind her 89% and 859-pair figures.
usage: python -P verify_dua_species.py <her outputs dir>
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "Benchmarks/revision_2026_11")
import line_corroboration as L
O = Path(sys.argv[1])
cl = pd.read_csv("datasets/processed/calibrated/20230825/ch3_lib_002_20230825T104221_00_l1/ch3_lib_002_20230825T104221_00_l1_cleaned.csv")
rng = np.random.default_rng(20261021)                     # her null_seed / draw construction
SH = rng.uniform(2, 20, 10000) * rng.choice([-1, 1], 10000)

def supported(groups, P, s=0.0):
    """number of distinct peaks claimed by groups having any member within 0.5 nm (one peak per group per species)."""
    claimed = set()
    for m in groups:
        d = np.abs((m + s)[:, None] - P[None])
        if d.min() < 0.5: claimed.add(int(d.min(0).argmin()) if False else int(np.unravel_index(d.argmin(), d.shape)[1]))
    return len(claimed)

def holm(p):
    p = np.asarray(p); o = np.argsort(p); a = np.empty_like(p); r = 0
    for i, j in enumerate(o): r = max(r, (len(p) - i) * p[j]); a[j] = min(1, r)
    return a

for tag, scores in (("pilot", "E_species_scores__pilot.csv"), ("expanded_v4_A4rep", "E_species_scores__expanded_v4_A4rep__parent_axis.csv")):
    G = pd.read_csv(O / f"E_line_groups__{tag}.csv")
    G["m"] = G.members_nm.map(lambda s: np.array([float(x) for x in str(s).split(";")]))
    rows = []
    for mid in (1, 3, 4):
        P = L.spectrum(cl, mid)[3]
        for sp, g in G.groupby("species"):
            ms = list(g.m); o = supported(ms, P)
            null = np.array([supported(ms, P, s) for s in SH[:2000]])
            rows.append((mid, sp, o, (1 + (null >= o).sum()) / 2001))
    R = pd.DataFrame(rows, columns=["mid", "species", "n_supported", "p"]); R["p_holm"] = holm(R.p)
    H = pd.read_csv(O / scores).rename(columns={"measurement_id": "mid"})
    M = R.merge(H[["mid", "species", "n_supported", "p_raw"]], on=["mid", "species"], suffixes=("", "_hers"))
    print(f"== {tag}: {len(R)} tests; supported counts identical to hers: {(M.n_supported == M.n_supported_hers).all()} "
          f"({(M.n_supported != M.n_supported_hers).sum()} differ); significant after Holm: {(R.p_holm < .05).sum()}")
    print(M.sort_values("p").head(4).to_string(index=False))

F = pd.read_csv(O / "E_feature_matches__expanded_v4_A4rep__parent_axis.csv")
print(f"\n89% check: supported features {len(F)}, with another species within 1.1 nm {F.unresolved_interference.sum()} "
      f"({F.unresolved_interference.mean():.0%}); species with no uncontested feature: "
      f"{len(set(pd.read_csv(O / 'E_line_groups__expanded_v4_A4rep.csv').species) - set(F[~F.unresolved_interference].species))}")
Bk = pd.read_csv(O / "E_ratio_blocked_pairs.csv")
print(f"859 check: blocked pairs {len(Bk)}; passing pairs (candidate file) {len((O / 'E_ratio_candidate_pairs.csv').read_text().strip().splitlines())}")
print(Bk.columns.tolist())
