#!/usr/bin/env python3
"""
SUPERSEDED by revision_v2/analysis.py and revision_v2/figures.py (pre-clamp clip fraction,
audited null model). Kept for history; do not use for manuscript numbers.

Revision analysis (reviewer responses)
======================================
Reproduces the archive-wide numbers added in the revision, using the processed
outputs in datasets/processed/ (run the ingestion pipeline first).

  1. Archive-wide ingestion summary: files, shots, background pairing,
     zero-clip distribution, channel-axis consistency, instrument settings.
  2. NIST false-positive test: the paper's matching rule (3-sigma prominence,
     5-channel spacing, |dl| < 0.5 nm) applied to the real NIST line list and to
     randomly shifted copies of it (null model). Matches that real lines produce
     no more often than shifted lines are indistinguishable from chance.
  3. Line blending: NIST reference pairs closer than the instrument's ~1 nm
     resolution element, which cannot be assigned to a single transition.

Usage (from the repository root):
  python publication_tables/revision_analysis.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Pipeline"))
from step4_nist_verification_logs import NIST_DB  # noqa: E402

PROCESSED = ROOT / "datasets" / "processed" / "calibrated"
RAW = ROOT / "datasets" / "uploads"            # raw L1 copies written by pipeline stage 6
PIPELINE_LOG = ROOT / "Pipeline" / "pipeline_log.json"
OUT_DIR = ROOT / "Benchmarks" / "table_outputs" / "revision"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Same constants as Benchmarks/generate_tables_678.py (paper Sections 2.3.2, 4.3)
CAL_MIN, CAL_MAX = 220.0, 800.0
NOISE_MIN, NOISE_MAX = 560.0, 580.0
TOL = 0.5                 # nm
CLIP_THRESHOLD = 0.5      # quality-warning threshold in step2
RESOLUTION_NM = 1.1       # optical resolution, FWHM < 1.1 nm (Sridhar et al. 2025, IEEE Sensors J. 25(2), Table I)
SAMPLING_NM = 0.34        # nm/channel

N_SHIFTS = 2000
SHIFT_MIN, SHIFT_MAX = 2.0, 20.0   # nm; >= 2 resolution elements away from the true line
RNG = np.random.default_rng(20251020)

WORKED_EXAMPLE = "ch3_lib_002_20230825T104221_00_l1"
WORKED_IDS = [1, 3, 4]

NIST_WL = np.array([e["wavelength"] for e in NIST_DB if CAL_MIN <= e["wavelength"] <= CAL_MAX])
NIST_EL = [e["element"] for e in NIST_DB if CAL_MIN <= e["wavelength"] <= CAL_MAX]


def detect_peaks(wl, inten):
    """Paper rule: 3-sigma prominence (sigma over 560-580 nm, ddof=0), 5-channel spacing."""
    sigma = float(np.std(inten[(wl >= NOISE_MIN) & (wl <= NOISE_MAX)], ddof=0))
    idx, _ = find_peaks(inten, prominence=3.0 * sigma, distance=5)
    return wl[idx]


def matched_peaks(peak_wl, lines):
    """Number of peaks with at least one reference line strictly within TOL."""
    if len(peak_wl) == 0:
        return 0
    return int((np.abs(peak_wl[:, None] - lines[None, :]) < TOL).any(axis=1).sum())


def lines_hit(peak_wl, lines):
    """Boolean per line: is any detected peak strictly within TOL of it."""
    if len(peak_wl) == 0:
        return np.zeros(len(lines), dtype=bool)
    return (np.abs(peak_wl[:, None] - lines[None, :]) < TOL).any(axis=0)


SHIFTS = RNG.uniform(SHIFT_MIN, SHIFT_MAX, N_SHIFTS) * RNG.choice([-1, 1], N_SHIFTS)


def null_matches(peak_wl):
    return np.array([matched_peaks(peak_wl, NIST_WL + s) for s in SHIFTS])


def load_archive():
    spectra, rows = [], []
    for csv in sorted(PROCESSED.glob("*/*/*_cleaned.csv")):
        obs = csv.parent.name
        df = pd.read_csv(csv)
        for mid, sub in df.groupby("Measurement_ID"):
            sub = sub.sort_values("Wavelength_nm")
            wl, inten = sub["Wavelength_nm"].to_numpy(), sub["Cleaned_Intensity"].to_numpy()
            first = sub.iloc[0]
            rows.append({
                "date": csv.parent.parent.name, "observation": obs, "measurement_id": int(mid),
                "n_channels": len(wl),
                "zero_clip_fraction": float(np.mean(inten == 0)),   # same definition as step2
                "integration_time_us": first["Integration_Time_us"],
                "number_of_pulses": first["Number_of_Pulses"],
                "operation_mode": first["Operation_Mode"],
            })
            cal = (wl >= CAL_MIN) & (wl <= CAL_MAX)
            spectra.append((wl[cal], inten[cal]))
    return pd.DataFrame(rows), spectra


def main():
    if not PROCESSED.exists():
        sys.exit(f"[ERROR] {PROCESSED} not found. Run the ingestion pipeline first.")

    shots, spectra = load_archive()
    valid = shots["zero_clip_fraction"] <= CLIP_THRESHOLD   # cleaned outputs hold paired shots only
    shots["quality_valid"] = valid
    shots.to_csv(OUT_DIR / "archive_shots.csv", index=False)

    # ── 1. Archive-wide ingestion summary ────────────────────────────
    bs = shots
    clip = bs["zero_clip_fraction"]
    stages = json.loads(PIPELINE_LOG.read_text())["stages"]
    s1, s2 = stages["stage_1"]["metrics"], stages["stage_2"]["metrics"]
    # Wavelength axis of every raw product, including those that produced no cleaned output
    axes = {tuple(pd.read_csv(f, nrows=0).columns[6:-8])
            for f in RAW.glob("*/*/*.csv") if not f.stem.split("_")[-1].isdigit()}
    axis = next(iter(axes))
    summary = {
        "products": s1["total_observation_folders"],
        "mission_days": s1["total_date_folders"],
        "products_with_cleaned_output": s2["files_cleaned"],
        "background_only_products": s2["bg_only_files"],
        "products_without_any_background": s2["plasma_only_files"],
        "pipeline_errors": s2["errors"],
        "plasma_acquisitions": len(shots) + s2["plasma_no_background"],
        "excluded_no_preceding_background": s2["plasma_no_background"],
        "distinct_wavelength_axes_in_raw": len(axes),
        "wavelength_axis": {"channels": len(axis), "min_nm": float(axis[0]), "max_nm": float(axis[-1])},
        "background_subtracted_shots": len(bs),
        "zero_clip_fraction_of_subtracted": {
            "median": round(float(clip.median()), 4),
            "p25": round(float(clip.quantile(0.25)), 4),
            "p75": round(float(clip.quantile(0.75)), 4),
            "above_threshold": int((clip > CLIP_THRESHOLD).sum()),
        },
        "quality_valid_shots": int(valid.sum()),
        "integration_time_us": {str(k): int(v) for k, v in shots["integration_time_us"].value_counts().items()},
        "number_of_pulses": {str(k): int(v) for k, v in shots["number_of_pulses"].value_counts().items()},
        "operation_mode": {str(k): int(v) for k, v in shots["operation_mode"].value_counts().items()},
    }
    # Does signal level (clip fraction) depend on acquisition settings?
    summary["median_clip_by_pulses"] = {str(k): round(float(v), 4) for k, v in
                                        bs.groupby("number_of_pulses")["zero_clip_fraction"].median().items()}
    summary["median_clip_by_integration_us"] = {str(k): round(float(v), 4) for k, v in
                                                bs.groupby("integration_time_us")["zero_clip_fraction"].median().items()}

    # ── 2a. False-positive test on the paper's worked example ────────
    worked = []
    for i, r in shots.iterrows():
        if r["observation"] == WORKED_EXAMPLE and r["measurement_id"] in WORKED_IDS:
            pk = detect_peaks(*spectra[i])
            obs, null = matched_peaks(pk, NIST_WL), null_matches(pk)
            worked.append({
                "measurement_id": int(r["measurement_id"]), "n_peaks": len(pk),
                "observed_matches": obs, "chance_mean": round(float(null.mean()), 2),
                "chance_p95": float(np.percentile(null, 95)),
                "p_value": round(float((null >= obs).mean()), 4),
            })
    pd.DataFrame(worked).to_csv(OUT_DIR / "nist_false_positive_worked_example.csv", index=False)

    # ── 2b. Archive-wide per-line detection rate vs. chance ──────────
    valid_idx = np.flatnonzero(valid.to_numpy())
    real_hits = np.zeros(len(NIST_WL))
    null_hits = np.zeros(len(NIST_WL))
    shift_sub = SHIFTS[:200]   # 200 shifts x ~400 spectra keeps runtime reasonable
    total_obs, total_null = 0, np.zeros(len(shift_sub))
    for i in valid_idx:
        pk = detect_peaks(*spectra[i])
        real_hits += lines_hit(pk, NIST_WL)
        total_obs += matched_peaks(pk, NIST_WL)
        for j, s in enumerate(shift_sub):
            null_hits += lines_hit(pk, NIST_WL + s)
            total_null[j] += matched_peaks(pk, NIST_WL + s)
    n_valid = len(valid_idx)
    per_line = pd.DataFrame({
        "element": NIST_EL, "nist_wavelength_nm": NIST_WL,
        "detected_in_pct_of_valid_spectra": np.round(100 * real_hits / n_valid, 1),
        "chance_pct_shifted_line": np.round(100 * null_hits / (n_valid * len(shift_sub)), 1),
    })
    per_line["excess_over_chance_pct"] = (per_line["detected_in_pct_of_valid_spectra"]
                                          - per_line["chance_pct_shifted_line"]).round(1)
    per_line.to_csv(OUT_DIR / "nist_line_detection_archive.csv", index=False)
    summary["archive_nist_test"] = {
        "valid_spectra": n_valid,
        "observed_matches_total": int(total_obs),
        "chance_matches_mean": round(float(total_null.mean()), 1),
        "chance_matches_p95": round(float(np.percentile(total_null, 95)), 1),
    }

    # ── 3. Blended reference lines ───────────────────────────────────
    order = np.argsort(NIST_WL)
    blends = []
    for a, b in zip(order[:-1], order[1:]):
        sep = NIST_WL[b] - NIST_WL[a]
        if sep < RESOLUTION_NM:
            blends.append({"line_a": f"{NIST_EL[a]} {NIST_WL[a]:.2f}",
                           "line_b": f"{NIST_EL[b]} {NIST_WL[b]:.2f}",
                           "separation_nm": round(float(sep), 2),
                           "separation_channels": round(float(sep / SAMPLING_NM), 1)})
    pd.DataFrame(blends).to_csv(OUT_DIR / "nist_blended_pairs.csv", index=False)
    summary["blended_pairs"] = blends

    with open(OUT_DIR / "archive_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print("\nWorked example (paper IDs 1, 3, 4) — observed vs. chance NIST matches:")
    print(pd.DataFrame(worked).to_string(index=False))
    print("\nArchive-wide per-line detection rate (valid spectra):")
    print(per_line.to_string(index=False))
    print(f"\nOutputs written to {OUT_DIR}")


if __name__ == "__main__":
    main()
