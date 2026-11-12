#!/usr/bin/env python3
"""
Line-corroboration test for the 15 candidate NIST matches of the worked example
(IDs 1, 3, 4 of ch3_lib_002_20230825T104221_00_l1; Benchmarks/table_outputs/table8_nist_verification.csv).

Answers Reviewer 6: "wavelength proximity only -- false positives without line ratios?"

For each candidate (species S, reference line l0, detected peak):
  A. Competitors   - lines of OTHER species (19 NIST ASD lists) within +-0.5 nm that are
                     LTE-strong (>= 10 % of that species' strongest line at T).
  B. Corroboration - lines of S that LTE predicts at >= 100 % of l0's emissivity, lie in
                     220-800 nm and are > 1.1 nm (one resolution element) from l0.
                     Lines closer than 1.1 nm are merged into one expected feature.
                     A feature is "found" if a detected peak (paper rule) is within +-0.5 nm
                     of any of its lines; distinct detected peaks are also counted, since
                     neighbouring features can share one peak.
                     Chance: the paper's random-shift null -- the whole feature set is shifted
                     by s ~ U(2, 20) nm, random sign, and re-counted; p = (1 + k) / (1 + N).
                     This keeps each feature's width, so wide features get a wide chance window.
  C. Ratios        - Ca II 393.37/396.85: observed peak-intensity ratio vs the
                     LTE optically-thin ratio over T = 8000-12000 K. The amplitude of each line
                     in units of sigma is reported; a ratio is only meaningful where both lines
                     are detected (H and K share the lower level, so this is a doublet intensity
                     ratio, not a branching ratio).
LTE emissivity:  e ~ g_k A_ki / lambda * exp(-E_k / kT)  (same species, so Saha cancels).
All results are conditional on the parent-table wavelength axis.

Usage (from the repository root):
  python Benchmarks/revision_2026_11/line_corroboration.py datasets/nist_asd_lines \
      datasets/processed/calibrated/20230825/ch3_lib_002_20230825T104221_00_l1/ch3_lib_002_20230825T104221_00_l1_cleaned.csv \
      Benchmarks/table_outputs/table8_nist_verification.csv Benchmarks/table_outputs/revision/line_corroboration
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

CAL_MIN, CAL_MAX = 220.0, 800.0
NOISE = (560.0, 580.0)
TOL, RES = 0.5, 1.1
TEMPS = (8000.0, 10000.0, 12000.0)
T0 = 10000.0
K_CM = 0.69503476            # Boltzmann constant in cm^-1 / K
PARTNER_FRAC, COMPETITOR_FRAC = 1.0, 0.1
N_SHIFTS, SHIFT_MIN, SHIFT_MAX, SEED = 10000, 2.0, 20.0, 20251020   # same null as the paper (Table 7)
_rng = np.random.default_rng(SEED)
SHIFTS = _rng.uniform(SHIFT_MIN, SHIFT_MAX, N_SHIFTS) * _rng.choice([-1, 1], N_SHIFTS)


def found_features(feats, pk, shift=0.0):
    """Per feature: is any detected peak within TOL of any of its (shifted) lines."""
    return np.array([(np.abs(pk[:, None] - (w + shift)[None, :]) <= TOL).any() for w in feats])


def clean(v):
    s = re.sub(r'[="\[\]\(\)?]', "", str(v)).strip()
    return s if s and s.lower() != "nan" else None


def num(v):
    s = clean(v)
    try:
        return float(s)
    except (TypeError, ValueError):
        return np.nan


def j_to_g(v):
    s = clean(v)
    if s is None or "," in s:
        return np.nan
    try:
        a, b = s.split("/") if "/" in s else (s, 1)
        return 2 * float(a) / float(b) + 1
    except ValueError:
        return np.nan


def load_nist(d):
    frames = []
    for f in sorted(Path(d).iterdir()):
        species = f.name.split(".")[0].replace("_", " ")
        df = pd.read_csv(f, dtype=str, index_col=False)
        wl = df["obs_wl_air(nm)"].map(num).fillna(df["ritz_wl_air(nm)"].map(num))
        out = pd.DataFrame({
            "species": species, "wl": wl,
            "A": df["Aki(s^-1)"].map(num), "Ek": df["Ek(cm-1)"].map(num),
            "gk": df["J_k"].map(j_to_g),
            "nist_int": df["intens"].map(lambda v: num(re.sub(r"[^0-9.]", "", str(v)) or "x")),
        })
        frames.append(out[(out.wl >= CAL_MIN - 1) & (out.wl <= CAL_MAX + 1)])
    lines = pd.concat(frames, ignore_index=True)
    for T in TEMPS:
        lines[f"eps_{int(T)}"] = lines.gk * lines.A / lines.wl * np.exp(-lines.Ek / (K_CM * T))
    return lines


def spectrum(cleaned, mid):
    s = cleaned[cleaned.Measurement_ID == mid].sort_values("Wavelength_nm")
    wl, y = s.Wavelength_nm.to_numpy(), s.Cleaned_Intensity.to_numpy()
    cal = (wl >= CAL_MIN) & (wl <= CAL_MAX)
    wl, y = wl[cal], y[cal]
    sigma = float(np.std(y[(wl >= NOISE[0]) & (wl <= NOISE[1])], ddof=0))
    idx, props = find_peaks(y, prominence=3 * sigma, distance=5)
    return wl, y, sigma, wl[idx], props["prominences"]


def ref_line(lines, species, ref_wl):
    """Full-precision NIST line behind the manuscript's rounded reference: strongest within 0.06 nm."""
    c = lines[(lines.species == species) & ((lines.wl - ref_wl).abs() <= 0.06)]
    if c.empty:
        return None
    c = c.assign(key=c[f"eps_{int(T0)}"].fillna(-1))
    return c.sort_values("key", ascending=False).iloc[0]


def main(nist_dir, cleaned_csv, table8_csv, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    lines = load_nist(nist_dir)
    cleaned = pd.read_csv(cleaned_csv)
    cands = pd.read_csv(table8_csv)
    smax = {s: g[f"eps_{int(T0)}"].max() for s, g in lines.groupby("species")}
    imax = {s: g.nist_int.max() for s, g in lines.groupby("species")}

    rows, comp_rows, part_rows, ratio_rows = [], [], [], []
    spec_cache = {}
    for c in cands.itertuples():
        if c.mid not in spec_cache:
            spec_cache[c.mid] = spectrum(cleaned, c.mid)
        wl, y, sigma, pk, prom = spec_cache[c.mid]
        S = c.nist_element
        r = ref_line(lines, S, c.nist_wl)
        tag = f"ID{c.mid} {S} {c.nist_wl}"

        # A. competitors
        near = lines[(lines.species != S) & ((lines.wl - c.detected_wl).abs() <= TOL)]
        strong = near[(near[f"eps_{int(T0)}"] >= COMPETITOR_FRAC * near.species.map(smax))
                      | (near.A.isna() & (near.nist_int >= COMPETITOR_FRAC * near.species.map(imax)))]
        for x in strong.itertuples():
            comp_rows.append({"candidate": tag, "species": x.species, "wl": round(x.wl, 3),
                              "rel_strength_T10k": round(x.eps_10000 / smax[x.species], 3)
                              if np.isfinite(x.eps_10000) else "no Aki (NIST int)"})

        # B. corroborating transitions
        n_exp = n_found = n_peaks_used = 0
        null = np.array([])
        if r is not None and np.isfinite(r[f"eps_{int(T0)}"]):
            sp = lines[(lines.species == S) & lines[f"eps_{int(T0)}"].notna()
                       & ((lines.wl - r.wl).abs() > RES)
                       & (lines.wl >= CAL_MIN) & (lines.wl <= CAL_MAX)]
            # expected at >= PARTNER_FRAC at every temperature in the range
            ok = np.all([sp[f"eps_{int(T)}"] >= PARTNER_FRAC * r[f"eps_{int(T)}"] for T in TEMPS], axis=0)
            sp = sp[ok].sort_values("wl")
            # merge partners into features no wider than one resolution element
            feats = []
            for x in sp.itertuples():
                if feats and x.wl - feats[-1][0].wl <= RES:
                    feats[-1].append(x)
                else:
                    feats.append([x])
            used = set()
            for f in feats:
                w = np.array([x.wl for x in f])
                hit = pk[(np.abs(pk[:, None] - w[None, :]) <= TOL).any(axis=1)]
                n_exp += 1
                n_found += bool(len(hit))
                used.update(np.round(hit, 2))
                part_rows.append({"candidate": tag, "partner_nm": "/".join(f"{v:.2f}" for v in w),
                                  "pred_rel_T10k": round(max(x.eps_10000 for x in f) / r.eps_10000, 2),
                                  "found": bool(len(hit)),
                                  "peak_nm": round(float(hit[0]), 2) if len(hit) else ""})
            n_peaks_used = len(used)
            fw = [np.array([x.wl for x in f]) for f in feats]
            null = np.array([found_features(fw, pk, s).sum() for s in SHIFTS]) if fw else np.array([])
        pval = (1 + int((null >= n_found).sum())) / (1 + len(null)) if n_exp else np.nan

        rows.append({
            "measurement_id": c.mid, "species": S, "ref_nm": c.nist_wl,
            "nist_full_nm": round(r.wl, 4) if r is not None else "",
            "ref_has_Aki": bool(r is not None and np.isfinite(r.A)),
            "detected_nm": c.detected_wl, "offset_nm": c.delta_wl,
            "n_strong_competitors": len(strong),
            "competitor_species": "; ".join(sorted(set(strong.species))),
            "expected_partner_features": n_exp, "partners_found": n_found,
            "distinct_peaks_used": n_peaks_used,
            "null_mean_found": round(float(null.mean()), 1) if len(null) else "",
            "p_shift": round(pval, 4) if np.isfinite(pval) else "",
        })

    # C. Ca II K/H ratio
    pairs = [("Ca II", 393.37, 396.85)]
    for mid, (wl, y, sigma, pk, prom) in spec_cache.items():
        for S, a, b in pairs:
            ra, rb = ref_line(lines, S, a), ref_line(lines, S, b)
            ia = y[np.abs(wl - a) <= TOL].max()
            ib = y[np.abs(wl - b) <= TOL].max()
            pred = [ra[f"eps_{int(T)}"] / rb[f"eps_{int(T)}"] for T in TEMPS]
            ratio_rows.append({"measurement_id": mid, "species": S, "pair": f"{a}/{b}",
                               "obs_ratio_peak": round(ia / ib, 2) if ib > 0 else "",
                               "obs_I_a": ia, "obs_I_b": ib, "sigma": round(sigma, 1),
                               "a_over_sigma": round(ia / sigma, 1), "b_over_sigma": round(ib / sigma, 1),
                               "a_detected": bool((np.abs(pk - a) <= TOL).any()),
                               "b_detected": bool((np.abs(pk - b) <= TOL).any()),
                               "lte_thin_ratio_8k_12k": f"{min(pred):.2f}-{max(pred):.2f}"})

    summ = pd.DataFrame(rows)
    summ.to_csv(out / "corroboration_summary.csv", index=False)
    pd.DataFrame(comp_rows).to_csv(out / "competitors.csv", index=False)
    pd.DataFrame(part_rows).to_csv(out / "partner_lines.csv", index=False)
    pd.DataFrame(ratio_rows).to_csv(out / "line_ratios.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_colwidth", 60)
    print(summ.to_string(index=False))
    print()
    print(pd.DataFrame(ratio_rows).to_string(index=False))


def _selfcheck():
    assert j_to_g('="3/2"') == 4 and j_to_g('="0"') == 1
    assert num('="[109610.2232]"') == 109610.2232 and np.isnan(num('=""'))
    pk = np.array([400.0])
    feats = [np.array([399.8]), np.array([400.3, 401.0]), np.array([450.0])]
    assert found_features(feats, pk).tolist() == [True, True, False]   # two features share one peak
    assert found_features(feats, pk, -50.0).tolist() == [False, False, True]


if __name__ == "__main__":
    _selfcheck()
    main(*sys.argv[1:5])
