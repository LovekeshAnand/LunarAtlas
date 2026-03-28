#!/usr/bin/env python3
"""
Chandrayaan-3 LIBS Spectra Plotting Script
==========================================

Generates plots from cleaned LIBS data files produced by batch_process_libs.py.

Plots generated:
1. All spectra overlaid on one plot
2. Individual spectrum per measurement (subplots)
3. Heatmap of all spectra across wavelengths
4. Peak intensity comparison across measurements

Usage:
    python plot_libs_spectra.py <cleaned_csv_OR_folder> [output_dir]

Examples (pass either the CSV file or the folder containing it):
    python plot_libs_spectra.py ch3_lib_002_20230825T104221_00_l1_cleaned.csv
    python plot_libs_spectra.py cleaned_spectra
    python plot_libs_spectra.py cleaned_spectra  graphs
"""

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from pathlib import Path


# ── Colour palette (one per measurement) ─────────────────────────────────────
COLOURS = ['#2196F3', '#FF5722', '#4CAF50', '#9C27B0',
           '#FF9800', '#00BCD4', '#E91E63', '#607D8B']

# Known LIBS emission lines for lunar elemental analysis
KNOWN_LINES = {
    # Element : (wavelength_nm, label)
    'Ca II': (393.37,  'Ca II'),
    'Ca I':  (422.67,  'Ca I'),
    'Mg II': (280.27,  'Mg II'),
    'Mg I':  (518.36,  'Mg I'),
    'Fe I':  (404.58,  'Fe I'),
    'Al I':  (396.15,  'Al I'),
    'Na I':  (588.99,  'Na I'),
    'Si I':  (288.16,  'Si I'),
    'Ti II': (334.94,  'Ti II'),
    'H I':   (656.28,  'H'),
    
}


def load_data(csv_path: str) -> pd.DataFrame:
    """Load and validate the cleaned CSV file.
    Accepts either a direct path to a CSV file, or a folder that contains one."""
    path = Path(csv_path)

    # If a directory was passed, find the first *_cleaned.csv inside it
    if path.is_dir():
        candidates = sorted(path.glob("*_cleaned.csv"))
        if not candidates:
            # Fallback: any CSV in the folder
            candidates = sorted(path.glob("*.csv"))
        if not candidates:
            sys.exit(
                f"No CSV files found in folder: {path}\n"
                "Please pass the path to your *_cleaned.csv file directly."
            )
        if len(candidates) > 1:
            print(f"Multiple CSV files found in folder, using: {candidates[0].name}")
        path = candidates[0]

    if not path.exists():
        sys.exit(f"File not found: {path}")

    print(f"Reading: {path.name}")
    df = pd.read_csv(path)
    df['Time_UTC'] = pd.to_datetime(df['Time_UTC'])

    required = ['Measurement_ID', 'Wavelength_nm', 'Cleaned_Intensity']
    missing = [c for c in required if c not in df.columns]
    if missing:
        sys.exit(f"Missing columns: {missing}")

    return df, path


def measurement_label(df: pd.DataFrame, mid: int) -> str:
    """Build a concise legend label from metadata."""
    row = df[df['Measurement_ID'] == mid].iloc[0]
    return (f"ID {mid}  |  E={row['Laser_Energy_V']} V  "
            f"|  {row['Number_of_Pulses']} pulse(s)  "
            f"|  {row['Integration_Time_us']} µs")


# ─────────────────────────────────────────────────────────────────────────────
# Plot 1 – All spectra overlaid
# ─────────────────────────────────────────────────────────────────────────────
def plot_all_overlaid(df: pd.DataFrame, out_dir: Path, stem: str) -> None:
    mids = sorted(df['Measurement_ID'].unique())
    fig, ax = plt.subplots(figsize=(16, 6))

    for i, mid in enumerate(mids):
        sub = df[df['Measurement_ID'] == mid].sort_values('Wavelength_nm')
        colour = COLOURS[i % len(COLOURS)]
        ax.plot(sub['Wavelength_nm'], sub['Cleaned_Intensity'],
                color=colour, linewidth=0.9, alpha=0.85,
                label=measurement_label(df, mid))

    # Mark known emission lines
    ymax = df['Cleaned_Intensity'].max()
    for name, (wl, lbl) in KNOWN_LINES.items():
        if df['Wavelength_nm'].min() <= wl <= df['Wavelength_nm'].max():
            ax.axvline(wl, color='gray', linewidth=0.6, linestyle='--', alpha=0.5)
            ax.text(wl + 1, ymax * 0.92, lbl,
                    fontsize=6.5, color='gray', rotation=90, va='top')

    ax.set_xlabel('Wavelength (nm)', fontsize=12)
    ax.set_ylabel('Cleaned Intensity (counts)', fontsize=12)
    ax.set_title(f'All Measurements Overlaid — {stem}', fontsize=13, fontweight='bold')
    ax.legend(fontsize=8, loc='upper right', framealpha=0.85)
    ax.set_xlim(df['Wavelength_nm'].min(), df['Wavelength_nm'].max())
    ax.set_ylim(bottom=0)
    ax.grid(True, linewidth=0.4, alpha=0.4)

    fig.tight_layout()
    out = out_dir / f"{stem}_01_all_overlaid.png"
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Saved: {out.name}")


# ─────────────────────────────────────────────────────────────────────────────
# Plot 2 – Individual subplots (one per measurement)
# ─────────────────────────────────────────────────────────────────────────────
def plot_individual_subplots(df: pd.DataFrame, out_dir: Path, stem: str) -> None:
    mids = sorted(df['Measurement_ID'].unique())
    n = len(mids)
    ncols = 2
    nrows = (n + 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 4 * nrows),
                              sharex=True, sharey=False)
    axes = np.array(axes).flatten()  # handle both 1-row and multi-row cases

    ymax_global = df['Cleaned_Intensity'].max()

    for i, mid in enumerate(mids):
        ax = axes[i]
        sub = df[df['Measurement_ID'] == mid].sort_values('Wavelength_nm')
        colour = COLOURS[i % len(COLOURS)]

        ax.plot(sub['Wavelength_nm'], sub['Cleaned_Intensity'],
                color=colour, linewidth=0.9)
        ax.fill_between(sub['Wavelength_nm'], sub['Cleaned_Intensity'],
                        alpha=0.15, color=colour)

        # Mark known emission lines
        for name, (wl, lbl) in KNOWN_LINES.items():
            if sub['Wavelength_nm'].min() <= wl <= sub['Wavelength_nm'].max():
                ax.axvline(wl, color='gray', linewidth=0.6, linestyle='--', alpha=0.5)
                ax.text(wl + 1, ymax_global * 0.88, lbl,
                        fontsize=6, color='gray', rotation=90, va='top')

        # Metadata box in top-left
        row = sub.iloc[0]
        info = (f"E = {row['Laser_Energy_V']} V\n"
                f"Pulses = {row['Number_of_Pulses']}\n"
                f"Int. time = {row['Integration_Time_us']} µs\n"
                f"PRR = {row['PRR_Hz']} Hz")
        ax.text(0.01, 0.97, info, transform=ax.transAxes,
                fontsize=7.5, va='top', ha='left',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor='lightgray', alpha=0.85))

        ax.set_title(f'Measurement ID {mid}  —  {row["Time_UTC"]}',
                     fontsize=9, fontweight='bold')
        ax.set_ylabel('Intensity (counts)', fontsize=8)
        ax.set_xlim(sub['Wavelength_nm'].min(), sub['Wavelength_nm'].max())
        ax.set_ylim(bottom=0)
        ax.grid(True, linewidth=0.4, alpha=0.4)

    # Hide unused subplots
    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    for ax in axes[-ncols:]:
        ax.set_xlabel('Wavelength (nm)', fontsize=9)

    fig.suptitle(f'Individual Spectra — {stem}', fontsize=13,
                 fontweight='bold', y=1.01)
    fig.tight_layout()

    out = out_dir / f"{stem}_02_individual_subplots.png"
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Saved: {out.name}")


# ─────────────────────────────────────────────────────────────────────────────
# Plot 3 – Heatmap (Measurement × Wavelength)
# ─────────────────────────────────────────────────────────────────────────────
def plot_heatmap(df: pd.DataFrame, out_dir: Path, stem: str) -> None:
    mids = sorted(df['Measurement_ID'].unique())
    pivot = df.pivot_table(index='Measurement_ID',
                           columns='Wavelength_nm',
                           values='Cleaned_Intensity',
                           aggfunc='first')

    fig, ax = plt.subplots(figsize=(16, max(3, len(mids) * 1.4)))
    img = ax.imshow(pivot.values, aspect='auto', cmap='inferno',
                    origin='lower', interpolation='nearest')

    # X-axis: wavelength ticks every ~50 nm
    wl_arr = pivot.columns.values
    tick_step = max(1, len(wl_arr) // 18)
    ax.set_xticks(range(0, len(wl_arr), tick_step))
    ax.set_xticklabels([f'{w:.0f}' for w in wl_arr[::tick_step]],
                       rotation=45, ha='right', fontsize=8)

    # Y-axis: one row per measurement
    ax.set_yticks(range(len(mids)))
    ax.set_yticklabels([f'ID {m}' for m in mids], fontsize=9)

    # Mark known emission lines
    for name, (wl, lbl) in KNOWN_LINES.items():
        if wl_arr.min() <= wl <= wl_arr.max():
            idx = np.argmin(np.abs(wl_arr - wl))
            ax.axvline(idx, color='cyan', linewidth=0.8, linestyle='--', alpha=0.6)
            ax.text(idx + 2, -0.6, lbl,
                    fontsize=6.5, color='cyan', rotation=90, va='top')

    cbar = fig.colorbar(img, ax=ax, pad=0.01)
    cbar.set_label('Cleaned Intensity (counts)', fontsize=10)

    ax.set_xlabel('Wavelength (nm)', fontsize=11)
    ax.set_ylabel('Measurement', fontsize=11)
    ax.set_title(f'Spectral Heatmap — {stem}', fontsize=13, fontweight='bold')

    fig.tight_layout()
    out = out_dir / f"{stem}_03_heatmap.png"
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Saved: {out.name}")


# ─────────────────────────────────────────────────────────────────────────────
# Plot 4 – Peak intensity comparison bar chart
# ─────────────────────────────────────────────────────────────────────────────
def plot_peak_comparison(df: pd.DataFrame, out_dir: Path, stem: str) -> None:
    mids = sorted(df['Measurement_ID'].unique())
    peak_vals, peak_wls, energies, labels = [], [], [], []

    for mid in mids:
        sub = df[df['Measurement_ID'] == mid]
        idx_max = sub['Cleaned_Intensity'].idxmax()
        peak_vals.append(sub.loc[idx_max, 'Cleaned_Intensity'])
        peak_wls.append(sub.loc[idx_max, 'Wavelength_nm'])
        energies.append(sub.iloc[0]['Laser_Energy_V'])
        labels.append(f'ID {mid}')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Left: peak intensity bar
    bars = ax1.bar(labels, peak_vals,
                   color=[COLOURS[i % len(COLOURS)] for i in range(len(mids))],
                   edgecolor='white', linewidth=0.8, width=0.55)
    for bar, val, wl in zip(bars, peak_vals, peak_wls):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + max(peak_vals) * 0.015,
                 f'{val:.0f}\n@ {wl:.1f} nm',
                 ha='center', va='bottom', fontsize=8.5)
    ax1.set_title('Peak Intensity per Measurement', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Peak Cleaned Intensity (counts)', fontsize=10)
    ax1.set_xlabel('Measurement', fontsize=10)
    ax1.set_ylim(0, max(peak_vals) * 1.18)
    ax1.grid(True, axis='y', linewidth=0.4, alpha=0.4)

    # Right: laser energy bar
    bars2 = ax2.bar(labels, energies,
                    color=[COLOURS[i % len(COLOURS)] for i in range(len(mids))],
                    edgecolor='white', linewidth=0.8, width=0.55, alpha=0.85)
    for bar, val in zip(bars2, energies):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + max(energies) * 0.008,
                 str(val), ha='center', va='bottom', fontsize=9)
    ax2.set_title('Laser Energy per Measurement', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Laser Energy (V)', fontsize=10)
    ax2.set_xlabel('Measurement', fontsize=10)
    ax2.set_ylim(min(energies) * 0.98, max(energies) * 1.04)
    ax2.grid(True, axis='y', linewidth=0.4, alpha=0.4)

    fig.suptitle(f'Measurement Comparison — {stem}',
                 fontsize=12, fontweight='bold')
    fig.tight_layout()
    out = out_dir / f"{stem}_04_peak_comparison.png"
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Saved: {out.name}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # ── Argument handling ────────────────────────────────────────────────────
    if len(sys.argv) < 2:
        sys.exit(
            "Usage:\n"
            "  python plot_libs_spectra.py <cleaned_csv_or_folder>\n"
            "  python plot_libs_spectra.py <cleaned_csv_or_folder> <output_dir>\n\n"
            "Examples:\n"
            "  python plot_libs_spectra.py cleaned_spectra\n"
            "  python plot_libs_spectra.py cleaned_spectra  graphs\n"
            "  python plot_libs_spectra.py ch3_lib_002_..._cleaned.csv"
        )

    csv_path = sys.argv[1]
    out_dir  = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(csv_path).parent / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("CHANDRAYAAN-3 LIBS SPECTRA PLOTTER")
    print("=" * 70)
    print(f"Input : {csv_path}")
    print(f"Output: {out_dir}")
    print("=" * 70)

    # ── Load data ────────────────────────────────────────────────────────────
    df, resolved_path = load_data(csv_path)
    stem = resolved_path.stem          # derived from the actual file, not the folder

    mids = sorted(df['Measurement_ID'].unique())

    print(f"\nLoaded {len(df):,} rows")
    print(f"Measurements : {list(mids)}")
    print(f"Wavelength   : {df['Wavelength_nm'].min():.2f} - {df['Wavelength_nm'].max():.2f} nm")
    print(f"Intensity    : 0 - {df['Cleaned_Intensity'].max():.1f} counts")
    print("\nGenerating plots...")

    # ── Generate all 4 plots ─────────────────────────────────────────────────
    plot_all_overlaid(df, out_dir, stem)
    plot_individual_subplots(df, out_dir, stem)
    plot_heatmap(df, out_dir, stem)
    plot_peak_comparison(df, out_dir, stem)

    print(f"\n✓ All 4 plots saved to: {out_dir}")
    print("\nPlots:")
    print("  01_all_overlaid.png      — All measurements on one chart")
    print("  02_individual_subplots   — One subplot per measurement")
    print("  03_heatmap.png           — Intensity heatmap across wavelengths")
    print("  04_peak_comparison.png   — Peak intensity + laser energy bar charts")


if __name__ == "__main__":
    main()