#!/usr/bin/env python3
"""
Stage 1 of species corroboration: build the reference set from NIST ASD exports.
Applies RULES.md sections 3-7 WITHOUT reading any spectrum.
Run this before run_species.py. Outputs are read-only inputs to that stage.

  python build_reference.py               # uses reference/nist_raw/*.tsv
  python build_reference.py --pilot       # regression mode: the 27-line NIST_DB
  python build_reference.py --group 0.7   # sensitivity grouping width
"""
import argparse, functools, hashlib, json, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REPO = BASE.parents[2]   # repository root (ported from the co-author's layout)
RAWD = REPO / "datasets" / "nist_asd_lines"   # identical to the co-author's reference/nist_raw
OUT  = BASE / "outputs"

CAL_MIN, CAL_MAX = 220.0, 800.0
GROUP_NM_DEFAULT  = 1.1
MAX_UNC_NM        = 0.05
MIN_GRADE         = "C"
SPAN_EPS          = 1e-9   # float guard so a span of exactly MAX_SPAN still joins
PER_BIN           = 5
BINS              = [(220,300),(300,400),(400,500),(500,600),(600,700),(700,800)]
CAP_GROUPS        = PER_BIN * len(BINS)   # 30
GRADES = ["AAA","AA","A+","A","B+","B","C+","C","D+","D","E"]

def grade_ok(g):
    if not isinstance(g,str) or not g.strip(): return None      # not quoted
    g = g.strip()
    if g not in GRADES: return None
    return GRADES.index(g) <= GRADES.index(MIN_GRADE)

def num(x):
    """Numeric part of a NIST field. Handles Excel armouring (="214") and
    qualifier notation ((0)?, 2g, 1000*) by keeping digits only."""
    s = str(x).strip().strip('"').replace("=", "").strip('"')
    s = "".join(c for c in s if c.isdigit() or c in ".-eE")
    try:
        return float(s)
    except Exception:
        return np.nan


def qualified(x):
    """True where NIST attached a qualifier letter or bracket to the value."""
    s = str(x).strip().strip('"').replace("=", "").strip('"')
    return bool(s) and any(c.isalpha() or c in "()[]?*:" for c in s)


COLMAP = {
    "obs_wl_air(nm)":"obs_nm","obs_wl_vac(nm)":"obs_nm","obs_wl(nm)":"obs_nm","observed":"obs_nm",
    "ritz_wl_air(nm)":"ritz_nm","ritz_wl_vac(nm)":"ritz_nm",
    "unc_obs_wl":"unc_nm","unc_ritz_wl":"unc_ritz","intens":"intensity",
    "aki(s^-1)":"aki","aki":"aki","acc":"acc","ei(cm-1)":"ei","ek(cm-1)":"ek",
    "ei(ev)":"ei","ek(ev)":"ek","element":"element","sp_num":"sp_num",
    "conf_i":"conf_i","term_i":"term_i","conf_k":"conf_k","term_k":"term_k",
    "j_i":"j_i","j_k":"j_k","type":"type",
}
ROMAN = {1:"I",2:"II",3:"III"}

def load_exports():
    files = sorted(f for f in RAWD.iterdir()
                   if f.is_file() and f.name.lower().endswith((".csv", ".txt", ".tsv")))
    if not files: return None
    frames, seen_vac = [], []
    for f in files:
        txt = f.read_text(encoding="utf-8", errors="replace")
        sep = "\t" if ("\t" in txt.split("\n")[0] and "," not in txt.split("\n")[0]) else ","
        d = pd.read_csv(f, sep=sep, dtype=str, engine="python", on_bad_lines="skip",
                        encoding="utf-8", encoding_errors="replace")
        raw_cols = [c.strip().strip('"').lower() for c in d.columns]
        if any("_vac(" in c for c in raw_cols):
            seen_vac.append(f.name)
        d.columns = [COLMAP.get(c, c) for c in raw_cols]
        # species from the file name: Fe_I.csv.txt / Ti_I.csv / Cr_II.txt -> "Fe I"
        stem = f.name
        for suf in (".csv.txt", ".tsv", ".csv", ".txt"):
            if stem.lower().endswith(suf):
                stem = stem[: -len(suf)]; break
        d["species"] = stem.replace("_", " ").strip()
        d["source_file"] = f.name
        frames.append(d)
    if seen_vac:
        sys.exit("VACUUM wavelengths detected in: " + ", ".join(seen_vac) +
                 "\nRULES.md requires air. Re-export these with an air setting, or remove them.")
    return pd.concat(frames, ignore_index=True)


def load_pilot():
    sys.path.insert(0, str(REPO / "Pipeline"))
    from step4_nist_verification_logs import NIST_DB
    d = pd.DataFrame(NIST_DB).rename(columns={"element":"species","wavelength":"obs_nm"})
    d["intensity"] = np.nan; d["aki"] = np.nan; d["acc"] = ""; d["unc_nm"] = np.nan
    d["source_file"] = "step4_nist_verification_logs.py::NIST_DB"
    return d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--group", type=float, default=GROUP_NM_DEFAULT)
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    tag = a.tag or ("pilot" if a.pilot else f"expanded_g{a.group:g}".replace(".", "p"))

    d = load_pilot() if a.pilot else load_exports()
    if d is None:
        sys.exit(f"No NIST exports found in {RAWD}. Add *.tsv exports, or run with --pilot.")
    if "intensity" in d: d["intensity_raw"] = d["intensity"]
    for c in ["obs_nm","unc_nm","intensity","aki"]:
        d[c] = d[c].map(num) if c in d else np.nan
    if "acc" not in d: d["acc"] = ""
    d["acc"] = d["acc"].fillna("")
    n_exported = len(d)

    # ── Rule 4: usability ────────────────────────────────────────────────
    ex = []
    def drop(mask, rule):
        nonlocal d
        bad = d[mask].copy()
        if len(bad):
            bad["exclusion_rule"] = rule
            ex.append(bad)
        d = d[~mask].copy()

    drop(d.obs_nm.isna(), "U1 no observed wavelength (Ritz-only)")
    drop(~d.obs_nm.between(CAL_MIN, CAL_MAX), f"U2 outside {CAL_MIN}-{CAL_MAX} nm")
    if a.pilot:
        # The 27-line pilot list carries no intensities, Aki values, uncertainties or accuracy
        # grades at all, so U3-U5 cannot be evaluated. They are WAIVED in pilot mode purely so
        # the regression check can run. This waiver is itself the demonstration that the pilot
        # list does not meet the usability standard required of the expanded set.
        print("[pilot] U3/U4/U5 waived: the 27-line list has no intensity, Aki, "
              "uncertainty or accuracy metadata.")
    else:
        drop(d.intensity.isna() & d.aki.isna(), "U3 neither relative intensity nor Aki")
    drop(d.unc_nm.notna() & (d.unc_nm > MAX_UNC_NM), f"U4 quoted uncertainty > {MAX_UNC_NM} nm")
    gok = d["acc"].map(grade_ok)
    drop(gok.eq(False), f"U5 accuracy grade worse than {MIN_GRADE}")
    d["flag_intensity_qualified"] = d["intensity_raw"].map(qualified) if "intensity_raw" in d else False
    d["flag_no_uncertainty_quoted"] = d.unc_nm.isna()
    d["flag_no_accuracy_quoted"] = d["acc"].map(grade_ok).isna()

    # ── Rule 5: deduplicate ──────────────────────────────────────────────
    d["_k"] = d.obs_nm.round(3)
    d["_g"] = d["acc"].map(lambda g: GRADES.index(g.strip()) if isinstance(g,str) and g.strip() in GRADES else 99)
    d = d.sort_values(["species","_k","_g","intensity"], ascending=[True,True,True,False])
    dup = d.duplicated(["species","_k"], keep="first")
    drop(dup, "D1 duplicate (species, observed wavelength to 0.001 nm)")
    d = d.sort_values(["species","obs_nm"]).reset_index(drop=True)

    # ── Rule 6: GREEDY SPAN-LIMITED GROUPING (within species) ────────────
    # Lines of one species are sorted by observed wavelength ascending (ties, which
    # cannot survive rule 5, by source file name then original row order). The first
    # line opens a group. Each subsequent line joins the OPEN group if and only if
    # (candidate - group_min) <= MAX_SPAN; the boundary is inclusive. Otherwise the
    # open group is closed and the candidate opens a new one. A group's span is
    # therefore bounded by MAX_SPAN by construction, and no chaining can occur.
    # The pass is greedy and single-sweep: a closed group is never reopened, and no
    # global optimisation of group boundaries is attempted.
    d = d.sort_values(["species", "obs_nm", "source_file"], kind="mergesort").reset_index(drop=True)
    d["_sp"] = d["species"]
    d["_gid"] = 0
    for sp, g in d.groupby("species", sort=True):
        gid, gmin = 0, None
        for idx, r in g.iterrows():
            if gmin is None:
                gmin = r.obs_nm
            elif (r.obs_nm - gmin) > a.group + SPAN_EPS:   # inclusive boundary (SPAN_EPS guards float error)
                gid += 1
                gmin = r.obs_nm
            d.at[idx, "_gid"] = gid
    d["group_id"] = d["_sp"] + "#" + d["_gid"].astype(str)

    recs = []
    for gid, g in d.groupby("group_id", sort=True):
        unc = g["unc_nm"] if "unc_nm" in g else pd.Series(dtype=float)
        # A5: ritz_nm arrives Excel-armoured (="777.1944"); pd.to_numeric returns NaN for
        # every row, so A4.1's median-Ritz definition silently fell back to median observed.
        ritz = g["ritz_nm"].map(num) if "ritz_nm" in g else pd.Series(dtype=float)
        # A4: ONE representative wavelength, used for binning, tie-break and matching.
        # median Ritz of members; fallback median observed. No intensity weighting.
        cen = float(ritz.median()) if ritz.notna().any() else float(g.obs_nm.median())
        recs.append({"group_id": gid, "species": g["_sp"].iloc[0], "group_nm": round(cen,4),
                     "n_lines": int(len(g)), "members_nm": ";".join(f"{x:.4f}" for x in g.obs_nm),
                     "max_intensity": g.intensity.max(), "max_aki": g.aki.max(),
                     "min_unc_nm": float(unc.min()) if unc.notna().any() else np.nan,
                     "ritz_rep_nm": round(cen,4),   # == group_nm under A4; kept for column stability
                     "span_nm": round(float(g.obs_nm.max()-g.obs_nm.min()),4)})
    G = pd.DataFrame(recs)

    # ── Rule 7: cap at CAP_GROUPS per species ────────────────────────────
    if G.empty:
        sys.exit("No groups survived the usability rules - nothing to score.")
    # ── Rule 7 (PROTOCOL AMENDMENT v2): STRATIFIED WAVELENGTH CAP ───────
    # Supersedes the v1 intensity-only ranking. Amendment made before any spectral
    # scoring; the v1 catalogue is preserved on disk under its own tag.
    #
    # 220-800 nm is divided into six fixed 100 nm bins. A group is assigned to the bin
    # containing its representative wavelength group_nm, half-open [lo, hi), except the
    # final bin which is closed [700, 800]. Up to PER_BIN groups are retained per bin
    # per species; bins with fewer usable groups contribute all of them, and no quota
    # is reallocated between bins.
    #
    # Within a bin, groups are ranked by, in strict order:
    #   a. smaller minimum member wavelength uncertainty; groups with a quoted
    #      uncertainty rank ahead of groups with none (see RULES.md A2.1)
    #   b. larger maximum member Aki; groups with no Aki rank last on this key
    #   c. larger maximum member NIST relative intensity; none ranks last
    #   d. smaller representative Ritz wavelength (deterministic final tie-break)
    # NIST relative intensity is a catalogue-ranking input only. It is NOT treated as a
    # prediction of lunar LIBS line brightness.
    def assign_bin(w):
        for i, (lo, hi) in enumerate(BINS):
            last = (i == len(BINS) - 1)
            if (lo <= w < hi) or (last and lo <= w <= hi):
                return lo
        return np.nan
    G["bin_lo"] = G.group_nm.map(assign_bin)
    assert G.bin_lo.notna().all(), "group outside the six bins"
    G["bin_lo"] = G.bin_lo.astype(int)
    BL = {lo: f"{lo}-{hi}" for lo, hi in BINS}
    G["bin"] = G.bin_lo.map(BL)
    # Amendment A3 ranking. Keys a and b are total orders and are applied as an
    # ordinary sort. Key c (uncertainty) is NOT a total order: a missing uncertainty
    # is neutral, so it is applied pairwise only inside an exact (a, b) tie-group,
    # over an input already ordered by key d. That makes the outcome deterministic
    # despite key c being formally non-transitive (A3.3).
    G["_int"] = G.max_intensity.fillna(-np.inf)      # a. stronger relative intensity
    G["_aki"] = G.max_aki.fillna(-np.inf)            # b. stronger Aki
    G["_unc"] = G.min_unc_nm                         # c. smaller uncertainty, neutral if absent
    G = G.sort_values(["species", "bin_lo", "_int", "_aki", "ritz_rep_nm"],
                      ascending=[True, True, False, False, True],
                      kind="mergesort").reset_index(drop=True)

    def cmp_unc(i, j):
        ui, uj = G.at[i, "_unc"], G.at[j, "_unc"]
        if pd.notna(ui) and pd.notna(uj) and ui != uj:
            return -1 if ui < uj else 1          # both quoted: smaller wins
        ri, rj = G.at[i, "ritz_rep_nm"], G.at[j, "ritz_rep_nm"]
        return -1 if ri < rj else (1 if ri > rj else 0)   # d. deterministic tie-break

    order = []
    for _, blk in G.groupby(["species", "bin_lo", "_int", "_aki"], sort=False):
        idx = list(blk.index)
        order.extend(sorted(idx, key=functools.cmp_to_key(cmp_unc)) if len(idx) > 1 else idx)
    G = G.loc[order].reset_index(drop=True)
    G["rank_in_bin"] = G.groupby(["species", "bin_lo"]).cumcount() + 1
    G["rank_in_species"] = np.where(G.rank_in_bin > PER_BIN, CAP_GROUPS + 1, G.rank_in_bin)
    capped = G[G.rank_in_bin > PER_BIN]
    if len(capped):
        cut = d[d.group_id.isin(capped.group_id)].copy()
        cut["exclusion_rule"] = f"C1 beyond stratified cap of {PER_BIN} groups per 100 nm bin"
        ex.append(cut)
    G = G[G.rank_in_bin <= PER_BIN].drop(columns=["_unc","_aki","_int"]).reset_index(drop=True)
    d = d[d.group_id.isin(G.group_id)]

    E = pd.concat(ex, ignore_index=True) if ex else pd.DataFrame(columns=list(d.columns)+["exclusion_rule"])
    keep = [c for c in ["species","obs_nm","ritz_nm","unc_nm","intensity","aki","ei","ek","acc",
                        "conf_i","term_i","conf_k","term_k","group_id",
                        "flag_no_uncertainty_quoted","flag_no_accuracy_quoted",
                        "flag_intensity_qualified","source_file"] if c in d]
    OUT.mkdir(parents=True, exist_ok=True)
    fl = OUT / f"E_reference_lines__{tag}.csv"
    fg = OUT / f"E_line_groups__{tag}.csv"
    fe = OUT / f"E_reference_exclusions__{tag}.csv"
    d[keep].to_csv(fl, index=False)
    G.to_csv(fg, index=False)
    E[[c for c in E.columns if not c.startswith("_")]].to_csv(fe, index=False)

    # ── G3: counts must reconcile ────────────────────────────────────────
    assert n_exported == len(d) + len(E), f"reconcile FAILED: {n_exported} != {len(d)}+{len(E)}"
    man = dict(tag=tag, mode="pilot" if a.pilot else "expanded", group_nm=a.group,
               cal_min=CAL_MIN, cal_max=CAL_MAX, max_unc_nm=MAX_UNC_NM, min_grade=MIN_GRADE,
               cap_groups=CAP_GROUPS, per_bin=PER_BIN, bins=[f"{a}-{b}" for a,b in BINS],
               cap_rule="A3 stratified: <=5 groups per 100 nm bin per species; rank intensity > Aki > uncertainty(neutral if absent) > median Ritz", n_exported=n_exported, n_usable_lines=len(d),
               n_excluded=len(E), n_groups=len(G),
               groups_per_species=G.species.value_counts().sort_index().to_dict(),
               sha256={f.name: hashlib.sha256(f.read_bytes()).hexdigest()[:16] for f in (fl,fg,fe)})
    (OUT / f"E_reference_manifest__{tag}.json").write_text(json.dumps(man, indent=2))
    print(json.dumps({k:v for k,v in man.items() if k!="sha256"}, indent=2))
    print(f"\nreconcile OK: {n_exported} exported = {len(d)} usable + {len(E)} excluded")

if __name__ == "__main__":
    main()
