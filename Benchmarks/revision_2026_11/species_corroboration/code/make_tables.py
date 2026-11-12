#!/usr/bin/env python3
"""T-A, T-B, T-C and the test-summary table. Reads existing outputs only."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs" / "tables"; OUT.mkdir(parents=True, exist_ok=True)
TAG = "expanded_v4_A4rep"
S = pd.read_csv(BASE/"outputs"/f"E_species_scores__{TAG}__parent_axis.csv")
F = pd.read_csv(BASE/"outputs"/f"E_feature_matches__{TAG}__parent_axis.csv")
R = pd.read_csv(BASE/"outputs"/f"E_recurrence__{TAG}__parent_axis.csv")

# ── T-A uncertainty budget ──────────────────────────────────────────────────
tc = lambda l: (0.05212 + 3.94983e-5*l - 5.62736e-8*l**2)
g  = lambda l: -6.70943 + 0.04408*l - 8.26777e-5*l**2 + 4.7636e-8*l**3
def v2a(l):
    s = 1e3/l; n = 1 + 0.0000834254 + 0.02406147/(130-s*s) + 0.00015998/(38.9-s*s); return l/n
dT = 8.95 - 25.0
rows = []
for lo, hi in [(220,300),(300,400),(400,500),(500,600),(600,700),(700,800)]:
    ll = np.arange(lo, hi+1, 1.0)
    rows.append({
        "region_nm": f"{lo}-{hi}",
        "a_dispersion_internal_nm": "<=0.005",
        "b_air_vacuum_nm": f"{(ll-v2a(ll)).min():.3f}-{(ll-v2a(ll)).max():.3f}",
        "c_temperature_unapplied_nm": f"{abs(dT*tc(ll)).min():.2f}-{abs(dT*tc(ll)).max():.2f}",
        "d_WD_sensitivity_nm_per_mm": f"{abs(g(ll)).min():.2f}-{abs(g(ll)).max():.2f}",
        "d_WD_bound_at_6mm_nm": f"{abs(6*g(ll)).min():.1f}-{abs(6*g(ll)).max():.1f}",
        "d_WD_bound_at_10mm_nm": f"{abs(10*g(ll)).min():.1f}-{abs(10*g(ll)).max():.1f}",
        "combined_bound_c_plus_d10_nm": f"{(abs(dT*tc(ll))+abs(10*g(ll))).min():.1f}-{(abs(dT*tc(ll))+abs(10*g(ll))).max():.1f}",
    })
TA = pd.DataFrame(rows); TA.to_csv(OUT/"T-A_uncertainty_budget.csv", index=False)

# ── T-B fingerprint summary ─────────────────────────────────────────────────
rows = []
for sp in sorted(S.species.unique()):
    s = S[S.species == sp]; f = F[F.species == sp]; r = R[R.species == sp]
    distinct = f.group_id.nunique()
    unc_ids = set(f[~f.unresolved_interference].group_id)
    rec = int(r.recurring.sum()) if len(r) else 0
    if distinct == 0:            lab = "unsupported or inconclusive"
    elif distinct < 2:           lab = "isolated candidate"
    elif len(unc_ids) == 0:      lab = "multi-line-supported, all features contested"
    else:                        lab = "multi-line-supported with unresolved interference"
    rows.append(dict(species=sp, groups_in_catalogue=int(s.n_groups.iloc[0]),
                     max_supported_in_one_acq=int(s.n_supported.max()),
                     distinct_groups_supported=distinct,
                     uncontested_groups=len(unc_ids), recurring_groups=rec,
                     recurring_and_uncontested=int(r[(r.recurring) & (r.group_id.isin(unc_ids))].shape[0]) if len(r) else 0,
                     smallest_p_raw=round(float(s.p_raw.min()), 4),
                     smallest_p_holm_global=round(float(s.p_holm_global.min()), 3),
                     significant_after_holm=bool(s.significant_after_holm.any()),
                     classification=lab))
TB = pd.DataFrame(rows).sort_values(["classification","smallest_p_raw"])
TB.to_csv(OUT/"T-B_fingerprint_summary.csv", index=False)

# ── T-C recurrence ──────────────────────────────────────────────────────────
TC = R.copy()
sp_pk = F.groupby(["species","group_id"]).peak_nm.agg(["min","max"]).rename(
    columns={"min":"peak_nm_min","max":"peak_nm_max"}).reset_index()
TC = TC.merge(sp_pk, on=["species","group_id"], how="left")
TC["peak_spread_nm"] = (TC.peak_nm_max - TC.peak_nm_min).round(3)
TC = TC.sort_values(["n_acquisitions","species","group_nm"], ascending=[False,True,True])
TC.to_csv(OUT/"T-C_recurrence.csv", index=False)

# ── T-D test summary ────────────────────────────────────────────────────────
TD = pd.DataFrame([
 ["1","Archive label + documentation audit","Which axis each product declares; air/vacuum; accuracy",
  "Parent header declares no unit (opaque Header object); subfile declares a Wavelength field; no accuracy or air/vacuum stated anywhere","Inconclusive from labels alone"],
 ["2","Annexure-I polynomial vs parent L1 header","Does the header reproduce the documented dispersion solution?",
  "Max |residual| 0.0050 nm across all 2,094 columns = CSV rounding","Parent axis matches the documented solution"],
 ["3","Radiometric transfer-function table vs Annexure-I","Independent archive product cross-check (pixels 147-1832)",
  "Max |residual| 0.00050 nm = its own rounding","Internal corroboration, not external validation"],
 ["4","Subfile axis characterisation","Is the subfile axis a shift or reparameterisation of the parent?",
  "Best integer pixel offset leaves 2.04 nm; best cubic leaves 1.21 nm; departs 4.96-11.14 nm; shape does not match the WD term","Subfile axis undocumented and unexplained"],
 ["5","Application Note-2 marker test","Do peaks reach the 5 reference markers within +/-0.17 nm after temperature and fitted WD correction?",
  "Best RMS 0.87 nm; 1 of 5 markers inside tolerance; implied WD 184.7 mm, outside 205+/-10 mm","Marker test does not close; residual beyond (c) and (d)"],
 ["6","Uncertainty budget from archive equations","Bound the wavelength error per observed peak",
  "300-500 nm: ~4.5-8.4 nm; 700-800 nm: ~1.0-1.1 nm","Exceeds the +/-0.5 nm tolerance except near 700-800 nm"],
 ["7","Pilot species test, 27-line list","Species-level support on the original reference list",
  "33 tests; smallest raw p 0.0161 (Mg I, ID 4); 0 significant after global Holm","No species-level support"],
 ["8","Expanded species test, 471 groups, 19 species","Species-level support on the pre-specified expanded catalogue",
  "57 tests; smallest raw p 0.0256 (O I, ID 3); all 57 adjusted p = 1.000; 0 significant","No species-level support"],
 ["9","Competing-species assessment","How many supported features are uniquely attributable?",
  "186 of 210 supported features (89%) have another species' line within 1.1 nm; 8 species have no uncontested feature","Attribution is largely ambiguous at this resolution"],
 ["10","Recurrence across acquisitions","Do supported groups recur in IDs 1, 3, 4?",
  "41 of 167 distinct supported groups recur in >=2; 2 recur in all 3 (Fe II 754.87, O I 777.42)","Limited repeatable structure"],
 ["11","Single-shot axis sensitivity arm","Are species conclusions stable against the axis ambiguity?",
  "57 tests; 0 significant; leading species change entirely (Cr I, Mn I, H I)","Species conclusions are not axis-stable"],
 ["12","Catalogue QA and unit tests","Does the catalogue obey its own rules?",
  "471 groups, max span 1.0993 nm, 0 violations; 27,656 = 2,261 usable + 25,395 excluded; 29 unit tests pass","Catalogue internally consistent"],
], columns=["#","Test","Question","Result","Verdict"])
TD.to_csv(OUT/"T-D_test_summary.csv", index=False)

for n, t in [("T-A", TA), ("T-B", TB), ("T-C", TC), ("T-D", TD)]:
    print(f"{n}: {len(t)} rows -> {OUT.name}/")
print()
pd.set_option("display.width", 250)
print(TB.to_string(index=False))
print()
print("recurring groups whose matched peak moves > 0.35 nm between acquisitions:")
print(TC[(TC.recurring) & (TC.peak_spread_nm > 0.35)][["species","group_nm","n_acquisitions","acquisitions","peak_nm_min","peak_nm_max","peak_spread_nm"]].to_string(index=False))
