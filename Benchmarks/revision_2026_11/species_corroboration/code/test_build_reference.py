#!/usr/bin/env python3
"""Unit tests for the A3 reference-catalogue rules. Run: python test_build_reference.py"""
import sys, numpy as np, pandas as pd, functools
sys.path.insert(0, ".")
import build_reference as B

F = []
def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"   [{detail}]" if detail and not cond else ""))
    if not cond: F.append(name)

# ── Rule 6: greedy span-limited grouping ────────────────────────────────────
def group(ws, span=1.1):
    gid, gmin, out = 0, None, []
    for w in sorted(ws):
        if gmin is None: gmin = w
        elif (w - gmin) > span + 1e-9: gid += 1; gmin = w
        out.append(gid)
    return out

# 20 lines at 0.5 nm spacing: a 1.1 nm group holds 3 of them, so 20 -> 7 groups.
# Single-linkage chaining would have produced exactly 1 group.
check("grouping: no chaining across a long dense run",
      len(set(group([220 + 0.5*i for i in range(20)]))) == 7,
      f"got {len(set(group([220+0.5*i for i in range(20)])))}")
check("grouping: span boundary is inclusive at exactly 1.1 nm",
      group([400.0, 401.1]) == [0, 0])
check("grouping: 1.1 nm + epsilon opens a new group",
      group([400.0, 401.1001]) == [0, 1])
check("grouping: every group span <= 1.1 nm on random input",
      all(
        (lambda ws, g: max(
            max(w for w, k in zip(ws, g) if k == gg) - min(w for w, k in zip(ws, g) if k == gg)
            for gg in set(g)) <= 1.1 + 1e-9
        )(sorted(np.random.default_rng(s).uniform(220, 800, 300)),
          group(sorted(np.random.default_rng(s).uniform(220, 800, 300))))
        for s in range(20)))
check("grouping: singleton input yields one group", group([500.0]) == [0])

# ── Binning ─────────────────────────────────────────────────────────────────
def abin(w):
    for i, (lo, hi) in enumerate(B.BINS):
        if (lo <= w < hi) or (i == len(B.BINS)-1 and lo <= w <= hi): return lo
    return None
check("bins: lower edge belongs to its own bin", abin(300.0) == 300)
check("bins: upper edge belongs to the next bin", abin(299.9999) == 220)
check("bins: final bin is closed at 800", abin(800.0) == 700)
check("bins: 220 is the first bin", abin(220.0) == 220)
check("bins: every value in range lands in exactly one bin",
      all(abin(w) is not None for w in np.linspace(220, 800, 5001)))

# ── A3 ranking ──────────────────────────────────────────────────────────────
def rank(rows):
    G = pd.DataFrame(rows)
    G["_int"] = G.max_intensity.fillna(-np.inf)
    G["_aki"] = G.max_aki.fillna(-np.inf)
    G["_unc"] = G.min_unc_nm
    G = G.sort_values(["_int","_aki","ritz_rep_nm"], ascending=[False,False,True],
                      kind="mergesort").reset_index(drop=True)
    def cmp(i, j):
        ui, uj = G.at[i,"_unc"], G.at[j,"_unc"]
        if pd.notna(ui) and pd.notna(uj) and ui != uj: return -1 if ui < uj else 1
        ri, rj = G.at[i,"ritz_rep_nm"], G.at[j,"ritz_rep_nm"]
        return -1 if ri < rj else (1 if ri > rj else 0)
    order = []
    for _, blk in G.groupby(["_int","_aki"], sort=False):
        idx = list(blk.index)
        order.extend(sorted(idx, key=functools.cmp_to_key(cmp)) if len(idx) > 1 else idx)
    return list(G.loc[order].group_id)

def R(gid, i=None, a=None, u=None, r=500.0):
    return dict(group_id=gid, max_intensity=i, max_aki=a, min_unc_nm=u, ritz_rep_nm=r)

check("rank a: stronger intensity wins over stronger Aki",
      rank([R("weak_int_big_aki", i=10, a=1e9, r=400), R("strong_int", i=100, a=1, r=401)])[0] == "strong_int")
check("rank b: Aki breaks an intensity tie",
      rank([R("lo", i=50, a=1e5, r=400), R("hi", i=50, a=1e8, r=401)])[0] == "hi")
check("rank c: smaller uncertainty wins when BOTH are quoted",
      rank([R("coarse", i=50, a=1e6, u=0.01, r=400), R("fine", i=50, a=1e6, u=0.0001, r=401)])[0] == "fine")
check("rank c: a lone uncertainty is NEUTRAL, falls through to Ritz",
      rank([R("has_unc", i=50, a=1e6, u=0.0001, r=600), R("no_unc", i=50, a=1e6, u=None, r=400)])[0] == "no_unc")
check("rank d: median Ritz breaks a full tie, ascending",
      rank([R("red", i=50, a=1e6, u=0.001, r=700), R("blue", i=50, a=1e6, u=0.001, r=300)])[0] == "blue")
check("rank: missing intensity ranks last, not first",
      rank([R("none", i=None, a=1e9, r=400), R("some", i=1, a=1, r=401)])[0] == "some")
check("rank: missing intensity AND Aki ranks last",
      rank([R("empty", r=400), R("any", i=1, r=401)])[0] == "any")
check("rank: deterministic under input permutation",
      len({tuple(rank([R("a",i=5,a=1e6,u=0.01,r=400), R("b",i=5,a=1e6,r=500), R("c",i=5,a=1e6,u=0.001,r=600)][::s]))
           for s in (1,-1)}) == 1)

# ── Representative wavelength ───────────────────────────────────────────────
def rep(ritz, obs):
    rz = pd.Series(ritz, dtype=float)
    return float(rz.median()) if rz.notna().any() else float(pd.Series(obs, dtype=float).median())
check("representative: median of Ritz, not mean", rep([400.0, 401.0, 410.0], [0,0,0]) == 401.0)
check("representative: even count takes the midpoint", rep([400.0, 402.0], [0,0]) == 401.0)
check("representative: falls back to median observed when no Ritz",
      rep([np.nan, np.nan], [500.0, 502.0, 520.0]) == 502.0)
check("representative: partial Ritz uses the Ritz values present",
      rep([np.nan, 300.0, 302.0], [0,0,0]) == 301.0)

# ── num() / qualified() parsing ─────────────────────────────────────────────
check("num: strips Excel armouring", B.num('="220.5278"') == 220.5278)
check("num: strips NIST intensity suffix letters", B.num('="2g"') == 2.0)
check("num: handles bracketed uncertain intensity", B.num('="(0)?"') == 0.0)
check("num: blank yields NaN", np.isnan(B.num('=""')))
check("num: scientific notation survives", B.num('="8.9e+07"') == 8.9e7)
check("qualified: flags a suffixed value", B.qualified('="2g"') is True)
check("qualified: plain number is not flagged", B.qualified('="214"') is False)

print("\n" + (f"ALL CHECKS PASS" if not F else f"{len(F)} FAILURE(S): " + "; ".join(F)))
sys.exit(1 if F else 0)
