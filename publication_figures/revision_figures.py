#!/usr/bin/env python3
"""
SUPERSEDED by revision_v2/analysis.py and revision_v2/figures.py (pre-clamp clip fraction,
audited null model). Kept for history; do not use for manuscript numbers.

LunarAtlas — Revision Figures
=============================
Figures added in response to reviewers:

  fig3_background_subtraction : full-range raw plasma, paired background and
                                cleaned spectrum for the worked example (ID 3).
  fig4_nist_annotated         : cleaned ID 3 spectrum with detected peaks and
                                NIST candidate assignments, with zoomed insets.
  fig5_archive_quality        : (a) zero-clip fraction across all background-
                                subtracted shots in the archive; (b) per-line
                                detection rate vs. chance (shifted-line null).

Requires datasets/uploads (raw L1 copies from pipeline stage 6),
datasets/processed, and the outputs of publication_tables/revision_analysis.py.

Usage (from the repository root):
  python publication_figures/revision_figures.py
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "publication_tables"))
from revision_analysis import (CAL_MIN, CAL_MAX, CLIP_THRESHOLD, NIST_EL, NIST_WL, RESOLUTION_NM,  # noqa: E402
                               NOISE_MIN, NOISE_MAX, OUT_DIR as TABLE_DIR, TOL, detect_peaks)

OBS = "ch3_lib_002_20230825T104221_00_l1"
RAW_CSV = ROOT / "datasets" / "uploads" / "20230825" / OBS / f"{OBS}.csv"
CLEANED_CSV = ROOT / "datasets" / "processed" / "calibrated" / "20230825" / OBS / f"{OBS}_cleaned.csv"
TARGET_MID = 3
DPI = 300

LABEL_GAP_NM = 11.0  # minimum horizontal spacing of species labels in Fig. 4(a)
C_RAW, C_BG, C_CLEAN, C_PEAK, C_NIST = "#64748b", "#d97706", "#1d4ed8", "#dc2626", "#16a34a"


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"{name}.{ext}", dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {name}.png/.pdf")


def paired_raw(mid):
    """Raw plasma row for Measurement_ID `mid` and the background step2 paired with it."""
    df = pd.read_csv(RAW_CSV)
    wl_cols = df.columns[6:-8]
    last_bg, n_plasma = None, 0
    for _, row in df.iterrows():
        frs, lfs = int(row["Force Reset Status"]), int(row["Laser Fire Status"])
        if frs == 1 and lfs == 0:
            last_bg = row[wl_cols].to_numpy(float)
        elif frs == 0 and lfs == 1:
            n_plasma += 1
            if n_plasma == mid:
                return wl_cols.astype(float).to_numpy(), row[wl_cols].to_numpy(float), last_bg
    raise ValueError(f"Measurement {mid} not found in {RAW_CSV.name}")


def cleaned(mid):
    df = pd.read_csv(CLEANED_CSV)
    sub = df[df["Measurement_ID"] == mid].sort_values("Wavelength_nm")
    return sub["Wavelength_nm"].to_numpy(), sub["Cleaned_Intensity"].to_numpy()


def fig3_background_subtraction():
    wl, plasma, bg = paired_raw(TARGET_MID)
    cwl, clean = cleaned(TARGET_MID)
    fig, (a, b) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
                               gridspec_kw={"height_ratios": [1.3, 1]})
    a.plot(wl, plasma, color=C_RAW, lw=0.6, label="Raw plasma acquisition $I_P$")
    a.plot(wl, bg, color=C_BG, lw=0.6, label="Paired background acquisition $I_B$ (preceding frame)")
    a.set_ylabel("L1 intensity (a.u.)")
    a.legend(loc="upper right", fontsize=8, frameon=False)
    a.set_title("(a) Measured inputs", loc="left", fontsize=10)
    b.plot(cwl, clean, color=C_CLEAN, lw=0.6, label=r"Cleaned $\max(0, I_P - I_B)$")
    b.axvspan(NOISE_MIN, NOISE_MAX, color="#e2e8f0", label=f"Noise window {NOISE_MIN:.0f}–{NOISE_MAX:.0f} nm")
    b.set_ylabel("Cleaned intensity (a.u.)")
    b.set_xlabel("Wavelength (nm)")
    b.legend(loc="upper right", fontsize=8, frameon=False)
    b.set_title("(b) After paired subtraction and zero-clamping", loc="left", fontsize=10)
    for ax in (a, b):
        ax.axvspan(wl[0], CAL_MIN, color="#f1f5f9", zorder=0)
        ax.axvspan(CAL_MAX, wl[-1], color="#f1f5f9", zorder=0)
        ax.set_xlim(wl[0], wl[-1])
        ax.grid(alpha=0.25, lw=0.5)
    b.text(0.005, 0.92, "outside calibrated range", transform=b.transAxes, fontsize=7, color="#64748b")
    save(fig, "fig3_background_subtraction")


def fig4_nist_annotated():
    wl, inten = cleaned(TARGET_MID)
    cal = (wl >= CAL_MIN) & (wl <= CAL_MAX)
    wl, inten = wl[cal], inten[cal]
    peaks = detect_peaks(wl, inten)
    peak_int = np.interp(peaks, wl, inten)
    sigma = np.std(inten[(wl >= NOISE_MIN) & (wl <= NOISE_MAX)], ddof=0)

    # Assignment: nearest NIST line within TOL; lines within one resolution element are labelled as a blend
    blends = pd.read_csv(TABLE_DIR / "nist_blended_pairs.csv")
    blend_of = {}
    for _, r in blends.iterrows():
        el_a, el_b = r.line_a.rsplit(" ", 1)[0], r.line_b.rsplit(" ", 1)[0]
        label = f"{el_a} blend" if el_a == el_b else f"{el_a}/{el_b} blend"
        for side in (r.line_a, r.line_b):
            blend_of[float(side.rsplit(" ", 1)[1])] = label
    assigned = []
    for p, h in zip(peaks, peak_int):
        d = np.abs(NIST_WL - p)
        if d.min() < TOL:
            j = int(d.argmin())
            assigned.append((p, h, blend_of.get(round(NIST_WL[j], 2), NIST_EL[j])))

    windows = [(276, 292), (386, 400), (582, 596), (770, 784)]
    fig = plt.figure(figsize=(11, 10))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.25, 1], hspace=1.0, wspace=0.3)
    main = fig.add_subplot(gs[0, :])

    def draw(ax, lo, hi, labels):
        m = (wl >= lo) & (wl <= hi)
        ax.plot(wl[m], inten[m], color=C_CLEAN, lw=0.7, drawstyle="steps-mid" if hi - lo < 50 else "default")
        pm = (peaks >= lo) & (peaks <= hi)
        ax.plot(peaks[pm], peak_int[pm], "v", color=C_RAW, ms=3, label="Detected peak (3σ prominence)")
        for x in NIST_WL[(NIST_WL >= lo) & (NIST_WL <= hi)]:
            ax.axvline(x, color=C_NIST, ls=":", lw=0.8)
        label_x = lo - LABEL_GAP_NM
        for p, h, name in assigned:
            if lo <= p <= hi:
                ax.plot(p, h, "v", color=C_PEAK, ms=5)
                if labels:  # labels in one band above the spectrum, pushed right so neighbours never overlap
                    label_x = max(p, label_x + LABEL_GAP_NM)
                    ax.annotate(name, (p, h), xytext=(label_x, inten.max() * 1.08), textcoords="data",
                                ha="center", va="bottom", fontsize=10, color=C_PEAK, rotation=90,
                                arrowprops=dict(arrowstyle="-", color=C_PEAK, lw=0.4))
        ax.set_xlim(lo, hi)
        ax.grid(alpha=0.25, lw=0.5)

    draw(main, CAL_MIN, CAL_MAX, labels=True)
    main.plot([], [], "v", color=C_PEAK, ms=5, label="Candidate NIST assignment (|Δλ| < 0.5 nm)")
    main.plot([], [], ls=":", color=C_NIST, label="NIST ASD reference line")
    main.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), fontsize=10, frameon=False, ncol=3)
    main.set_ylim(top=inten.max() * 1.8)
    main.tick_params(labelsize=11)
    main.set_ylabel("Cleaned intensity (a.u.)", fontsize=12)
    main.set_title(f"(a) Measurement ID {TARGET_MID}, calibrated range (3σ = {3 * sigma:.0f} a.u.)",
                   loc="left", fontsize=12)
    for k, (lo, hi) in enumerate(windows):
        ax = fig.add_subplot(gs[1, k])
        draw(ax, lo, hi, labels=False)
        # One label per group of reference lines closer than the resolution element (labels would collide)
        groups = []
        for x, name in sorted((x, n) for x, n in zip(NIST_WL, NIST_EL) if lo <= x <= hi):
            if groups and x - groups[-1][-1][0] < RESOLUTION_NM:
                groups[-1].append((x, name))
            else:
                groups.append([(x, name)])
        for g in groups:
            names = [n for _, n in g]
            text = (f"{names[0]} " + "/".join(f"{x:.1f}" for x, _ in g) if len(set(names)) == 1
                    else "/".join(f"{n} {x:.1f}" for x, n in g))
            ax.text(np.mean([x for x, _ in g]), 1.01, text, transform=ax.get_xaxis_transform(),
                    rotation=90, fontsize=8.5, color=C_NIST, ha="center", va="bottom")
        ax.set_xlabel("Wavelength (nm)", fontsize=10)
        ax.set_title(f"({'bcde'[k]}) {lo}–{hi} nm", loc="left", fontsize=11, pad=100)
        ax.tick_params(labelsize=9)
        main.axvspan(lo, hi, color="#fef3c7", zorder=0)
    save(fig, "fig4_nist_annotated")


def fig5_archive_quality():
    shots = pd.read_csv(TABLE_DIR / "archive_shots.csv")
    lines = pd.read_csv(TABLE_DIR / "nist_line_detection_archive.csv")
    products = json.loads((TABLE_DIR / "archive_summary.json").read_text())["products"]
    clip = shots["zero_clip_fraction"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={"width_ratios": [1, 1.6]})
    a.hist(clip, bins=np.linspace(0, 1, 21), color=C_CLEAN, edgecolor="white")
    a.axvline(CLIP_THRESHOLD, color=C_PEAK, ls="--", lw=1)
    over = int((clip > CLIP_THRESHOLD).sum())
    a.text(CLIP_THRESHOLD + 0.02, a.get_ylim()[1] * 0.9,
           f"quality flag\n{over}/{len(clip)} shots ({100 * over / len(clip):.0f}%)", fontsize=8, color=C_PEAK)
    a.set_xlabel("Zero-clamped channel fraction")
    a.set_ylabel("Plasma shots")
    a.set_title(f"(a) Signal quality, {len(clip)} paired shots from {products} products", loc="left", fontsize=10)
    x = np.arange(len(lines))
    b.bar(x, lines["detected_in_pct_of_valid_spectra"], color=C_CLEAN, label="Real NIST line")
    b.plot(x, lines["chance_pct_shifted_line"], "_", color="black", ms=12, mew=1.5,
           label="Chance (line shifted 2–20 nm)")
    b.set_xticks(x, [f"{e} {w:.1f}" for e, w in zip(lines["element"], lines["nist_wavelength_nm"])],
                 rotation=90, fontsize=7)
    b.set_ylabel("Valid spectra with a peak within 0.5 nm (%)")
    b.set_title(f"(b) Per-line detection rate, {int(shots['quality_valid'].sum())} quality-valid spectra",
                loc="left", fontsize=10)
    b.legend(fontsize=8, frameon=False)
    for ax in (a, b):
        ax.grid(alpha=0.25, lw=0.5, axis="y")
    save(fig, "fig5_archive_quality")


if __name__ == "__main__":
    for path in (RAW_CSV, CLEANED_CSV, TABLE_DIR / "archive_shots.csv"):
        if not path.exists():
            sys.exit(f"[ERROR] Missing {path}. Run the pipeline and revision_analysis.py first.")
    fig3_background_subtraction()
    fig4_nist_annotated()
    fig5_archive_quality()
