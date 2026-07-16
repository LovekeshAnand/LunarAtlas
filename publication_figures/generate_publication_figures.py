#!/usr/bin/env python3
"""
LunarAtlas — Publication Figure Generator
==========================================
Regenerates both figures used in the SoftwareX submission:

  Fig 1 (fig1_architecture):
      Three-tier system architecture diagram showing the Data Layer
      (PostgreSQL), Logic Layer (FastAPI + Redis), and Presentation
      Layer (React), with the offline ingestion pipeline feeding data
      from raw PDS4 L1 archives. Mirrors the committed PNG/PDF exactly.

  Fig 2 (fig2_adaptive_zoom):
      LTTB+Peaks downsampling of the cleaned spectrum (Measurement ID 3)
      at zoom levels k=1-4, showing full-resolution reference (light grey),
      downsampled curve (blue), and preserved peaks (red).

Usage
-----
  # From the repository root:
  python publication_figures/generate_publication_figures.py

  # Flags:
  python publication_figures/generate_publication_figures.py --fig1-only
  python publication_figures/generate_publication_figures.py --fig2-only
  python publication_figures/generate_publication_figures.py --dpi 150

Requirements
------------
  matplotlib, numpy, scipy, pandas
  (all in requirements.txt / environment.yml)

Output
------
  publication_figures/fig1_architecture.{pdf,png}
  publication_figures/fig2_adaptive_zoom.{pdf,png}
"""

import argparse
import sys
import math
import numpy as np
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent.parent
OUT_DIR = Path(__file__).resolve().parent

CLEANED_CSV = (
    ROOT / "datasets" / "processed" / "calibrated"
    / "20230825"
    / "ch3_lib_002_20230825T104221_00_l1"
    / "ch3_lib_002_20230825T104221_00_l1_cleaned.csv"
)

CAL_MIN    = 220.0
CAL_MAX    = 800.0
NOISE_MIN  = 560.0
NOISE_MAX  = 580.0
TARGET_MID = 3

# NIST reference wavelengths used for peak-lock (Section 2.3.2 of paper)
NIST_TARGETS = [
    274.95, 279.55, 280.27, 285.21, 288.16,
    393.37, 396.85, 404.58, 422.67, 517.27,
    588.99, 589.59, 777.19,
]


# ─────────────────────────────────────────────────────────────────────────────
# Fig 1 — System Architecture Diagram
# ─────────────────────────────────────────────────────────────────────────────

def generate_fig1(out_dir: Path, dpi: int = 300) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Polygon
    from matplotlib.lines import Line2D

    FIG_W, FIG_H = 13.5, 7.8
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=dpi)
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    C_PRES  = "#dbeafe"; B_PRES  = "#1d4ed8"
    C_LOGIC = "#ede9fe"; B_LOGIC = "#7c3aed"
    C_DATA  = "#dcfce7"; B_DATA  = "#15803d"
    C_BOX   = "#ffffff"; B_BOX   = "#374151"
    ARROW   = "#4b5563"
    DIAMOND_BG = "#fb923c"; DIAMOND_BD = "#c2410c"
    HIT_C   = "#16a34a"; MISS_C  = "#dc2626"

    def rrect(x, y, w, h, fc, ec, lw=1.4, zorder=2):
        p = FancyBboxPatch((x, y), w, h,
            boxstyle="round,pad=0,rounding_size=0.12",
            facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder)
        ax.add_patch(p)

    def lbl(x, y, t, fs=9, fw="normal", c="#1e293b", ha="center", va="center", z=4):
        ax.text(x, y, t, fontsize=fs, fontweight=fw, color=c,
                ha=ha, va=va, zorder=z, linespacing=1.5)

    def arrowv(x, y1, y2, c=ARROW, lw=1.6, txt="", side="right"):
        ax.annotate("", xy=(x, y2), xytext=(x, y1),
                    arrowprops=dict(arrowstyle="-|>", color=c, lw=lw, mutation_scale=14), zorder=5)
        if txt:
            tx = x + 0.18 if side == "right" else x - 0.18
            ax.text(tx, (y1+y2)/2, txt, fontsize=7.5, color=c,
                    ha="left" if side=="right" else "right", va="center", style="italic", zorder=5)

    def arrowh(x1, x2, y, c=ARROW, lw=1.6, txt="", side="top"):
        ax.annotate("", xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle="-|>", color=c, lw=lw, mutation_scale=14), zorder=5)
        if txt:
            ty = y + 0.15 if side == "top" else y - 0.15
            ax.text((x1+x2)/2, ty, txt, fontsize=7.5, color=c,
                    ha="center", va="bottom" if side=="top" else "top", style="italic", zorder=5)

    # Presentation layer
    rrect(0.35, 5.85, 12.8, 1.65, C_PRES, B_PRES, lw=2.0, zorder=1)
    lbl(1.15, 6.73, "1. PRESENTATION\nLAYER\n(Client Side)", fs=9.5, fw="bold", c=B_PRES)
    rrect(2.8, 6.05, 3.0, 1.15, C_BOX, B_BOX, zorder=3)
    lbl(4.30, 6.625, "Web Application\n(React 18 UI)", fs=8.5)
    rrect(8.15, 6.05, 3.5, 1.15, C_BOX, B_BOX, zorder=3)
    lbl(9.90, 6.625, "Spectral Viewer\n(SVG Graphics Canvas)", fs=8.5)

    # Logic layer
    rrect(0.35, 3.50, 12.8, 2.10, C_LOGIC, B_LOGIC, lw=2.0, zorder=1)
    lbl(1.15, 4.55, "2. LOGIC LAYER\n(Server Side)", fs=9.5, fw="bold", c=B_LOGIC)
    rrect(2.6, 3.75, 7.2, 1.60, "#f5f3ff", B_LOGIC, lw=1.2, zorder=3)
    lbl(6.20, 5.10, "API Service (FastAPI)", fs=9, fw="bold", c=B_LOGIC)
    lbl(6.20, 4.72, "• Route Handler & Redis Cache Check", fs=7.8)
    lbl(6.20, 4.45, "• ALS Baseline & Savitzky-Golay Denoising", fs=7.8)
    lbl(6.20, 4.18, "• LTTB + Peaks Downsampling Engine", fs=7.8)

    # Diamond
    dx, dy, dw, dh = 10.55, 3.95, 1.65, 0.85
    dp = np.array([[dx+dw/2, dy+dh],[dx+dw, dy+dh/2],[dx+dw/2, dy],[dx, dy+dh/2]])
    ax.add_patch(Polygon(dp, closed=True, facecolor=DIAMOND_BG, edgecolor=DIAMOND_BD,
                         linewidth=1.4, zorder=3))
    lbl(dx+dw/2, dy+dh/2, "Cache\nfound?", fs=8, fw="bold", c="white")

    # Data layer
    rrect(0.35, 0.35, 12.8, 2.85, C_DATA, B_DATA, lw=2.0, zorder=1)
    lbl(1.15, 2.10, "3. DATABASE &\nPIPELINE LAYER", fs=9.5, fw="bold", c=B_DATA)
    rrect(2.6, 0.70, 3.7, 2.20, C_BOX, B_DATA, lw=1.3, zorder=3)
    lbl(4.45, 2.40, "PostgreSQL Database", fs=8.5, fw="bold", c=B_DATA)
    lbl(4.45, 2.05, "• Raw Count Readings", fs=7.8)
    lbl(4.45, 1.77, "• Cleaned Spectra Data", fs=7.8)
    lbl(4.45, 1.49, "• NIST Reference Lines", fs=7.8)
    rrect(6.90, 0.70, 3.5, 2.20, C_BOX, B_PRES, lw=1.3, zorder=3)
    lbl(8.65, 2.40, "Ingestion Pipeline", fs=8.5, fw="bold", c=B_PRES)
    lbl(8.65, 2.05, "• XML Metadata Ingestion", fs=7.8)
    lbl(8.65, 1.77, "• Wide-to-Long Reshape", fs=7.8)
    lbl(8.65, 1.49, "• Background Subtraction", fs=7.8)
    rrect(10.95, 0.70, 2.0, 2.20, "#f9fafb", B_BOX, lw=1.2, zorder=3)
    lbl(11.95, 1.80, "Raw PDS4 L1\nArchive\n(XML/CSV)", fs=7.8)

    # Arrows
    arrowv(4.30, 5.85, 5.35, c=ARROW, txt="HTTP Request", side="left")
    ax.annotate("", xy=(9.90, 5.85), xytext=(9.90, 5.35),
                arrowprops=dict(arrowstyle="-|>", color=B_PRES, lw=1.6, mutation_scale=14), zorder=5)
    lbl(10.95, 5.60, "Responds with denoised,\ndownsampled data", fs=7.5, c=B_PRES, ha="left")
    ax.annotate("", xy=(11.65, 6.625), xytext=(12.375, 4.38),
                arrowprops=dict(arrowstyle="-|>", color=HIT_C, lw=1.6, mutation_scale=14,
                               connectionstyle="arc3,rad=-0.35"), zorder=5)
    lbl(13.0, 5.55, "Yes\n(Cache Hit)", fs=8, fw="bold", c=HIT_C, ha="left")
    ax.annotate("", xy=(9.80, 3.35), xytext=(11.95, 3.80),
                arrowprops=dict(arrowstyle="-|>", color=MISS_C, lw=1.5, mutation_scale=14,
                               linestyle="dashed"), zorder=5)
    lbl(10.85, 3.47, "No (Cache Miss)", fs=8, fw="bold", c=MISS_C)
    arrowv(4.45, 2.90, 3.75, c=ARROW, txt="Responds with\nclean data", side="left")
    arrowh(6.90, 6.30, 1.80, c=ARROW, txt="Saves", side="top")
    arrowh(10.95, 10.40, 1.80, c=ARROW, txt="Reads", side="top")

    fig.tight_layout(pad=0)
    for ext in ("pdf", "png"):
        out = out_dir / f"fig1_architecture.{ext}"
        fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor="white")
        print(f"  [SUCCESS] Saved: {out.name}")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 2 — Adaptive Zoom (LTTB+Peaks at k=1–4)
# ─────────────────────────────────────────────────────────────────────────────

def _lttb(data: np.ndarray, threshold: int) -> np.ndarray:
    n = len(data)
    if threshold >= n or threshold == 0:
        return data.copy()
    sampled_idx = [0]
    bucket_size = (n - 2) / max(threshold - 2, 1)
    a = 0
    for i in range(threshold - 2):
        bs = int(math.floor((i+1)*bucket_size)) + 1
        be = min(int(math.floor((i+2)*bucket_size)) + 1, n)
        ns = int(math.floor((i+2)*bucket_size)) + 1
        ne = min(int(math.floor((i+3)*bucket_size)) + 1, n)
        avg = data[ns:ne].mean(axis=0) if ne > ns else data[min(be-1, n-1)]
        ax_pt = data[a]
        best, best_idx = -1.0, bs
        for j in range(bs, be):
            area = abs((ax_pt[0]-avg[0])*(data[j][1]-ax_pt[1])
                      -(ax_pt[0]-data[j][0])*(avg[1]-ax_pt[1])) * 0.5
            if area > best:
                best, best_idx = area, j
        sampled_idx.append(best_idx)
        a = best_idx
    sampled_idx.append(n - 1)
    return data[sampled_idx]


def _lttb_peaks(data: np.ndarray, threshold: int,
                nist_wls: list, sigma: float) -> np.ndarray:
    from scipy.signal import find_peaks as _fp
    lttb_out = _lttb(data, threshold)
    lttb_set = set()
    for pt in lttb_out:
        idx = int(np.clip(np.searchsorted(data[:, 0], pt[0]), 0, len(data)-1))
        lttb_set.add(idx)
    intensities = data[:, 1]
    cal_mask = (data[:, 0] >= CAL_MIN) & (data[:, 0] <= CAL_MAX)
    cal_idx = np.where(cal_mask)[0]
    peaks_local, _ = _fp(intensities[cal_mask], prominence=3.0*sigma, distance=5)
    peak_global = set(cal_idx[peaks_local].tolist())
    nist_set = set()
    for wl in nist_wls:
        if CAL_MIN <= wl <= CAL_MAX:
            nist_set.add(int(np.argmin(np.abs(data[:, 0] - wl))))
    all_idx = sorted(lttb_set | peak_global | nist_set)
    return data[all_idx]


def generate_fig2(out_dir: Path, cleaned_csv: Path, dpi: int = 300) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    import pandas as pd
    from scipy.signal import find_peaks as _fp

    if not cleaned_csv.exists():
        print(
            f"\n[WARNING] Cleaned CSV not found:\n  {cleaned_csv}\n"
            "  Run the ingestion pipeline first:\n"
            "    cd Pipeline && ./run_pipeline.sh\n"
            "  then re-run this script.\n"
        )
        return

    df  = pd.read_csv(cleaned_csv)
    sub = df[df["Measurement_ID"] == TARGET_MID].sort_values("Wavelength_nm")
    cal = (sub["Wavelength_nm"] >= CAL_MIN) & (sub["Wavelength_nm"] <= CAL_MAX)
    sub = sub[cal]

    wl  = sub["Wavelength_nm"].values.astype(float)
    Int = sub["Cleaned_Intensity"].values.astype(float)
    full = np.column_stack([wl, Int])
    N_CAL = len(full)

    noise_mask = (wl >= NOISE_MIN) & (wl <= NOISE_MAX)
    sigma = float(np.std(Int[noise_mask], ddof=0)) if noise_mask.any() else 1.0

    peak_idx, _ = _fp(Int, prominence=3.0*sigma, distance=5)

    zoom_levels = [1, 2, 3, 4]
    thresholds  = [min(N_CAL, math.ceil(N_CAL * 2**(-k))) for k in zoom_levels]
    densities   = [t/N_CAL*100 for t in thresholds]

    fig, axes = plt.subplots(2, 2, figsize=(14, 8), dpi=dpi)
    axes = axes.flatten()

    for i, (k, thr, dens) in enumerate(zip(zoom_levels, thresholds, densities)):
        ax = axes[i]
        ds = _lttb_peaks(full, thr, NIST_TARGETS, sigma)
        ds_wl  = ds[:, 0]; ds_int = ds[:, 1]

        ax.plot(wl, Int, color="#cbd5e1", linewidth=0.5, alpha=0.7, zorder=1)
        ax.plot(ds_wl, ds_int, color="#2563eb", linewidth=1.2, zorder=2)

        for pidx in peak_idx:
            pk_wl = wl[pidx]
            nearest = np.argmin(np.abs(ds_wl - pk_wl))
            if abs(ds_wl[nearest] - pk_wl) < 0.5:
                ax.scatter([ds_wl[nearest]], [ds_int[nearest]],
                           color="#dc2626", s=14, zorder=4, linewidths=0)

        ax.set_xlim(CAL_MIN, CAL_MAX)
        ax.set_ylim(bottom=0)
        ax.set_title(f" = {k}$  –  {dens:.1f}% density  ({thr}/{N_CAL} pts)",
                     fontsize=10, fontweight="bold", color="#0f172a")
        ax.set_xlabel("Wavelength (nm)", fontsize=9)
        ax.set_ylabel("Cleaned Intensity (a.u.)", fontsize=9)
        ax.tick_params(labelsize=8)
        ax.set_facecolor("#f8fafc")
        ax.grid(True, color="#e2e8f0", linewidth=0.4)
        for sp in ax.spines.values():
            sp.set_edgecolor("#cbd5e1")

        if i == 0:
            handles = [
                Line2D([0],[0], color="#cbd5e1", lw=1.2, label="Full resolution"),
                Line2D([0],[0], color="#2563eb", lw=1.2, label="LTTB+Peaks"),
                Line2D([0],[0], marker="o", color="w", markerfacecolor="#dc2626",
                       markersize=6, label="Preserved peaks"),
            ]
            ax.legend(handles=handles, fontsize=8, loc="upper right",
                      framealpha=0.9, edgecolor="#e2e8f0")

    fig.suptitle(
        "LTTB+Peaks Adaptive Downsampling — Measurement ID 3 (Chandrayaan-3 LIBS)",
        fontsize=12, fontweight="bold", color="#0f172a", y=1.01
    )
    fig.tight_layout()
    for ext in ("pdf", "png"):
        out = out_dir / f"fig2_adaptive_zoom.{ext}"
        fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor="white")
        print(f"  [SUCCESS] Saved: {out.name}")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate LunarAtlas publication figures (Fig 1 & Fig 2).")
    parser.add_argument("--fig1-only", action="store_true")
    parser.add_argument("--fig2-only", action="store_true")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--cleaned-csv", type=str, default=str(CLEANED_CSV))
    args = parser.parse_args()

    print("=" * 60)
    print(" LUNARATLAS PUBLICATION FIGURE GENERATOR")
    print("=" * 60)
    print(f" Output directory : {OUT_DIR}")
    print(f" DPI              : {args.dpi}")
    print("-" * 60)

    if not args.fig2_only:
        print("\n[FIG 1] Generating system architecture diagram...")
        generate_fig1(OUT_DIR, dpi=args.dpi)

    if not args.fig1_only:
        print(f"\n[FIG 2] Generating adaptive zoom plot (Measurement ID {TARGET_MID})...")
        generate_fig2(OUT_DIR, Path(args.cleaned_csv), dpi=args.dpi)

    print("\n" + "=" * 60)
    print(" DONE — figures written to publication_figures/")
    print("=" * 60)


if __name__ == "__main__":
    main()
